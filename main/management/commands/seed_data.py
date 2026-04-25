import requests
import random
from io import BytesIO
from PIL import Image
from faker import Faker
from decimal import Decimal

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.utils import timezone
from datetime import timedelta

from users.models import CustomUser, Address
from sellers.models import Seller
from main.models import Category, Subcategory, Size, Product, ProductSize, ProductImage
from orders.models import Order, OrderItem
from reviews.models import Review
from payouts.models import Payout
from chat.models import Conversation, Message

class Command(BaseCommand):
    help = 'Seeds all apps with test data'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Starting FULL database seeding...'))
        fake = Faker()

        # Helper to generate images
        def generate_image(text, size=(800, 800), keyword=None):
            if not keyword:
                # Try to extract a meaningful keyword from text
                keyword = slugify(text).split('-')[0] or "product"
            
            for attempt in range(3):  # Try 3 times
                try:
                    url = f"https://loremflickr.com/{size[0]}/{size[1]}/{keyword}"
                    response = requests.get(url, timeout=20)  # Increased timeout
                    if response.status_code == 200:
                        return ContentFile(response.content, name=f'{slugify(text)}_{random.randint(1000, 9999)}.jpg')
                except Exception as e:
                    if attempt == 2:
                        self.stdout.write(self.style.ERROR(f"Error fetching image for '{keyword}' after 3 attempts: {e}"))
            
            # Fallback to solid color
            color = (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))
            image = Image.new('RGB', size, color=color)
            img_io = BytesIO()
            image.save(img_io, format='JPEG')
            return ContentFile(img_io.getvalue(), name=f'{slugify(text)}_{random.randint(1000, 9999)}.jpg')

        # 1. Create Sizes
        self.stdout.write('Creating sizes...')
        clothing_sizes = ['XS', 'S', 'M', 'L', 'XL']
        shoe_sizes = ['38', '39', '40', '41', '42', '43', '44']
        accessory_sizes = ['One Size', 'S', 'M', 'L']
        
        for name in clothing_sizes:
            Size.objects.get_or_create(name=name, kind=Size.KindChoices.CLOTHING)
        for name in shoe_sizes:
            Size.objects.get_or_create(name=name, kind=Size.KindChoices.SHOES)
        for name in accessory_sizes:
            Size.objects.get_or_create(name=name, kind=Size.KindChoices.ACCESSORIES)

        all_cloth_sizes = list(Size.objects.filter(kind=Size.KindChoices.CLOTHING))
        all_shoe_sizes = list(Size.objects.filter(kind=Size.KindChoices.SHOES))
        all_accessory_sizes = list(Size.objects.filter(kind=Size.KindChoices.ACCESSORIES))

        # 2. Create Categories & Subcategories
        self.stdout.write('Creating categories...')
        categories_data = {
            'Clothing': ['T-Shirts', 'Jeans', 'Jackets', 'Dresses'],
            'Shoes': ['Sneakers', 'Boots', 'Sandals', 'Formal'],
            'Accessories': ['Hats', 'Belts', 'Bags', 'Watches']
        }
        
        created_categories = []
        for cat_name, subcats in categories_data.items():
            cat, _ = Category.objects.get_or_create(name=cat_name)
            created_categories.append(cat)
            for sub_name in subcats:
                Subcategory.objects.get_or_create(category=cat, name=sub_name)

        subcategories = list(Subcategory.objects.all())

        # 3. Create Buyers
        self.stdout.write('Creating buyers...')
        buyers = []
        for i in range(5):
            email = f"buyer{i}@example.com"
            user, created = CustomUser.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': fake.first_name(),
                    'last_name': fake.last_name(),
                }
            )
            if created:
                user.set_password('password123')
                user.save()
            buyers.append(user)

        # 4. Create Sellers
        self.stdout.write('Creating sellers...')
        sellers = []
        for i in range(5):
            email = f"seller{i}@example.com"
            user, created = CustomUser.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': fake.first_name(),
                    'last_name': fake.last_name(),
                }
            )
            if created:
                user.set_password('password123')
                user.save()
            
            seller, s_created = Seller.objects.get_or_create(
                user=user,
                shop_slug=f"shop-{i}",
                defaults={
                    'shop_name': f"{fake.company()} Shop",
                    'description': fake.text(max_nb_chars=200),
                    'status': 'verified',
                    'balance': 0
                }
            )
            if s_created:
                seller.logo.save(f"logo_{i}.jpg", generate_image("logo", (200, 200)))
            sellers.append(seller)

        # 5. Create Products
        self.stdout.write('Creating products...')
        all_products = []
        
        for seller in sellers:
            for _ in range(random.randint(5, 8)):  
                subcat = random.choice(subcategories)
                cat = subcat.category
                
                size_kind = Size.KindChoices.CLOTHING
                if cat.name == 'Shoes':
                    size_kind = Size.KindChoices.SHOES
                elif cat.name == 'Accessories':
                    size_kind = Size.KindChoices.ACCESSORIES

                prod_name = f"{fake.word().capitalize()} {subcat.name}"
                unique_slug = slugify(f"{prod_name}-{random.randint(1000, 99999)}")
                
                price = Decimal(str(round(random.uniform(10.0, 200.0), 2)))
                
                product = Product.objects.create(
                    seller=seller,
                    category=cat,
                    subcategory=subcat,
                    name=prod_name,
                    slug=unique_slug,
                    size_kind=size_kind,
                    price=price,
                    description=fake.text(),
                    color=fake.color_name()
                )
                
                # Use category name as keyword for better images
                img_keyword = cat.name.lower()
                product.main_image.save("prod.jpg", generate_image(prod_name, keyword=img_keyword))
                all_products.append(product)

                # Extra images
                for _ in range(random.randint(0, 2)):
                    img = ProductImage(product=product)
                    img.image.save("extra.jpg", generate_image(prod_name + " extra", keyword=img_keyword))
                
                # Sizes
                if size_kind == Size.KindChoices.SHOES:
                    sizes_to_use = all_shoe_sizes
                elif size_kind == Size.KindChoices.ACCESSORIES:
                    sizes_to_use = all_accessory_sizes
                else:
                    sizes_to_use = all_cloth_sizes
                
                if sizes_to_use:
                    selected_sizes = random.sample(sizes_to_use, k=random.randint(2, min(5, len(sizes_to_use))))
                    for s in selected_sizes:
                        ProductSize.objects.create(
                            product=product,
                            size=s,
                            stock=random.randint(10, 50)
                        )

        # 6. Create Reviews
        self.stdout.write('Creating reviews...')
        for product in all_products:
            # Random amount of reviews 0-3
            for _ in range(random.randint(0, 3)):
                buyer = random.choice(buyers)
                Review.objects.get_or_create(
                    product=product,
                    user=buyer,
                    defaults={
                        'rating': random.randint(1, 5),
                        'comment': fake.sentence() if random.choice([True, False]) else ''
                    }
                )

        # 7. Create Orders
        self.stdout.write('Creating orders...')
        orders = []
        for buyer in buyers:
            # 1 to 3 orders per buyer
            for _ in range(random.randint(1, 3)):
                order = Order.objects.create(
                    user=buyer,
                    first_name=buyer.first_name,
                    last_name=buyer.last_name,
                    email=buyer.email,
                    address1=fake.street_address(),
                    city=fake.city(),
                    country=fake.country(),
                    postal_code=fake.postcode(),
                    total_price=Decimal(0),
                    status=random.choice(['paid', 'shipped', 'delivered'])
                )
                
                # Add random 1-4 items
                order_total = Decimal(0)
                selected_products = random.sample(all_products, k=random.randint(1, 4))
                for prod in selected_products:
                    # Pick random product size
                    prod_size = prod.product_sizes.first()
                    qty = random.randint(1, 3)
                    price = prod.price * qty
                    order_total += price
                    
                    OrderItem.objects.create(
                        order=order,
                        product=prod,
                        size=prod_size,
                        seller=prod.seller,
                        seller_amount=prod.price,
                        quantity=qty,
                        price=prod.price
                    )
                
                # Update total and simulate payment logic applied credits
                order.total_price = order_total
                order.paid_at = timezone.now() - timedelta(days=random.randint(1, 30))
                order.save()
                
                # Credit seller balance manually since it's testing
                for item in order.items.all():
                    item.seller.balance += item.seller_amount * item.quantity
                    item.seller.save()
                order.seller_balance_applied_at = order.paid_at
                order.stripe_payment_intent_id = f"pi_{fake.word()}"
                order.save()

        # 8. Create Payouts
        self.stdout.write('Creating payouts...')
        for seller in sellers:
            if seller.balance > 50:
                payout_amount = min(Decimal(50), seller.balance)
                seller.balance -= payout_amount
                seller.save()
                Payout.objects.create(
                    seller=seller,
                    amount=payout_amount,
                    status=random.choice(['pending', 'completed']),
                    payment_method='Bank Transfer',
                )

        # 9. Create Chats
        self.stdout.write('Creating chat conversations...')
        for _ in range(10):
            buyer = random.choice(buyers)
            seller = random.choice(sellers)
            conv, _ = Conversation.objects.get_or_create(buyer=buyer, seller=seller)
            
            # Create a few messages
            for _ in range(random.randint(2, 6)):
                sender = buyer if random.choice([True, False]) else seller.user
                Message.objects.create(
                    conversation=conv,
                    sender=sender,
                    text=fake.text(max_nb_chars=100)
                )

        self.stdout.write(self.style.SUCCESS('\nSUCCESS! Database fully seeded with buyers, reviews, orders, payouts, and chats.'))
        self.stdout.write(self.style.SUCCESS('Login credentials logic:'))
        self.stdout.write('- Sellers: seller0@example.com ... seller4@example.com (pass: password123)')
        self.stdout.write('- Buyers: buyer0@example.com ... buyer4@example.com (pass: password123)')
