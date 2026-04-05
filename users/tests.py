from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from orders.models import Order
from sellers.models import Seller
from users.models import CustomUser


class UserOrderAccessTests(TestCase):
    def setUp(self):
        self.owner = CustomUser.objects.create_user(
            email='owner@example.com',
            first_name='Owner',
            last_name='User',
            password='testpass123',
        )
        self.other_user = CustomUser.objects.create_user(
            email='other@example.com',
            first_name='Other',
            last_name='User',
            password='testpass123',
        )
        self.order = Order.objects.create(
            user=self.owner,
            first_name='Owner',
            last_name='User',
            email='owner@example.com',
            total_price=Decimal('99.99'),
        )

    def test_user_cannot_view_foreign_order(self):
        self.client.force_login(self.other_user)
        response = self.client.get(reverse('users:order_detail', kwargs={'order_id': self.order.id}))

        self.assertEqual(response.status_code, 404)


class UserSellerStateTests(TestCase):
    def test_dashboard_access_is_based_on_seller_profile_not_raw_role(self):
        user = CustomUser.objects.create_user(
            email='sellerstate@example.com',
            first_name='Seller',
            last_name='State',
            password='testpass123',
            role='buyer',
        )
        self.assertFalse(user.can_access_seller_dashboard)
        self.assertIsNone(user.seller_status)

        Seller.objects.create(
            user=user,
            shop_name='State Shop',
            shop_slug='state-shop',
            status='pending',
        )
        user.refresh_from_db()
        self.assertTrue(user.can_access_seller_dashboard)
        self.assertEqual(user.seller_status, 'pending')
        self.assertEqual(user.role, 'seller')
