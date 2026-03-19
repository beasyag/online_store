from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.template.response import TemplateResponse
from django.http import JsonResponse
from .models import Conversation, Message
from sellers.models import Seller


@login_required(login_url='/users/login')
def conversation_list(request):
    conversations = Conversation.objects.filter(
        buyer=request.user
    ).prefetch_related('messages').order_by('-updated_at')
    return TemplateResponse(request, 'chat/list.html', {'conversations': conversations})


@login_required(login_url='/users/login')
def conversation_detail(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id, buyer=request.user)
    messages_qs = conversation.messages.order_by('created_at')
    messages_qs.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
    return TemplateResponse(request, 'chat/detail.html', {
        'conversation': conversation,
        'messages': messages_qs,
    })


@login_required(login_url='/users/login')
def start_conversation(request, shop_slug):
    seller = get_object_or_404(Seller, shop_slug=shop_slug, status='verified')
    conversation, created = Conversation.objects.get_or_create(
        buyer=request.user,
        seller=seller,
    )
    return redirect('chat:detail', conversation_id=conversation.id)


@login_required(login_url='/users/login')
def send_message(request, conversation_id):
    if request.method == 'POST':
        conversation = get_object_or_404(Conversation, id=conversation_id, buyer=request.user)
        text = request.POST.get('text', '').strip()
        if text:
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                text=text,
            )
            conversation.save()  # обновляет updated_at
    return redirect('chat:detail', conversation_id=conversation_id)