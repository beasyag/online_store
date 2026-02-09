from django.contrib import admin
from .models import Category, ProductSize, \
    ProductImage, Product, Size

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class ProductSizeInline(admin.TabularInline):
    model = ProductSize
    extra = 1

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'color')
    list_filter = ('category', 'color')
    search_fields = ('name', 'color', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductSizeInline, ProductImageInline]

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

class SizeAdmin(admin.ModelAdmin):
    list_display = ['name']

admin.site.register(Product, ProductAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Size, SizeAdmin)
# Register your models here.
