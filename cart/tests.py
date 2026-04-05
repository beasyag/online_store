from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from cart.models import Cart, CartItem
from main.models import Category, Product, ProductSize, Size
from sellers.models import Seller
from users.models import CustomUser


class CartStockTests(TestCase):
    def setUp(self):
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
            stock=2,
        )

    def get_cart(self):
        session = self.client.session
        if not session.session_key:
            session.save()
        cart, _ = Cart.objects.get_or_create(session_key=session.session_key)
        return cart

    def test_add_to_cart_requires_size_for_sized_product(self):
        response = self.client.post(
            reverse('cart:add_to_cart', kwargs={'slug': self.product.slug}),
            data={'quantity': 1},
        )

        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content,
            {'error': 'Invalid form data', 'errors': {'size_id': ['This field is required.']}},
        )

    def test_add_to_cart_rejects_quantity_above_stock(self):
        response = self.client.post(
            reverse('cart:add_to_cart', kwargs={'slug': self.product.slug}),
            data={'quantity': 3, 'size_id': self.product_size.id},
        )

        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'error': 'Only 2 items available'})

    def test_add_to_cart_rejects_total_quantity_above_stock(self):
        self.client.post(
            reverse('cart:add_to_cart', kwargs={'slug': self.product.slug}),
            data={'quantity': 1, 'size_id': self.product_size.id},
        )

        response = self.client.post(
            reverse('cart:add_to_cart', kwargs={'slug': self.product.slug}),
            data={'quantity': 2, 'size_id': self.product_size.id},
        )

        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'error': 'Only 1 more available'})
        self.assertEqual(self.get_cart().items.get().quantity, 1)

    def test_update_cart_item_rejects_quantity_above_stock(self):
        cart = self.get_cart()
        item = CartItem.objects.create(
            cart=cart,
            product=self.product,
            product_size=self.product_size,
            quantity=1,
        )

        response = self.client.post(
            reverse('cart:update_item', kwargs={'item_id': item.id}),
            data={'quantity': 4},
        )

        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'error': 'Only 2 items available'})
        item.refresh_from_db()
        self.assertEqual(item.quantity, 1)
