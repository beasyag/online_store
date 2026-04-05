from django.contrib import admin
from .models import Category, ProductSize, \
    ProductImage, Product, Size, HeroVideo, Subcategory


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class ProductSizeInline(admin.TabularInline):
    model = ProductSize
    extra = 1

class SubcategoryInline(admin.TabularInline):
    model = Subcategory
    extra = 2
    prepopulated_fields = {'slug': ('name',)}

class ProductTypeAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'has_sizes', 'has_shoe_sizes', 'has_color',
        'has_material', 'has_fragrance_notes', 'has_metal_type',
        'has_volume', 'has_weight'
    )
    prepopulated_fields = {'slug': ('name',)}

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'color')
    list_filter = ('category', 'color')
    search_fields = ('name', 'color', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductSizeInline, ProductImageInline]
    fieldsets = (
        (None, {
            'fields': (
                'seller', 'name', 'slug', 'category', 'subcategory',
                'size_kind', 'price', 'color', 'description', 'main_image',
            )
        }),
    )


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [SubcategoryInline]

class SizeAdmin(admin.ModelAdmin):
    list_display = ['name', 'kind']
    list_filter = ['kind']


class HeroVideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'created_at')
    list_filter = ('is_active',)

admin.site.register(HeroVideo, HeroVideoAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Size, SizeAdmin)
# Register your models here.
