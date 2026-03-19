from django.db import models
from django.conf import settings
from main.models import Product, ProductSize
from decimal import Decimal


class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )

    PAYMENT_PROVIDER_CHOICES = (
        ('stripe', 'Stripe'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,  # ← история заказов сохраняется при удалении юзера
        null=True,
        related_name='orders'
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=254)
    company = models.CharField(max_length=100, blank=True, null=True)
    address1 = models.CharField(max_length=255, blank=True, null=True)  # ← 255
    address2 = models.CharField(max_length=255, blank=True, null=True)  # ← 255
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    province = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)  # ← 30
    special_instructions = models.TextField(blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_provider = models.CharField(
        max_length=20,
        choices=PAYMENT_PROVIDER_CHOICES,
        default='stripe',
        null=True,
        blank=True
    )
    platform_commission = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.id} by {self.email}"

    def get_total_price(self):  # ← метод на уровне Order
        return sum(item.get_total_price() for item in self.items.all())

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_address(self):
        parts = filter(None, [self.address1, self.address2, self.city, self.province, self.postal_code, self.country])
        return ', '.join(parts)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,  # ← товар можно удалить из каталога
        null=True,
        blank=True
    )
    size = models.ForeignKey(
        ProductSize,
        on_delete=models.SET_NULL,  # ← размер можно удалить
        null=True,
        blank=True
    )
    # ← snapshot полей на момент заказа
    seller = models.ForeignKey(
        'sellers.Seller',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='order_items'
    )
    seller_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    product_name = models.CharField(max_length=100, blank=True)
    size_name = models.CharField(max_length=20, blank=True)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        # ← сохраняем название товара и размера при создании
        if self.product and not self.product_name:
            self.product_name = self.product.name
        if self.size and not self.size_name:
            self.size_name = self.size.size.name
        super().save(*args, **kwargs)

    def __str__(self):
        name = self.product_name or (self.product.name if self.product else 'Deleted product')
        size = self.size_name or (self.size.size.name if self.size else 'Deleted size')
        return f"{name} - {size} ({self.quantity})"

    def get_total_price(self):
        return self.price * self.quantity