from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from cart.models import Cart, CartItem
from main.models import Category, Product, ProductSize, Size
from orders.models import Order
from sellers.models import Seller
from users.models import CustomUser


class CheckoutFlowTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
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
            commission_rate=Decimal('10.00'),
        )
        category = Category.objects.create(name='Shoes', slug='shoes')
        size = Size.objects.create(name='42', kind=Size.KindChoices.SHOES)
        self.product = Product.objects.create(
            seller=self.seller,
            name='Runner',
            slug='runner',
            category=category,
            price=Decimal('120.00'),
            main_image='products/main/test.jpg',
            size_kind=Size.KindChoices.SHOES,
        )
        self.product_size = ProductSize.objects.create(
            product=self.product,
            size=size,
            stock=5,
        )

    def login_with_cart(self):
        self.client.force_login(self.user)
        session = self.client.session
        if not session.session_key:
            session.save()
        Cart.objects.create(session_key=session.session_key)

    @patch('orders.services.create_stripe_checkout_session')
    def test_checkout_creates_single_order_item_per_cart_item(self, mock_checkout):
        self.login_with_cart()
        cart = Cart.objects.get(session_key=self.client.session.session_key)
        CartItem.objects.create(
            cart=cart,
            product=self.product,
            product_size=self.product_size,
            quantity=2,
        )
        mock_checkout.return_value = SimpleNamespace(url='https://stripe.test/session')

        response = self.client.post(
            reverse('orders:checkout'),
            data={
                'payment_provider': 'stripe',
                'first_name': 'Buyer',
                'last_name': 'User',
                'email': self.user.email,
                'address1': 'Street 1',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.get()
        self.assertEqual(order.items.count(), 1)
        item = order.items.get()
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.seller, self.seller)
        self.assertEqual(item.seller_amount, Decimal('108.00'))
        self.assertEqual(cart.items.count(), 0)

    def test_checkout_rejects_unsupported_payment_provider(self):
        self.login_with_cart()
        cart = Cart.objects.get(session_key=self.client.session.session_key)
        CartItem.objects.create(
            cart=cart,
            product=self.product,
            product_size=self.product_size,
            quantity=1,
        )

        response = self.client.post(
            reverse('orders:checkout'),
            data={
                'payment_provider': 'cash',
                'first_name': 'Buyer',
                'last_name': 'User',
                'email': self.user.email,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please select a valid payment provider')
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(cart.items.count(), 1)

    @patch('orders.services.create_stripe_checkout_session', side_effect=Exception('stripe down'))
    def test_checkout_payment_failure_rolls_back_order_and_keeps_cart(self, _mock_checkout):
        self.login_with_cart()
        cart = Cart.objects.get(session_key=self.client.session.session_key)
        CartItem.objects.create(
            cart=cart,
            product=self.product,
            product_size=self.product_size,
            quantity=1,
        )

        response = self.client.post(
            reverse('orders:checkout'),
            data={
                'payment_provider': 'stripe',
                'first_name': 'Buyer',
                'last_name': 'User',
                'email': self.user.email,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(cart.items.count(), 1)
