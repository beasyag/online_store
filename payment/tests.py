from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from main.models import Category, Product, ProductSize, Size
from orders.models import Order, OrderItem
from sellers.models import Seller
from users.models import CustomUser


class StripeWebhookTests(TestCase):
    def setUp(self):
        buyer = CustomUser.objects.create_user(
            email='buyer@example.com',
            first_name='Buyer',
            last_name='User',
            password='testpass123',
        )
        seller_user = CustomUser.objects.create_user(
            email='seller@example.com',
            first_name='Seller',
            last_name='User',
            password='testpass123',
            role='seller',
        )
        self.seller = Seller.objects.create(
            user=seller_user,
            shop_name='Seller Shop',
            shop_slug='seller-shop',
            status='verified',
            balance=Decimal('0.00'),
        )
        category = Category.objects.create(name='Shoes', slug='shoes')
        size = Size.objects.create(name='42', kind=Size.KindChoices.SHOES)
        product = Product.objects.create(
            seller=self.seller,
            name='Runner',
            slug='runner',
            category=category,
            price=Decimal('120.00'),
            main_image='products/main/test.jpg',
            size_kind=Size.KindChoices.SHOES,
        )
        product_size = ProductSize.objects.create(product=product, size=size, stock=5)
        self.order = Order.objects.create(
            user=buyer,
            first_name='Buyer',
            last_name='User',
            email='buyer@example.com',
            total_price=Decimal('120.00'),
            status='pending',
            payment_provider='stripe',
        )
        OrderItem.objects.create(
            order=self.order,
            product=product,
            size=product_size,
            seller=self.seller,
            product_name=product.name,
            size_name=size.name,
            quantity=2,
            price=Decimal('120.00'),
            seller_amount=Decimal('90.00'),
        )

    @patch('payment.views.stripe.Webhook.construct_event')
    def test_webhook_is_idempotent_for_seller_balance(self, mock_construct_event):
        mock_construct_event.return_value = {
            'type': 'checkout.session.completed',
            'data': {
                'object': {
                    'metadata': {'order_id': str(self.order.id)},
                    'payment_intent': 'pi_test_123',
                    'id': 'cs_test_123',
                }
            },
        }

        for _ in range(2):
            response = self.client.post(
                reverse('payment:stripe-webhook'),
                data='{}',
                content_type='application/json',
                HTTP_STRIPE_SIGNATURE='sig_test',
            )
            self.assertEqual(response.status_code, 200)

        self.order.refresh_from_db()
        self.seller.refresh_from_db()
        self.assertEqual(self.order.status, 'paid')
        self.assertEqual(self.order.stripe_payment_intent_id, 'pi_test_123')
        self.assertEqual(self.order.stripe_checkout_session_id, 'cs_test_123')
        self.assertEqual(self.seller.balance, Decimal('180.00'))

    @patch('payment.views.stripe.Webhook.construct_event')
    def test_expired_checkout_cancels_pending_order(self, mock_construct_event):
        mock_construct_event.return_value = {
            'type': 'checkout.session.expired',
            'data': {'object': {'metadata': {'order_id': str(self.order.id)}}},
        }

        response = self.client.post(
            reverse('payment:stripe-webhook'),
            data='{}',
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='sig_test',
        )

        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'cancelled')
        self.assertIsNotNone(self.order.cancelled_at)

    @patch('payment.views.stripe.Webhook.construct_event')
    def test_full_refund_reverses_seller_balance_once(self, mock_construct_event):
        self.order.mark_paid(payment_intent_id='pi_test_123', checkout_session_id='cs_test_123')
        self.seller.refresh_from_db()
        self.assertEqual(self.seller.balance, Decimal('180.00'))

        mock_construct_event.return_value = {
            'type': 'charge.refunded',
            'data': {
                'object': {
                    'payment_intent': 'pi_test_123',
                    'amount': 24000,
                    'amount_refunded': 24000,
                    'refunds': {'data': [{'id': 're_test_123'}]},
                }
            },
        }

        for _ in range(2):
            response = self.client.post(
                reverse('payment:stripe-webhook'),
                data='{}',
                content_type='application/json',
                HTTP_STRIPE_SIGNATURE='sig_test',
            )
            self.assertEqual(response.status_code, 200)

        self.order.refresh_from_db()
        self.seller.refresh_from_db()
        self.assertEqual(self.order.status, 'refunded')
        self.assertEqual(self.order.stripe_refund_id, 're_test_123')
        self.assertEqual(self.order.refunded_amount, Decimal('240.00'))
        self.assertEqual(self.seller.balance, Decimal('0.00'))

    def test_cancel_view_does_not_cancel_paid_order(self):
        self.order.mark_paid(payment_intent_id='pi_test_123', checkout_session_id='cs_test_123')

        response = self.client.get(
            reverse('payment:stripe-cancel'),
            {'order_id': self.order.id},
        )

        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'paid')
