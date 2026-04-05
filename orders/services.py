from dataclasses import dataclass
from decimal import Decimal

from django.db import transaction

from orders.models import Order, OrderItem
from payment.views import create_stripe_checkout_session


VALID_PAYMENT_PROVIDERS = {'stripe'}


class CheckoutError(Exception):
    pass


class InvalidPaymentProviderError(CheckoutError):
    pass


@dataclass
class CheckoutStartResult:
    redirect_url: str


def build_order_items(order, cart):
    order_items = []
    for item in cart.items.select_related('product__seller', 'product_size__size'):
        seller = item.product.seller
        commission_rate = seller.commission_rate if seller else Decimal('10.00')
        seller_amount = item.product.price * (
            Decimal('1.00') - (Decimal(str(commission_rate)) / Decimal('100.00'))
        )
        order_items.append(
            OrderItem(
                order=order,
                product=item.product,
                size=item.product_size,
                product_name=item.product.name,
                size_name=item.product_size.size.name,
                seller=seller,
                quantity=item.quantity,
                price=item.product.price or Decimal('0.00'),
                seller_amount=seller_amount,
            )
        )
    return order_items


def ensure_supported_payment_provider(payment_provider):
    if payment_provider not in VALID_PAYMENT_PROVIDERS:
        raise InvalidPaymentProviderError(f'Unsupported payment provider: {payment_provider}')


@transaction.atomic
def create_order_from_cart(*, user, cart, cleaned_data, payment_provider):
    ensure_supported_payment_provider(payment_provider)
    order = Order.objects.create(
        user=user,
        first_name=cleaned_data['first_name'],
        last_name=cleaned_data['last_name'],
        email=cleaned_data['email'],
        company=cleaned_data['company'],
        address1=cleaned_data['address1'],
        address2=cleaned_data['address2'],
        city=cleaned_data['city'],
        country=cleaned_data['country'],
        province=cleaned_data['province'],
        postal_code=cleaned_data['postal_code'],
        phone=cleaned_data['phone'],
        special_instructions='',
        total_price=cart.subtotal,
        payment_provider=payment_provider,
    )
    OrderItem.objects.bulk_create(build_order_items(order, cart))
    return order


def start_checkout_payment(*, order, cart, request):
    if order.payment_provider == 'stripe':
        checkout_session = create_stripe_checkout_session(order, cart, request)
        cart.clear()
        return CheckoutStartResult(redirect_url=checkout_session.url)
    raise InvalidPaymentProviderError(f'Unsupported payment provider: {order.payment_provider}')
