from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.template.response import TemplateResponse
from django.http import HttpResponse
from django.urls import reverse
from django.contrib import messages
from .models import Seller
from .forms import SellerRegistrationForm, SellerProductForm, SellerProductSizeFormSet
from main.models import Product
from orders.models import Order, OrderItem
from decimal import Decimal


@login_required(login_url='/users/login')
def seller_register(request):
    if hasattr(request.user, 'seller'):
        return redirect('sellers:dashboard')

    if request.method == 'POST':
        form = SellerRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            seller = form.save(commit=False)
            seller.user = request.user
            seller.save()
            request.user.role = 'seller'
            request.user.save()
            messages.success(request, 'Application submitted. Awaiting verification.')
            return redirect('sellers:dashboard')
    else:
        form = SellerRegistrationForm()

    return render(request, 'sellers/register.html', {'form': form})


@login_required(login_url='/users/login')
def dashboard(request):
    if not hasattr(request.user, 'seller'):
        return redirect('sellers:register')

    seller = request.user.seller
    recent_orders = OrderItem.objects.filter(
        seller=seller
    ).select_related('order', 'product').order_by('-order__created_at')[:5]

    context = {
        'seller': seller,
        'recent_orders': recent_orders,
        'total_products': seller.products.count(),
        'total_orders': OrderItem.objects.filter(seller=seller).count(),
        'total_revenue': sum(
            item.seller_amount * item.quantity
            for item in OrderItem.objects.filter(seller=seller)
        ),
    }
    return TemplateResponse(request, 'sellers/dashboard.html', context)


@login_required(login_url='/users/login')
def product_list(request):
    if not hasattr(request.user, 'seller'):
        return redirect('sellers:register')

    seller = request.user.seller
    products = seller.products.order_by('-created_at')
    return TemplateResponse(request, 'sellers/products.html', {
        'seller': seller,
        'products': products,
    })


@login_required(login_url='/users/login')
def product_add(request):
    if not hasattr(request.user, 'seller'):
        return redirect('sellers:register')

    seller = request.user.seller
    if not seller.is_verified:
        messages.error(request, 'Your account must be verified before adding products.')
        return redirect('sellers:dashboard')

    if request.method == 'POST':
        form = SellerProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.seller = seller
            product.save()
            messages.success(
                request,
                'Product added. Add sizes and stock (e.g. EU 40, 41 for shoes).',
            )
            return redirect('sellers:product_edit', slug=product.slug)
    else:
        form = SellerProductForm()

    return TemplateResponse(request, 'sellers/product_form.html', {
        'form': form,
        'seller': seller,
    })


@login_required(login_url='/users/login')
def product_edit(request, slug):
    if not hasattr(request.user, 'seller'):
        return redirect('sellers:register')

    seller = request.user.seller
    product = get_object_or_404(Product, slug=slug, seller=seller)

    if request.method == 'POST':
        form = SellerProductForm(request.POST, request.FILES, instance=product)
        formset = SellerProductSizeFormSet(request.POST, instance=product)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, 'Product updated successfully.')
            return redirect('sellers:products')
    else:
        form = SellerProductForm(instance=product)
        formset = SellerProductSizeFormSet(instance=product)

    return TemplateResponse(request, 'sellers/product_form.html', {
        'form': form,
        'formset': formset,
        'seller': seller,
        'product': product,
    })


@login_required(login_url='/users/login')
def product_delete(request, slug):
    if not hasattr(request.user, 'seller'):
        return redirect('sellers:register')

    seller = request.user.seller
    product = get_object_or_404(Product, slug=slug, seller=seller)

    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted.')
        return redirect('sellers:products')

    return TemplateResponse(request, 'sellers/product_confirm_delete.html', {
        'product': product,
        'seller': seller,
    })


@login_required(login_url='/users/login')
def order_list(request):
    if not hasattr(request.user, 'seller'):
        return redirect('sellers:register')

    seller = request.user.seller
    order_items = OrderItem.objects.filter(
        seller=seller
    ).select_related('order', 'product').order_by('-order__created_at')

    return TemplateResponse(request, 'sellers/orders.html', {
        'seller': seller,
        'order_items': order_items,
    })


@login_required(login_url='/users/login')
def order_detail(request, order_id):
    if not hasattr(request.user, 'seller'):
        return redirect('sellers:register')

    seller = request.user.seller
    order = get_object_or_404(Order, id=order_id)
    items = order.items.filter(seller=seller).select_related('product')

    return TemplateResponse(request, 'sellers/order_detail.html', {
        'seller': seller,
        'order': order,
        'items': items,
    })


@login_required(login_url='/users/login')
def analytics(request):
    if not hasattr(request.user, 'seller'):
        return redirect('sellers:register')

    seller = request.user.seller
    order_items = OrderItem.objects.filter(seller=seller).select_related('product', 'order')

    total_revenue = sum(item.seller_amount * item.quantity for item in order_items)
    total_orders = order_items.values('order').distinct().count()
    total_products = seller.products.count()
    top_products = (
        seller.products
        .annotate_with_sales()  # добавим ниже
        .order_by('-total_sold')[:5]
    ) if hasattr(seller.products, 'annotate_with_sales') else []

    context = {
        'seller': seller,
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'total_products': total_products,
        'order_items': order_items,
    }
    return TemplateResponse(request, 'sellers/analytics.html', context)


def shop_page(request, shop_slug):
    seller = get_object_or_404(Seller, shop_slug=shop_slug, status='verified')
    products = seller.products.order_by('-created_at')

    return TemplateResponse(request, 'sellers/shop.html', {
        'seller': seller,
        'products': products,
    })