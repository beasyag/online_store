from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.template.response import TemplateResponse
from django.http import HttpResponse
from django.urls import reverse
from django.contrib import messages
from .models import Seller
from .forms import SellerRegistrationForm, SellerProductForm, SellerProductSizeFormSet, SellerProductImageFormSet
from main.models import Product
from orders.models import Order, OrderItem
from .services import (
    SellerAccessError,
    get_dashboard_metrics,
    get_seller_analytics,
    get_seller_order_detail,
    get_seller_order_items,
    require_seller,
)


@login_required(login_url='/users/login')
def seller_register(request):
    if request.user.can_access_seller_dashboard:
        return redirect('sellers:dashboard')

    if request.method == 'POST':
        form = SellerRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            seller = form.save(commit=False)
            seller.user = request.user
            seller.save()
            messages.success(request, 'Application submitted. Awaiting verification.')
            return redirect('sellers:dashboard')
    else:
        form = SellerRegistrationForm()

    return render(request, 'sellers/register.html', {'form': form})


@login_required(login_url='/users/login')
def dashboard(request):
    if not request.user.can_access_seller_dashboard:
        return redirect('sellers:register')

    seller = require_seller(request.user)
    context = {'seller': seller, **get_dashboard_metrics(seller)}
    return TemplateResponse(request, 'sellers/dashboard.html', context)


@login_required(login_url='/users/login')
def product_list(request):
    if not request.user.can_access_seller_dashboard:
        return redirect('sellers:register')

    seller = require_seller(request.user)
    products = seller.products.order_by('-created_at')
    return TemplateResponse(request, 'sellers/products.html', {
        'seller': seller,
        'products': products,
    })


@login_required(login_url='/users/login')
def product_add(request):
    if not request.user.can_access_seller_dashboard:
        return redirect('sellers:register')

    seller = require_seller(request.user)
    if not request.user.can_manage_products_as_seller:
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
    if not request.user.can_access_seller_dashboard:
        return redirect('sellers:register')

    seller = require_seller(request.user)
    product = get_object_or_404(Product, slug=slug, seller=seller)

    if request.method == 'POST':
        form = SellerProductForm(request.POST, request.FILES, instance=product)
        formset = SellerProductSizeFormSet(request.POST, instance=product)
        image_formset = SellerProductImageFormSet(request.POST, request.FILES, instance=product)
        if form.is_valid() and formset.is_valid() and image_formset.is_valid():
            form.save()
            formset.save()
            image_formset.save()
            messages.success(request, 'Product updated successfully.')
            return redirect('sellers:products')
    else:
        form = SellerProductForm(instance=product)
        formset = SellerProductSizeFormSet(instance=product)
        image_formset = SellerProductImageFormSet(instance=product)

    return TemplateResponse(request, 'sellers/product_form.html', {
        'form': form,
        'formset': formset,
        'image_formset': image_formset,
        'seller': seller,
        'product': product,
    })


@login_required(login_url='/users/login')
def product_delete(request, slug):
    if not request.user.can_access_seller_dashboard:
        return redirect('sellers:register')

    seller = require_seller(request.user)
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
    if not request.user.can_access_seller_dashboard:
        return redirect('sellers:register')

    seller = require_seller(request.user)
    order_items = get_seller_order_items(seller)

    return TemplateResponse(request, 'sellers/orders.html', {
        'seller': seller,
        'order_items': order_items,
    })


@login_required(login_url='/users/login')
def order_detail(request, order_id):
    if not request.user.can_access_seller_dashboard:
        return redirect('sellers:register')

    seller = require_seller(request.user)
    order = get_object_or_404(Order, id=order_id)
    items = get_seller_order_detail(seller, order)

    return TemplateResponse(request, 'sellers/order_detail.html', {
        'seller': seller,
        'order': order,
        'items': items,
    })


@login_required(login_url='/users/login')
def analytics(request):
    if not request.user.can_access_seller_dashboard:
        return redirect('sellers:register')

    seller = require_seller(request.user)
    context = {'seller': seller, **get_seller_analytics(seller)}
    return TemplateResponse(request, 'sellers/analytics.html', context)


def shop_page(request, shop_slug):
    seller = get_object_or_404(Seller, shop_slug=shop_slug, status='verified')
    products = seller.products.order_by('-created_at')

    return TemplateResponse(request, 'sellers/shop.html', {
        'seller': seller,
        'products': products,
    })
