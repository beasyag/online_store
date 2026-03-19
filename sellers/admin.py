from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Seller


@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    list_display = ('shop_name', 'user', 'status', 'commission_rate', 'balance', 'created_at')
    list_filter = ('status',)
    search_fields = ('shop_name', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'logo_preview')
    ordering = ('-created_at',)

    fieldsets = (
        ('Shop Info', {
            'fields': ('user', 'shop_name', 'shop_slug', 'description', 'logo', 'logo_preview')
        }),
        ('Status & Finance', {
            'fields': ('status', 'commission_rate', 'balance')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def logo_preview(self, obj):
        if obj.logo:
            return mark_safe(f"<img src='{obj.logo.url}' style='max-height: 100px; max-width: 100px; object-fit: cover;' />")
        return mark_safe('<span style="color:gray;">No logo</span>')
    logo_preview.short_description = 'Logo Preview'

    # ← кнопки быстрого одобрения/отклонения
    actions = ['verify_sellers', 'reject_sellers', 'suspend_sellers']

    def verify_sellers(self, request, queryset):
        queryset.update(status='verified')
        self.message_user(request, f'{queryset.count()} seller(s) verified.')
    verify_sellers.short_description = 'Verify selected sellers'

    def reject_sellers(self, request, queryset):
        queryset.update(status='rejected')
        self.message_user(request, f'{queryset.count()} seller(s) rejected.')
    reject_sellers.short_description = 'Reject selected sellers'

    def suspend_sellers(self, request, queryset):
        queryset.update(status='suspended')
        self.message_user(request, f'{queryset.count()} seller(s) suspended.')
    suspend_sellers.short_description = 'Suspend selected sellers'