import stripe
from decimal import Decimal
from django.conf import settings
from django.db import transaction
from django.shortcuts import redirect, get_object_or_404, render
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from orders.models import Order

stripe.api_key = settings.STRIPE_SECRET_KEY
stripe_endpoint_secret = settings.STRIPE_WEBHOOK_SECRET


def create_stripe_checkout_session(order, cart, request):
    # ← cart передаётся явно, не создаётся заново
    line_items = []
    for item in cart.items.select_related('product', 'product_size__size'):
        line_items.append({
            'price_data': {
                'currency': 'usd',  # ← единая валюта
                'product_data': {
                    'name': f'{item.product.name} - {item.product_size.size.name}',
                },
                'unit_amount': int(item.product.price * 100),
            },
            'quantity': item.quantity,
        })

    checkout_session = stripe.checkout.Session.create(
        line_items=line_items,
        mode='payment',
        success_url=(
            request.build_absolute_uri('/payment/stripe/success/')
            + '?session_id={CHECKOUT_SESSION_ID}'
        ),
        cancel_url=(
            request.build_absolute_uri('/payment/stripe/cancel/')
            + f'?order_id={order.id}'  # ← ? уже был исправлен
        ),
        metadata={
            'order_id': order.id,
        }
    )

    order.stripe_payment_intent_id = checkout_session.payment_intent
    order.stripe_checkout_session_id = checkout_session.id
    order.payment_provider = 'stripe'
    order.save(update_fields=['stripe_payment_intent_id', 'stripe_checkout_session_id', 'payment_provider', 'updated_at'])

    return checkout_session


@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, stripe_endpoint_secret
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    event_type = event['type']

    if event_type == 'checkout.session.completed':
        session = event['data']['object']
        order_id = session['metadata'].get('order_id')
        try:
            with transaction.atomic():
                order = Order.objects.select_for_update().get(id=order_id)
                order.mark_paid(
                    payment_intent_id=session.get('payment_intent'),
                    checkout_session_id=session.get('id'),
                )
        except Order.DoesNotExist:
            return HttpResponse(status=400)

    elif event_type == 'checkout.session.expired':
        session = event['data']['object']
        order_id = session['metadata'].get('order_id')
        try:
            with transaction.atomic():
                order = Order.objects.select_for_update().get(id=order_id)
                order.mark_cancelled()
        except Order.DoesNotExist:
            return HttpResponse(status=400)

    elif event_type == 'charge.refunded':
        charge = event['data']['object']
        payment_intent_id = charge.get('payment_intent')
        try:
            with transaction.atomic():
                order = Order.objects.select_for_update().get(
                    stripe_payment_intent_id=payment_intent_id
                )
                amount_refunded = charge.get('amount_refunded') or 0
                amount_total = charge.get('amount') or 0
                if amount_total and amount_refunded >= amount_total:
                    refunds = charge.get('refunds', {}).get('data', [])
                    refund_id = refunds[0].get('id') if refunds else None
                    order.mark_refunded(
                        refund_id=refund_id,
                        refunded_amount=Decimal(amount_refunded) / Decimal('100'),
                    )
        except Order.DoesNotExist:
            return HttpResponse(status=400)

    return HttpResponse(status=200)


def stripe_success(request):
    session_id = request.GET.get('session_id')
    if not session_id:
        return redirect('main:index')  # ← исправлен синтаксис

    try:
        session = stripe.checkout.Session.retrieve(session_id)
        order_id = session.metadata.get('order_id')
        order = get_object_or_404(Order, id=order_id)

        context = {'order': order}
        if request.headers.get('HX-Request'):
            return TemplateResponse(request, 'payment/stripe_success_content.html', context)
        return render(request, 'payment/stripe_success.html', context)

    except Exception:
        return redirect('main:index')


def stripe_cancel(request):
    order_id = request.GET.get('order_id')
    if not order_id:
        return redirect('orders:checkout')

    order = get_object_or_404(Order, id=order_id)
    order.mark_cancelled()

    context = {'order': order}
    if request.headers.get('HX-Request'):
        return TemplateResponse(request, 'payment/stripe_cancel_content.html', context)
    return render(request, 'payment/stripe_cancel.html', context)
