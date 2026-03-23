from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProductType(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)

    # какие атрибуты показывать для этого типа
    has_sizes = models.BooleanField(default=False)
    has_shoe_sizes = models.BooleanField(default=False)
    has_color = models.BooleanField(default=True)
    has_material = models.BooleanField(default=False)
    has_fragrance_notes = models.BooleanField(default=False)  # для парфюмерии
    has_metal_type = models.BooleanField(default=False)       # для украшений
    has_volume = models.BooleanField(default=False)           # для парфюмерии (мл)
    has_weight = models.BooleanField(default=False)           # для украшений (г)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Size(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name

class Subcategory(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='subcategories'
    )
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Subcategory.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.category.name} → {self.name}"

class Product(models.Model):
    seller = models.ForeignKey(
        'sellers.Seller',
        on_delete=models.CASCADE,
        related_name='products',
        null=True,
        blank=True
    )
    subcategory = models.ForeignKey(
        'Subcategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )
    product_type = models.ForeignKey(
        ProductType,
        on_delete=models.PROTECT,
        related_name='products',
        null=True,
        blank=True
    )
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products'
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    main_image = models.ImageField(upload_to='products/main/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # общие атрибуты
    color = models.CharField(max_length=100, blank=True)
    material = models.CharField(max_length=100, blank=True)

    # Обувь
    shoe_size = models.CharField(max_length=20, blank=True)

    # Парфюмерия
    fragrance_top_notes = models.CharField(max_length=255, blank=True)
    fragrance_heart_notes = models.CharField(max_length=255, blank=True)
    fragrance_base_notes = models.CharField(max_length=255, blank=True)
    volume_ml = models.PositiveIntegerField(null=True, blank=True)

    # Украшения
    METAL_CHOICES = (
        ('gold', 'Gold'),
        ('silver', 'Silver'),
        ('platinum', 'Platinum'),
        ('rose_gold', 'Rose Gold'),
    )
    metal_type = models.CharField(
        max_length=20,
        choices=METAL_CHOICES,
        blank=True
    )
    metal_purity = models.CharField(max_length=10, blank=True)  # 585, 750, 925
    gemstone = models.CharField(max_length=100, blank=True)
    weight_g = models.DecimalField(
        max_digits=6, decimal_places=2,
        null=True, blank=True
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProductSize(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='product_sizes'
    )
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    stock = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('product', 'size')

    def __str__(self):
        return f"{self.size.name} ({self.stock} in stock) for {self.product.name}"


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='products/extra/')

    def __str__(self):
        return f"Image for {self.product.name}"


class HeroVideo(models.Model):
    title = models.CharField(max_length=100, blank=True)
    video = models.FileField(upload_to='hero/')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Hero Video'
        verbose_name_plural = 'Hero Videos'

    def __str__(self):
        return self.title or f"Hero Video {self.id}"