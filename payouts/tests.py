from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from payouts.models import Payout
from sellers.models import Seller
from users.models import CustomUser


class PayoutRequestTests(TestCase):
    def setUp(self):
        user = CustomUser.objects.create_user(
            email='seller@example.com',
            first_name='Seller',
            last_name='User',
            password='testpass123',
            role='seller',
        )
        self.seller = Seller.objects.create(
            user=user,
            shop_name='Seller Shop',
            shop_slug='seller-shop',
            status='verified',
            balance=Decimal('250.00'),
        )
        self.client.force_login(user)

    def test_rejects_invalid_payout_amount(self):
        response = self.client.post(reverse('payouts:request'), {'amount': 'abc'})

        self.assertEqual(response.status_code, 302)
        self.seller.refresh_from_db()
        self.assertEqual(self.seller.balance, Decimal('250.00'))

    def test_rejects_payout_above_balance(self):
        response = self.client.post(reverse('payouts:request'), {'amount': '300.00'})

        self.assertEqual(response.status_code, 302)
        self.seller.refresh_from_db()
        self.assertEqual(self.seller.balance, Decimal('250.00'))

    def test_reserves_balance_with_decimal_precision(self):
        response = self.client.post(reverse('payouts:request'), {'amount': '100.10'})

        self.assertEqual(response.status_code, 302)
        self.seller.refresh_from_db()
        self.assertEqual(self.seller.balance, Decimal('149.90'))

    def test_failed_payout_releases_reserved_balance_once(self):
        self.client.post(reverse('payouts:request'), {'amount': '100.10'})
        payout = Payout.objects.get()

        payout.mark_failed()
        payout.refresh_from_db()
        self.seller.refresh_from_db()
        self.assertEqual(payout.status, 'failed')
        self.assertEqual(self.seller.balance, Decimal('250.00'))

        payout.mark_failed()
        self.seller.refresh_from_db()
        self.assertEqual(self.seller.balance, Decimal('250.00'))
