from django.contrib import admin
from .models import Review, SellerReview


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('product__name', 'user__email', 'comment')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)


@admin.register(SellerReview)
class SellerReviewAdmin(admin.ModelAdmin):
    list_display = ('seller', 'user', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('seller__shop_name', 'user__email', 'comment')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)