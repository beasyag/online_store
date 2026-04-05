from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from main.models import Category, Product, ProductSize, ProductView, Size, Subcategory
from orders.models import Order, OrderItem
from reviews.models import Review
from sellers.models import Seller
from users.models import CustomUser


class PersonalizationTests(TestCase):
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
        )
        self.seller = Seller.objects.create(
            user=seller_user,
            shop_name='Seller Shop',
            shop_slug='seller-shop',
            status='verified',
        )
        category = Category.objects.create(name='Shoes', slug='shoes')
        self.preferred_subcategory = Subcategory.objects.create(
            category=category,
            name='Sneakers',
            slug='sneakers',
        )
        other_subcategory = Subcategory.objects.create(
            category=category,
            name='Boots',
            slug='boots',
        )
        size = Size.objects.create(name='42', kind=Size.KindChoices.SHOES)
        self.purchased_product = Product.objects.create(
            seller=self.seller,
            category=category,
            subcategory=self.preferred_subcategory,
            name='Purchased Runner',
            slug='purchased-runner',
            price=Decimal('120.00'),
            color='Black',
            main_image='products/main/test.jpg',
            size_kind=Size.KindChoices.SHOES,
        )
        self.recommended_product = Product.objects.create(
            seller=self.seller,
            category=category,
            subcategory=self.preferred_subcategory,
            name='Recommended Runner',
            slug='recommended-runner',
            price=Decimal('130.00'),
            color='Black',
            main_image='products/main/test.jpg',
            size_kind=Size.KindChoices.SHOES,
        )
        self.other_product = Product.objects.create(
            seller=self.seller,
            category=category,
            subcategory=other_subcategory,
            name='Other Boot',
            slug='other-boot',
            price=Decimal('150.00'),
            color='Brown',
            main_image='products/main/test.jpg',
            size_kind=Size.KindChoices.SHOES,
        )
        ProductSize.objects.create(product=self.purchased_product, size=size, stock=5)
        ProductSize.objects.create(product=self.recommended_product, size=size, stock=5)
        ProductSize.objects.create(product=self.other_product, size=size, stock=5)
        for index in range(4):
            filler = Product.objects.create(
                seller=self.seller,
                category=category,
                subcategory=other_subcategory,
                name=f'Filler {index}',
                slug=f'filler-{index}',
                price=Decimal('99.00'),
                color='Grey',
                main_image='products/main/test.jpg',
                size_kind=Size.KindChoices.SHOES,
            )
            ProductSize.objects.create(product=filler, size=size, stock=5)

    def test_product_detail_records_authenticated_view(self):
        self.client.force_login(self.user)
        url = reverse('main:product_detail', kwargs={'slug': self.other_product.slug})

        self.client.get(url)
        self.client.get(url)

        product_view = ProductView.objects.get(user=self.user, product=self.other_product)
        self.assertEqual(product_view.view_count, 2)

    def test_homepage_recommendations_prioritize_user_preferences(self):
        order = Order.objects.create(
            user=self.user,
            first_name='Buyer',
            last_name='User',
            email=self.user.email,
            total_price=Decimal('120.00'),
            status='paid',
        )
        OrderItem.objects.create(
            order=order,
            product=self.purchased_product,
            size=self.purchased_product.product_sizes.first(),
            seller=self.seller,
            product_name=self.purchased_product.name,
            size_name='42',
            quantity=1,
            price=Decimal('120.00'),
            seller_amount=Decimal('100.00'),
        )
        ProductView.objects.create(user=self.user, product=self.recommended_product, view_count=3)
        Review.objects.create(
            product=self.recommended_product,
            user=self.user,
            rating=5,
            comment='Love it',
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse('main:index'))

        recommended_products = list(response.context['recommended_products'])
        self.assertTrue(recommended_products)
        self.assertEqual(recommended_products[0], self.recommended_product)
        self.assertNotIn(self.purchased_product, recommended_products)
        self.assertEqual(response.context['rec_title'], 'Recommended for You')

    def test_homepage_exposes_recently_viewed_products(self):
        self.client.force_login(self.user)
        ProductView.objects.create(user=self.user, product=self.other_product, view_count=2)

        response = self.client.get(reverse('main:index'))

        continue_exploring = list(response.context['continue_exploring_products'])
        self.assertIn(self.other_product, continue_exploring)

    def test_homepage_exposes_similar_customer_products(self):
        other_user = CustomUser.objects.create_user(
            email='otherbuyer@example.com',
            first_name='Other',
            last_name='Buyer',
            password='testpass123',
        )
        shared_order = Order.objects.create(
            user=self.user,
            first_name='Buyer',
            last_name='User',
            email=self.user.email,
            total_price=Decimal('120.00'),
            status='paid',
        )
        OrderItem.objects.create(
            order=shared_order,
            product=self.purchased_product,
            size=self.purchased_product.product_sizes.first(),
            seller=self.seller,
            product_name=self.purchased_product.name,
            size_name='42',
            quantity=1,
            price=Decimal('120.00'),
            seller_amount=Decimal('100.00'),
        )
        collaborative_product = Product.objects.create(
            seller=self.seller,
            category=self.purchased_product.category,
            subcategory=self.preferred_subcategory,
            name='Collaborative Pick',
            slug='collaborative-pick',
            price=Decimal('140.00'),
            color='Black',
            main_image='products/main/test.jpg',
            size_kind=Size.KindChoices.SHOES,
        )
        ProductSize.objects.create(
            product=collaborative_product,
            size=self.purchased_product.product_sizes.first().size,
            stock=5,
        )
        for index in range(4):
            filler = Product.objects.create(
                seller=self.seller,
                category=self.purchased_product.category,
                subcategory=self.preferred_subcategory,
                name=f'Collaborative Filler {index}',
                slug=f'collaborative-filler-{index}',
                price=Decimal('111.00'),
                color='Black',
                main_image='products/main/test.jpg',
                size_kind=Size.KindChoices.SHOES,
            )
            ProductSize.objects.create(
                product=filler,
                size=self.purchased_product.product_sizes.first().size,
                stock=5,
            )
        other_order = Order.objects.create(
            user=other_user,
            first_name='Other',
            last_name='Buyer',
            email=other_user.email,
            total_price=Decimal('260.00'),
            status='paid',
        )
        OrderItem.objects.create(
            order=other_order,
            product=self.purchased_product,
            size=self.purchased_product.product_sizes.first(),
            seller=self.seller,
            product_name=self.purchased_product.name,
            size_name='42',
            quantity=1,
            price=Decimal('120.00'),
            seller_amount=Decimal('100.00'),
        )
        OrderItem.objects.create(
            order=other_order,
            product=collaborative_product,
            size=collaborative_product.product_sizes.first(),
            seller=self.seller,
            product_name=collaborative_product.name,
            size_name='42',
            quantity=1,
            price=Decimal('140.00'),
            seller_amount=Decimal('110.00'),
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse('main:index'))

        similar_customer_products = list(response.context['similar_customer_products'])
        self.assertIn(collaborative_product, similar_customer_products)

    def test_catalog_includes_personalized_products_block(self):
        ProductView.objects.create(user=self.user, product=self.recommended_product, view_count=2)

        self.client.force_login(self.user)
        response = self.client.get(reverse('main:catalog_all'))

        personalized_catalog = list(response.context['catalog_personalized_products'])
        self.assertTrue(personalized_catalog)
        self.assertIn(self.recommended_product, personalized_catalog)
