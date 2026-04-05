from collections import defaultdict
from decimal import Decimal

from django.db.models import Count, Avg

from main.models import Product, ProductView
from orders.models import OrderItem
from reviews.models import Review


SUCCESSFUL_ORDER_STATUSES = ['paid', 'shipped', 'delivered', 'refunded']


def record_product_view(user, product):
    if not user.is_authenticated:
        return
    product_view, created = ProductView.objects.get_or_create(
        user=user,
        product=product,
        defaults={'view_count': 1},
    )
    if not created:
        product_view.view_count += 1
        product_view.save(update_fields=['view_count', 'last_viewed_at'])


def get_trending_products(*, limit=4, exclude_ids=None):
    exclude_ids = exclude_ids or []
    return Product.objects.exclude(id__in=exclude_ids).annotate(
        order_count=Count('orderitem', distinct=True),
        average_rating=Avg('reviews__rating'),
    ).order_by('-order_count', '-average_rating', '-created_at')[:limit]


def get_recently_viewed_products(*, user, limit=4, exclude_ids=None):
    exclude_ids = exclude_ids or []
    if not user.is_authenticated:
        return []
    views = ProductView.objects.filter(user=user).exclude(product_id__in=exclude_ids).select_related(
        'product'
    ).order_by('-last_viewed_at')[:limit]
    return [view.product for view in views]


def _add_product_preferences(scores, product, weight):
    scores['category'][product.category_id] += weight
    if product.subcategory_id:
        scores['subcategory'][product.subcategory_id] += weight * Decimal('1.5')
    if product.seller_id:
        scores['seller'][product.seller_id] += weight
    if product.color:
        scores['color'][product.color.lower()] += weight * Decimal('0.75')
    if product.size_kind:
        scores['size_kind'][product.size_kind] += weight * Decimal('0.5')


def build_user_preference_scores(user):
    scores = {
        'category': defaultdict(Decimal),
        'subcategory': defaultdict(Decimal),
        'seller': defaultdict(Decimal),
        'color': defaultdict(Decimal),
        'size_kind': defaultdict(Decimal),
    }

    purchased_items = OrderItem.objects.filter(
        order__user=user,
        order__status__in=SUCCESSFUL_ORDER_STATUSES,
        product__isnull=False,
    ).select_related('product', 'product__subcategory', 'product__seller')
    for item in purchased_items:
        _add_product_preferences(scores, item.product, Decimal('6.0') * item.quantity)

    viewed_items = ProductView.objects.filter(user=user).select_related(
        'product', 'product__subcategory', 'product__seller'
    )
    for item in viewed_items:
        weight = Decimal(min(item.view_count, 5))
        _add_product_preferences(scores, item.product, weight)

    reviewed_items = Review.objects.filter(user=user).select_related(
        'product', 'product__subcategory', 'product__seller'
    )
    for review in reviewed_items:
        weight = Decimal(max(review.rating, 2))
        _add_product_preferences(scores, review.product, weight)

    return scores


def _score_product(product, scores):
    score = Decimal('0')
    score += scores['category'][product.category_id]
    if product.subcategory_id:
        score += scores['subcategory'][product.subcategory_id]
    if product.seller_id:
        score += scores['seller'][product.seller_id]
    if product.color:
        score += scores['color'][product.color.lower()]
    if product.size_kind:
        score += scores['size_kind'][product.size_kind]
    return score


def get_similar_customer_products(*, user, limit=4, exclude_ids=None):
    exclude_ids = set(exclude_ids or [])
    if not user.is_authenticated:
        return []

    user_product_ids = set(OrderItem.objects.filter(
        order__user=user,
        order__status__in=SUCCESSFUL_ORDER_STATUSES,
        product__isnull=False,
    ).values_list('product_id', flat=True))
    if not user_product_ids:
        return []

    similar_users = OrderItem.objects.filter(
        order__status__in=SUCCESSFUL_ORDER_STATUSES,
        product_id__in=user_product_ids,
        order__user__isnull=False,
    ).exclude(order__user=user).values('order__user').annotate(
        overlap=Count('product_id', distinct=True)
    ).order_by('-overlap')[:10]
    similar_user_ids = [row['order__user'] for row in similar_users]
    if not similar_user_ids:
        return []

    exclude_ids.update(user_product_ids)
    candidate_ids = OrderItem.objects.filter(
        order__user_id__in=similar_user_ids,
        order__status__in=SUCCESSFUL_ORDER_STATUSES,
        product__isnull=False,
    ).exclude(product_id__in=exclude_ids).values('product_id').annotate(
        support=Count('order__user', distinct=True)
    ).order_by('-support')[:limit]
    ranked_ids = [row['product_id'] for row in candidate_ids]
    products = Product.objects.in_bulk(ranked_ids)
    return [products[product_id] for product_id in ranked_ids if product_id in products]


def get_personalized_products(*, user, limit=4, exclude_ids=None):
    exclude_ids = set(exclude_ids or [])
    if not user.is_authenticated:
        return list(get_trending_products(limit=limit, exclude_ids=list(exclude_ids)))

    successful_purchases = OrderItem.objects.filter(
        order__user=user,
        order__status__in=SUCCESSFUL_ORDER_STATUSES,
        product__isnull=False,
    ).values_list('product_id', flat=True)
    exclude_ids.update(successful_purchases)

    scores = build_user_preference_scores(user)
    similar_customer_products = get_similar_customer_products(
        user=user,
        limit=limit,
        exclude_ids=list(exclude_ids),
    )
    has_signals = any(any(bucket.values()) for bucket in scores.values())
    if not has_signals and not similar_customer_products:
        return list(get_trending_products(limit=limit, exclude_ids=list(exclude_ids)))

    candidates = Product.objects.exclude(id__in=exclude_ids).select_related(
        'category', 'subcategory', 'seller'
    ).annotate(
        order_count=Count('orderitem', distinct=True),
        average_rating=Avg('reviews__rating'),
    )
    ranked = sorted(
        candidates,
        key=lambda product: (
            Decimal('5') if product in similar_customer_products else Decimal('0'),
            _score_product(product, scores),
            Decimal(product.order_count or 0),
            Decimal(str(product.average_rating or 0)),
            product.created_at.timestamp(),
        ),
        reverse=True,
    )
    return ranked[:limit]
