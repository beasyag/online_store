from django.db.models import Q
from django.shortcuts import get_object_or_404

from chat.models import Conversation, Message
from sellers.models import Seller


def list_conversations_for_user(user):
    if getattr(user, 'is_seller', False):
        return Conversation.objects.filter(
            Q(buyer=user) | Q(seller=user.seller)
        ).prefetch_related('messages').order_by('-updated_at').distinct()
    return Conversation.objects.filter(
        buyer=user
    ).prefetch_related('messages').order_by('-updated_at')


def get_conversation_for_user(user, conversation_id):
    if getattr(user, 'is_seller', False):
        return get_object_or_404(
            Conversation,
            Q(id=conversation_id) & (Q(buyer=user) | Q(seller=user.seller))
        )
    return get_object_or_404(Conversation, id=conversation_id, buyer=user)


def mark_conversation_messages_read(conversation, user):
    messages_qs = conversation.messages.order_by('created_at')
    messages_qs.filter(is_read=False).exclude(sender=user).update(is_read=True)
    return messages_qs


def start_conversation_for_user(user, shop_slug):
    seller = get_object_or_404(Seller, shop_slug=shop_slug, status='verified')
    conversation, _ = Conversation.objects.get_or_create(
        buyer=user,
        seller=seller,
    )
    return conversation


def create_message_in_conversation(user, conversation_id, text):
    conversation = get_conversation_for_user(user, conversation_id)
    clean_text = (text or '').strip()
    if clean_text:
        Message.objects.create(
            conversation=conversation,
            sender=user,
            text=clean_text,
        )
        conversation.save(update_fields=['updated_at'])
    return conversation
