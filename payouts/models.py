from django.db import models
from sellers.models import Seller
from django.utils import timezone


class Payout(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    )

    seller = models.ForeignKey(Seller, on_delete=models.CASCADE, related_name='payouts')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=100, blank=True)
    payment_details = models.JSONField(default=dict, blank=True)
    balance_released_at = models.DateTimeField(blank=True, null=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    failed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payout {self.id} — {self.seller.shop_name} ({self.amount}$)"

    def release_reserved_balance(self):
        if self.balance_released_at:
            return False
        self.seller.balance += self.amount
        self.seller.save(update_fields=['balance', 'updated_at'])
        self.balance_released_at = timezone.now()
        return True

    def mark_processing(self):
        if self.status == 'processing':
            return False
        self.status = 'processing'
        self.save(update_fields=['status', 'updated_at'])
        return True

    def mark_completed(self):
        if self.status == 'completed':
            return False
        self.status = 'completed'
        self.processed_at = self.processed_at or timezone.now()
        self.save(update_fields=['status', 'processed_at', 'updated_at'])
        return True

    def mark_failed(self):
        self.release_reserved_balance()
        self.status = 'failed'
        self.failed_at = self.failed_at or timezone.now()
        self.save(update_fields=['status', 'failed_at', 'balance_released_at', 'updated_at'])
        return True

    def mark_cancelled(self):
        self.release_reserved_balance()
        self.status = 'cancelled'
        self.save(update_fields=['status', 'balance_released_at', 'updated_at'])
        return True
