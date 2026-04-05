from django.db import models
from django.conf import settings
from django.utils.text import slugify


class Seller(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),      # ожидает модерации
        ('verified', 'Verified'),    # одобрен
        ('rejected', 'Rejected'),    # отклонён
        ('suspended', 'Suspended'),  # заблокирован
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='seller'
    )
    shop_name = models.CharField(max_length=100)
    shop_slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='sellers/logos/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.shop_slug:
            base_slug = slugify(self.shop_name)
            slug = base_slug
            counter = 1
            while Seller.objects.filter(shop_slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.shop_slug = slug
        super().save(*args, **kwargs)
        if self.user.role != 'admin' and self.user.role != 'seller':
            self.user.role = 'seller'
            self.user.save(update_fields=['role'])

    def delete(self, *args, **kwargs):
        user = self.user
        super().delete(*args, **kwargs)
        if user.role == 'seller':
            user.role = 'buyer'
            user.save(update_fields=['role'])

    @property
    def is_verified(self):
        return self.status == 'verified'

    @property
    def can_access_dashboard(self):
        return True

    @property
    def can_manage_products(self):
        return self.is_verified

    def __str__(self):
        return self.shop_name
