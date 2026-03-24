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
                'price', 'color', 'size_kind', 'description', 'main_image',
            )
        }),
    )


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [SubcategoryInline]


class SizeAdmin(admin.ModelAdmin):
    list_display = ['name']


class HeroVideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'created_at')
    list_filter = ('is_active',)


admin.site.register(HeroVideo, HeroVideoAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Size, SizeAdmin)
