from django.db.models import Sum, F, DecimalField, ExpressionWrapper, IntegerField, Count
from django.db.models.functions import Coalesce

from orders.models import Order, OrderItem


class SellerAccessError(Exception):
    pass


def require_seller(user):
    seller = user.seller_profile
    if not seller:
        raise SellerAccessError('Seller profile is required.')
    return seller


def get_dashboard_metrics(seller):
    seller_items = OrderItem.objects.filter(seller=seller)
    revenue_expression = ExpressionWrapper(
        F('seller_amount') * F('quantity'),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )
    aggregates = seller_items.aggregate(
        total_orders=Coalesce(Sum('quantity'), 0, output_field=IntegerField()),
        total_revenue=Coalesce(
            Sum(revenue_expression),
            0,
            output_field=DecimalField(max_digits=12, decimal_places=2),
        ),
    )
    recent_orders = seller_items.select_related('order', 'product').order_by('-order__created_at')[:5]
    return {
        'recent_orders': recent_orders,
        'total_products': seller.products.count(),
        'total_orders': seller_items.count(),
        'total_revenue': aggregates['total_revenue'],
    }


def get_seller_order_items(seller):
    return OrderItem.objects.filter(seller=seller).select_related('order', 'product').order_by('-order__created_at')


def get_seller_order_detail(seller, order):
    return order.items.filter(seller=seller).select_related('product')


def get_seller_analytics(seller):
    order_items = OrderItem.objects.filter(seller=seller).select_related('product', 'order')
    revenue_expression = ExpressionWrapper(
        F('seller_amount') * F('quantity'),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )
    orders = Order.objects.filter(items__seller=seller).distinct()
    successful_orders = orders.filter(status__in=['paid', 'shipped', 'delivered', 'refunded'])
    aggregates = order_items.aggregate(
        total_revenue=Coalesce(
            Sum(revenue_expression),
            0,
            output_field=DecimalField(max_digits=12, decimal_places=2),
        ),
    )
    successful_revenue = order_items.filter(
        order__status__in=['paid', 'shipped', 'delivered', 'refunded']
    ).aggregate(
        total=Coalesce(
            Sum(revenue_expression),
            0,
            output_field=DecimalField(max_digits=12, decimal_places=2),
        ),
    )['total']
    total_orders = orders.count()
    successful_orders_count = successful_orders.count()
    checkout_conversion = (
        round((successful_orders_count / total_orders) * 100, 2)
        if total_orders else 0
    )
    average_order_value = (
        successful_revenue / successful_orders_count
        if successful_orders_count else 0
    )
    repeat_customers = successful_orders.exclude(user__isnull=True).values('user').annotate(
        order_count=Count('id', distinct=True)
    ).filter(order_count__gt=1).count()
    sales_by_product = order_items.values('product_name').annotate(
        total_revenue=Coalesce(
            Sum(revenue_expression),
            0,
            output_field=DecimalField(max_digits=12, decimal_places=2),
        ),
        total_units=Coalesce(Sum('quantity'), 0, output_field=IntegerField()),
        total_orders=Count('order', distinct=True),
    ).order_by('-total_revenue', 'product_name')
    return {
        'total_revenue': aggregates['total_revenue'],
        'total_orders': total_orders,
        'total_products': seller.products.count(),
        'checkout_conversion': checkout_conversion,
        'average_order_value': average_order_value,
        'repeat_customers': repeat_customers,
        'successful_orders': successful_orders_count,
        'sales_by_product': sales_by_product,
        'order_items': order_items,
    }
