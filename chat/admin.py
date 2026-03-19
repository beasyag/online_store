from django.contrib import admin
from .models import Conversation, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('sender', 'text', 'is_read', 'created_at')
    can_delete = False


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('buyer', 'seller', 'message_count', 'created_at', 'updated_at')
    search_fields = ('buyer__email', 'seller__shop_name')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [MessageInline]

    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = 'Messages'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'sender', 'short_text', 'is_read', 'created_at')
    list_filter = ('is_read',)
    search_fields = ('sender__email', 'text')
    readonly_fields = ('created_at',)

    def short_text(self, obj):
        return obj.text[:50]
    short_text.short_description = 'Text'