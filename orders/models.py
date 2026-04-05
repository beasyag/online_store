from django.db import models
from django.conf import settings
from main.models import Product, ProductSize
from decimal import Decimal
from django.utils import timezone


class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
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
    refunded_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stripe_checkout_session_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_refund_id = models.CharField(max_length=255, blank=True, null=True)
    seller_balance_applied_at = models.DateTimeField(blank=True, null=True)
    seller_balance_reversed_at = models.DateTimeField(blank=True, null=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)
    refunded_at = models.DateTimeField(blank=True, null=True)
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

    def can_be_cancelled(self):
        return self.status == 'pending'

    def can_be_refunded(self):
        return self.status in {'paid', 'shipped', 'delivered'}

    def apply_seller_credits(self):
        if self.seller_balance_applied_at:
            return False
        now = timezone.now()
        for item in self.items.select_related('seller').all():
            if item.seller and item.seller_amount:
                item.seller.balance += item.seller_amount * item.quantity
                item.seller.save(update_fields=['balance', 'updated_at'])
        self.seller_balance_applied_at = now
        self.seller_balance_reversed_at = None
        return True

    def reverse_seller_credits(self):
        if not self.seller_balance_applied_at or self.seller_balance_reversed_at:
            return False
        now = timezone.now()
        for item in self.items.select_related('seller').all():
            if item.seller and item.seller_amount:
                item.seller.balance -= item.seller_amount * item.quantity
                item.seller.save(update_fields=['balance', 'updated_at'])
        self.seller_balance_reversed_at = now
        return True

    def mark_paid(self, *, payment_intent_id=None, checkout_session_id=None):
        if self.status == 'refunded':
            return False
        changed = False
        if self.status != 'paid':
            self.status = 'paid'
            self.paid_at = self.paid_at or timezone.now()
            changed = True
        if payment_intent_id and self.stripe_payment_intent_id != payment_intent_id:
            self.stripe_payment_intent_id = payment_intent_id
            changed = True
        if checkout_session_id and self.stripe_checkout_session_id != checkout_session_id:
            self.stripe_checkout_session_id = checkout_session_id
            changed = True
        if self.apply_seller_credits():
            changed = True
        if changed:
            self.save()
        return changed

    def mark_cancelled(self):
        if not self.can_be_cancelled():
            return False
        self.status = 'cancelled'
        self.cancelled_at = self.cancelled_at or timezone.now()
        self.save(update_fields=['status', 'cancelled_at', 'updated_at'])
        return True

    def mark_refunded(self, *, refund_id=None, refunded_amount=None):
        if self.status == 'refunded':
            return False
        if refunded_amount is None:
            refunded_amount = self.total_price
        changed = False
        if refund_id and self.stripe_refund_id != refund_id:
            self.stripe_refund_id = refund_id
            changed = True
        if self.refunded_amount != refunded_amount:
            self.refunded_amount = refunded_amount
            changed = True
        if self.status != 'refunded':
            self.status = 'refunded'
            self.refunded_at = self.refunded_at or timezone.now()
            changed = True
        if self.reverse_seller_credits():
            changed = True
        if changed:
            self.save()
        return changed


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
