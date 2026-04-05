from decimal import Decimal, InvalidOperation

from django.db import transaction

from payouts.models import Payout


class PayoutRequestError(Exception):
    pass


def parse_payout_amount(raw_amount):
    if not raw_amount:
        raise PayoutRequestError('Please enter an amount.')
    try:
        amount = Decimal(raw_amount)
    except InvalidOperation as exc:
        raise PayoutRequestError('Enter a valid payout amount.') from exc
    if amount <= Decimal('0.00'):
        raise PayoutRequestError('Payout amount must be greater than zero.')
    return amount


@transaction.atomic
def create_payout_request(*, seller, requested_by, raw_amount, payment_method=''):
    amount = parse_payout_amount(raw_amount)
    seller.refresh_from_db(fields=['balance'])
    if amount > seller.balance:
        raise PayoutRequestError('Insufficient balance.')

    payout = Payout.objects.create(
        seller=seller,
        amount=amount,
        payment_method=payment_method,
        payment_details={'requested_by': requested_by},
    )
    seller.balance -= amount
    seller.save(update_fields=['balance', 'updated_at'])
    return payout
