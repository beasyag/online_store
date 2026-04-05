from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from main.models import Category, Product, ProductSize, Size
from orders.models import Order, OrderItem
from sellers.models import Seller
from users.models import CustomUser


class SellerAccessTests(TestCase):
    def setUp(self):
        owner_user = CustomUser.objects.create_user(
            email='owner@example.com',
            first_name='Owner',
            last_name='User',
            password='testpass123',
            role='seller',
        )
        intruder_user = CustomUser.objects.create_user(
            email='intruder@example.com',
            first_name='Intruder',
            last_name='User',
            password='testpass123',
            role='seller',
        )
        owner = Seller.objects.create(
            user=owner_user,
            shop_name='Owner Shop',
            shop_slug='owner-shop',
            status='verified',
        )
        Seller.objects.create(
            user=intruder_user,
            shop_name='Intruder Shop',
            shop_slug='intruder-shop',
            status='verified',
        )
        category = Category.objects.create(name='Shoes', slug='shoes')
        self.product = Product.objects.create(
            seller=owner,
            name='Runner',
            slug='runner',
            category=category,
            price=Decimal('120.00'),
            main_image='products/main/test.jpg',
        )
        self.client.force_login(intruder_user)

    def test_seller_cannot_edit_foreign_product(self):
        response = self.client.get(reverse('sellers:product_edit', kwargs={'slug': self.product.slug}))

        self.assertEqual(response.status_code, 404)


class SellerRoleAndActionTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='buyer@example.com',
            first_name='Buyer',
            last_name='User',
            password='testpass123',
        )
        self.client.force_login(self.user)
        self.category = Category.objects.create(name='Shoes', slug='shoes')
        self.size = Size.objects.create(name='42', kind=Size.KindChoices.SHOES)

    def make_test_image(self):
        return SimpleUploadedFile(
            'test.gif',
            (
                b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00'
                b'\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00'
                b'\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
            ),
            content_type='image/gif',
        )

    def test_seller_register_sets_role_and_redirects_to_dashboard(self):
        response = self.client.post(
            reverse('sellers:register'),
            data={'shop_name': 'New Shop', 'description': 'Test shop'},
        )

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('sellers:dashboard'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, 'seller')
        self.assertTrue(hasattr(self.user, 'seller'))
        self.assertEqual(self.user.seller.status, 'pending')
        self.assertTrue(self.user.can_access_seller_dashboard)
        self.assertFalse(self.user.can_manage_products_as_seller)

    def test_non_seller_dashboard_redirects_to_register(self):
        response = self.client.get(reverse('sellers:dashboard'))

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('sellers:register'))

    def test_unverified_seller_cannot_add_product(self):
        seller = Seller.objects.create(
            user=self.user,
            shop_name='Pending Shop',
            shop_slug='pending-shop',
            status='pending',
        )

        response = self.client.post(
            reverse('sellers:product_add'),
            data={
                'name': 'Pending Product',
                'category': self.category.id,
                'size_kind': Size.KindChoices.SHOES,
                'color': 'Black',
                'price': '120.00',
                'description': 'Blocked',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('sellers:dashboard'))
        self.assertFalse(Product.objects.filter(name='Pending Product', seller=seller).exists())

    def test_verified_seller_can_add_product(self):
        seller = Seller.objects.create(
            user=self.user,
            shop_name='Verified Shop',
            shop_slug='verified-shop',
            status='verified',
        )
        image = self.make_test_image()

        response = self.client.post(
            reverse('sellers:product_add'),
            data={
                'name': 'Verified Product',
                'category': self.category.id,
                'size_kind': Size.KindChoices.SHOES,
                'color': 'Black',
                'price': '120.00',
                'description': 'Allowed',
                'main_image': image,
            },
        )

        product = Product.objects.get(name='Verified Product', seller=seller)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            reverse('sellers:product_edit', kwargs={'slug': product.slug}),
        )

    def test_seller_role_is_derived_from_seller_profile(self):
        self.assertFalse(self.user.can_access_seller_dashboard)
        seller = Seller.objects.create(
            user=self.user,
            shop_name='State Shop',
            shop_slug='state-shop',
            status='pending',
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, 'seller')
        self.assertEqual(self.user.seller_status, 'pending')
        self.assertTrue(self.user.can_access_seller_dashboard)
        self.assertFalse(self.user.can_manage_products_as_seller)

        seller.status = 'verified'
        seller.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.seller_status, 'verified')
        self.assertTrue(self.user.can_manage_products_as_seller)


class SellerAnalyticsTests(TestCase):
    def setUp(self):
        self.seller_user = CustomUser.objects.create_user(
            email='seller@example.com',
            first_name='Seller',
            last_name='User',
            password='testpass123',
        )
        self.seller = Seller.objects.create(
            user=self.seller_user,
            shop_name='Analytics Shop',
            shop_slug='analytics-shop',
            status='verified',
        )
        self.buyer = CustomUser.objects.create_user(
            email='buyer@example.com',
            first_name='Buyer',
            last_name='User',
            password='testpass123',
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
        product_size = ProductSize.objects.create(product=self.product, size=size, stock=10)

        order1 = Order.objects.create(
            user=self.buyer,
            first_name='Buyer',
            last_name='User',
            email='buyer@example.com',
            total_price=Decimal('120.00'),
            status='paid',
        )
        OrderItem.objects.create(
            order=order1,
            product=self.product,
            size=product_size,
            seller=self.seller,
            product_name='Runner',
            size_name='42',
            quantity=1,
            price=Decimal('120.00'),
            seller_amount=Decimal('100.00'),
        )

        order2 = Order.objects.create(
            user=self.buyer,
            first_name='Buyer',
            last_name='User',
            email='buyer@example.com',
            total_price=Decimal('240.00'),
            status='refunded',
        )
        OrderItem.objects.create(
            order=order2,
            product=self.product,
            size=product_size,
            seller=self.seller,
            product_name='Runner',
            size_name='42',
            quantity=2,
            price=Decimal('120.00'),
            seller_amount=Decimal('90.00'),
        )

        order3 = Order.objects.create(
            user=self.buyer,
            first_name='Buyer',
            last_name='User',
            email='buyer@example.com',
            total_price=Decimal('120.00'),
            status='cancelled',
        )
        OrderItem.objects.create(
            order=order3,
            product=self.product,
            size=product_size,
            seller=self.seller,
            product_name='Runner',
            size_name='42',
            quantity=1,
            price=Decimal('120.00'),
            seller_amount=Decimal('90.00'),
        )

        self.client.force_login(self.seller_user)

    def test_analytics_exposes_product_metrics(self):
        response = self.client.get(reverse('sellers:analytics'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_orders'], 3)
        self.assertEqual(response.context['successful_orders'], 2)
        self.assertEqual(response.context['checkout_conversion'], 66.67)
        self.assertEqual(response.context['average_order_value'], Decimal('140.00'))
        self.assertEqual(response.context['repeat_customers'], 1)
        self.assertEqual(response.context['sales_by_product'][0]['total_units'], 4)
