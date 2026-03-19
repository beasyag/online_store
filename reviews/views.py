from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Review, SellerReview
from main.models import Product
from sellers.models import Seller


@login_required(login_url='/users/login')
def add_product_review(request, slug):
    if request.method == 'POST':
        product = get_object_or_404(Product, slug=slug)
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '')

        Review.objects.update_or_create(
            product=product,
            user=request.user,
            defaults={'rating': rating, 'comment': comment}
        )
        messages.success(request, 'Review submitted.')
    return redirect('main:product_detail', slug=slug)


@login_required(login_url='/users/login')
def add_seller_review(request, shop_slug):
    if request.method == 'POST':
        seller = get_object_or_404(Seller, shop_slug=shop_slug)
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '')

        SellerReview.objects.update_or_create(
            seller=seller,
            user=request.user,
            defaults={'rating': rating, 'comment': comment}
        )
        messages.success(request, 'Review submitted.')
    return redirect('sellers:shop', shop_slug=shop_slug)


@login_required(login_url='/users/login')
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)
    slug = review.product.slug
    review.delete()
    messages.success(request, 'Review deleted.')
    return redirect('main:product_detail', slug=slug)