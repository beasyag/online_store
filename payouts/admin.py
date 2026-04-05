from django.contrib import admin
from .models import Payout


@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = ('id', 'seller', 'amount', 'status', 'payment_method', 'created_at')
    list_filter = ('status',)
    search_fields = ('seller__shop_name', 'seller__user__email')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)

    actions = ['mark_completed', 'mark_processing', 'mark_failed']

    def mark_completed(self, request, queryset):
        for payout in queryset:
            payout.mark_completed()
        self.message_user(request, f'{queryset.count()} payout(s) marked as completed.')
    mark_completed.short_description = 'Mark as completed'

    def mark_processing(self, request, queryset):
        for payout in queryset:
            payout.mark_processing()
        self.message_user(request, f'{queryset.count()} payout(s) marked as processing.')
    mark_processing.short_description = 'Mark as processing'

    def mark_failed(self, request, queryset):
        for payout in queryset:
            payout.mark_failed()
        self.message_user(request, f'{queryset.count()} payout(s) marked as failed.')
    mark_failed.short_description = 'Mark as failed'
