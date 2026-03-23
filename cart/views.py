from django.shortcuts import get_object_or_404
from django.views.generic import View
from django.http import JsonResponse
from django.template.response import TemplateResponse
from django.db import transaction
from main.models import Product, ProductSize, Size
from .models import Cart, CartItem
from .forms import AddToCartForm


class CartMixin:
    def get_cart(self, request):
        if hasattr(request, 'cart'):
            return request.cart

        if not request.session.session_key:
            request.session.create()

        cart, created = Cart.objects.get_or_create(
            session_key=request.session.session_key
        )

        request.session['cart_id'] = cart.id
        request.session.modified = True
        return cart


class CartModalView(CartMixin, View):
    def get(self, request):
        cart = self.get_cart(request)
        context = {
            'cart': cart,
            'cart_items': cart.items.select_related(
                'product',
                'product_size__size'
            ).order_by('-added_at')
        }
        return TemplateResponse(request, 'cart/cart_modal.html', context)


class AddToCartView(CartMixin, View):
    @transaction.atomic
    def post(self, request, slug):
        cart = self.get_cart(request)
        product = get_object_or_404(Product, slug=slug)

        # ← если у товара нет размеров — size_id не нужен
        has_sizes = (
            product.product_type and
            (product.product_type.has_sizes or product.product_type.has_shoe_sizes)
        )

        if has_sizes:
            form = AddToCartForm(request.POST, product=product)
            if not form.is_valid():
                return JsonResponse({'error': 'Invalid form data'}, status=400)
            size_id = form.cleaned_data.get('size_id')
            product_size = get_object_or_404(ProductSize, id=size_id, product=product)
            quantity = form.cleaned_data['quantity']
        else:
            # ← для аксессуаров, сумок, парфюмерии — без размера
            product_size = product.product_sizes.first()
            quantity = int(request.POST.get('quantity', 1))

            if not product_size:
                # создаём заглушку ProductSize без размера
                default_size, _ = Size.objects.get_or_create(name='One Size')
                product_size, _ = ProductSize.objects.get_or_create(
                    product=product,
                    size=default_size,
                    defaults={'stock': 999}
                )

        if product_size.stock < quantity:
            return JsonResponse({
                'error': f'Only {product_size.stock} items available'
            }, status=400)

        cart_item = cart.add_product(product, product_size, quantity)
        request.session['cart_id'] = cart.id
        request.session.modified = True

        if request.headers.get('HX-Request'):
            context = {
                'cart': cart,
                'cart_items': cart.items.select_related(
                    'product', 'product_size__size'
                ).order_by('-added_at')
            }
            return TemplateResponse(request, 'cart/cart_modal.html', context)

        return JsonResponse({
            'success': True,
            'total_items': cart.total_items,
            'message': f"{product.name} added to cart",
            'cart_item_id': cart_item.id
        })


class UpdateCartItemView(CartMixin, View):
    @transaction.atomic
    def post(self, request, item_id):
        cart = self.get_cart(request)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)

        quantity = int(request.POST.get('quantity', 1))

        if quantity < 0:
            return JsonResponse({'error': 'Invalid quantity'}, status=400)

        if quantity == 0:
            cart_item.delete()
        else:
            if quantity > cart_item.product_size.stock:
                return JsonResponse({
                    'error': f'Only {cart_item.product_size.stock} items available'
                }, status=400)

            cart_item.quantity = quantity
            cart_item.save()

        request.session['cart_id'] = cart.id
        request.session.modified = True

        context = {
            'cart': cart,
            'cart_items': cart.items.select_related(
                'product',
                'product_size__size',
            ).order_by('-added_at')
        }
        return TemplateResponse(request, 'cart/cart_modal.html', context)


class RemoveCartItemView(CartMixin, View):
    def post(self, request, item_id):
        cart = self.get_cart(request)

        try:
            cart_item = cart.items.get(id=item_id)
            cart_item.delete()

            request.session['cart_id'] = cart.id
            request.session.modified = True

            context = {
                'cart': cart,
                'cart_items': cart.items.select_related(
                    'product',
                    'product_size__size',
                ).order_by('-added_at')
            }
            return TemplateResponse(request, 'cart/cart_modal.html', context)
        except CartItem.DoesNotExist:
            return JsonResponse({'error': 'Item not found'}, status=400)


class CartCountView(CartMixin, View):
    def get(self, request):
        cart = self.get_cart(request)
        return JsonResponse({
            'total_items': cart.total_items,
            'subtotal': float(cart.subtotal)
        })


class ClearCartView(CartMixin, View):
    def post(self, request):
        cart = self.get_cart(request)
        cart.clear()

        request.session['cart_id'] = cart.id
        request.session.modified = True

        if request.headers.get('HX-Request'):
            return TemplateResponse(request, 'cart/cart_empty.html', {
                'cart': cart
            })
        return JsonResponse({
            'success': True,  # ← исправлена опечатка
            'message': 'Cart cleared'
        })


class CartSummaryView(CartMixin, View):
    def get(self, request):
        cart = self.get_cart(request)
        context = {
            'cart': cart,
            'cart_items': cart.items.select_related(
                'product',
                'product_size__size'
            ).order_by('-added_at')
        }
        return TemplateResponse(request, 'cart/cart_summary.html', context)