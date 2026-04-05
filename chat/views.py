from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.template.response import TemplateResponse
from django.http import JsonResponse
from .services import (
    create_message_in_conversation,
    get_conversation_for_user,
    list_conversations_for_user,
    mark_conversation_messages_read,
    start_conversation_for_user,
)


@login_required(login_url='/users/login')
def conversation_list(request):
    conversations = list_conversations_for_user(request.user)
    return TemplateResponse(request, 'chat/list.html', {'conversations': conversations})


@login_required(login_url='/users/login')
def conversation_detail(request, conversation_id):
    conversation = get_conversation_for_user(request.user, conversation_id)
    messages_qs = mark_conversation_messages_read(conversation, request.user)
    return TemplateResponse(request, 'chat/detail.html', {
        'conversation': conversation,
        'messages': messages_qs,
    })


@login_required(login_url='/users/login')
def start_conversation(request, shop_slug):
    conversation = start_conversation_for_user(request.user, shop_slug)
    return redirect('chat:detail', conversation_id=conversation.id)


@login_required(login_url='/users/login')
def send_message(request, conversation_id):
    if request.method == 'POST':
        create_message_in_conversation(request.user, conversation_id, request.POST.get('text', ''))
    return redirect('chat:detail', conversation_id=conversation_id)
