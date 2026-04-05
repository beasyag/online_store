from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.views.generic import View
from .forms import OrderForm
from cart.views import CartMixin
from .services import (
    InvalidPaymentProviderError,
    create_order_from_cart,
    start_checkout_payment,
)
import logging

logger = logging.getLogger(__name__)


@method_decorator(login_required(login_url='/users/login'), name='dispatch')
class CheckoutView(CartMixin, View):

    def get_cart_context(self, cart):
        return {
            'cart': cart,
            'cart_items': cart.items.select_related(
                'product',
                'product_size__size'
            ).order_by('-added_at'),
        }

    def get(self, request):
        cart = self.get_cart(request)
        logger.debug(
            f"Checkout GET: cart_id={cart.id}, "
            f"total_items={cart.total_items}, subtotal={cart.subtotal}"
        )

        if cart.total_items == 0:
            logger.warning("Cart is empty")
            if request.headers.get('HX-Request'):
                return TemplateResponse(request, 'orders/empty_cart.html', {'message': 'No items available'})
            return redirect('cart:cart_modal')

        context = {
            **self.get_cart_context(cart),
            'form': OrderForm(user=request.user),
            'total_price': cart.subtotal,
        }

        if request.headers.get('HX-Request'):
            return TemplateResponse(request, 'orders/checkout_content.html', context)
        return render(request, 'orders/checkout.html', context)

    def post(self, request):
        cart = self.get_cart(request)
        order = None
        payment_provider = request.POST.get('payment_provider')
        logger.debug(
            f"Checkout POST: cart_id={cart.id}, "
            f"total_items={cart.total_items}, payment_provider={payment_provider}"
        )

        if cart.total_items == 0:
            logger.warning("Cart is empty")
            if request.headers.get('HX-Request'):
                return TemplateResponse(request, 'orders/empty_cart.html', {'message': 'No items available'})
            return redirect('cart:cart_modal')

        # ← убран 'heleket' — его нет в модели
        if not payment_provider:
            logger.error(f"Invalid payment provider: {payment_provider}")
            context = {
                **self.get_cart_context(cart),
                'form': OrderForm(user=request.user),
                'total_price': cart.subtotal,
                'error_message': 'Please select a valid payment provider',
            }
            if request.headers.get('HX-Request'):
                return TemplateResponse(request, 'orders/checkout_content.html', context)
            return render(request, 'orders/checkout.html', context)

        form_data = request.POST.copy()
        if not form_data.get('email'):
            form_data['email'] = request.user.email
        form = OrderForm(form_data, user=request.user)

        if not form.is_valid():
            logger.warning(f"Form validation error: {form.errors}")
            context = {
                **self.get_cart_context(cart),
                'form': form,
                'total_price': cart.subtotal,
                'error_message': 'Please correct the errors on the form.',
            }
            if request.headers.get('HX-Request'):
                return TemplateResponse(request, 'orders/checkout_content.html', context)
            return render(request, 'orders/checkout.html', context)

        try:
            order = create_order_from_cart(
                user=request.user,
                cart=cart,
                cleaned_data=form.cleaned_data,
                payment_provider=payment_provider,
            )
            logger.info(f"Creating payment session for provider: {payment_provider}")
            checkout = start_checkout_payment(order=order, cart=cart, request=request)
            if request.headers.get('HX-Request'):
                response = HttpResponse(status=200)
                response['HX-Redirect'] = checkout.redirect_url
                logger.info(f"HX-Redirect to Stripe: {checkout.redirect_url}")
                return response
            return redirect(checkout.redirect_url)
        except InvalidPaymentProviderError:
            context = {
                **self.get_cart_context(cart),
                'form': form,
                'total_price': cart.subtotal,
                'error_message': 'Please select a valid payment provider',
            }
            if request.headers.get('HX-Request'):
                return TemplateResponse(request, 'orders/checkout_content.html', context)
            return render(request, 'orders/checkout.html', context)
        except Exception as e:
            logger.error(f"Error creating payment: {str(e)}", exc_info=True)
            if order is not None:
                order.delete()
            context = {
                **self.get_cart_context(cart),
                'form': form,
                'total_price': cart.subtotal,
                'error_message': 'Payment processing error. Please try again.',
            }
            if request.headers.get('HX-Request'):
                return TemplateResponse(request, 'orders/checkout_content.html', context)
            return render(request, 'orders/checkout.html', context)
