from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator
from django.db.models import Q, Count
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json

from .models import ChatRoom, ChatMessage
from .forms import ChatMessageForm, AdminChatMessageForm


@login_required
def user_chat_room(request):
    room, created = ChatRoom.objects.get_or_create_room(request.user)

    if request.method == 'POST':
        form = ChatMessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.room = room
            message.author = request.user
            message.save()

            # Broadcast the new message to the channel layer
            # so it can be picked up by the WebSocket consumer.
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'chat_room_{room.id}',
                {
                    'type': 'chat_message',
                    'message': message.content,
                    'author_email': message.author.email,
                    'author_avatar': message.author.avatar.url if message.author.avatar else '',
                    'created_at': message.created_at.strftime('%H:%M'),
                    'is_staff': message.author.is_staff,
                }
            )

            room.messages.filter(
                author__is_staff=True,
                is_read=False
            ).update(is_read=True)

            return redirect('chat_module:user_chat')
    else:
        form = ChatMessageForm()

    messages_list = room.messages.select_related('author').order_by('created_at')
    paginator = Paginator(messages_list, 50)
    page_number = request.GET.get('page', paginator.num_pages)
    messages_page = paginator.get_page(page_number)

    context = {
        'room': room,
        'messages': messages_page,
        'form': form,
        'room_id': room.id,
    }
    return render(request, 'chat_module/user_chat.html', context)


@staff_member_required
def admin_chat_list(request):
    '''List of all chat rooms for admin.'''
    search_query = request.GET.get('search', '')
    rooms = ChatRoom.objects.active_rooms().select_related('user')

    if search_query:
        rooms = rooms.filter(
            Q(user__email__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(title__icontains=search_query)
        )

    rooms = rooms.annotate(
        unread_count=Count(
            'messages',
            filter=Q(
                messages__author__is_staff=False,
                messages__is_read=False
            )
        )
    )

    paginator = Paginator(rooms, 20)
    page_number = request.GET.get('page')
    rooms_page = paginator.get_page(page_number)

    context = {
        'rooms': rooms_page,
        'search_query': search_query,
    }
    return render(request, 'chat_module/admin_chat_list.html', context)


@staff_member_required
def admin_chat_room(request, room_id):
    '''Admin interface for a specific chat room.'''
    room = get_object_or_404(ChatRoom, id=room_id)

    if request.method == 'POST':
        form = AdminChatMessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.room = room
            message.author = request.user
            message.save()

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'chat_room_{room.id}',
                {
                    'type': 'chat_message',
                    'message': message.content,
                    'author_email': message.author.email,
                    'author_avatar': message.author.avatar.url if message.author.avatar else '',
                    'created_at': message.created_at.strftime('%H:%M'),
                    'is_staff': message.author.is_staff,
                }
            )

            return redirect('chat_module:admin_room', room_id=room.id)
    else:
        form = AdminChatMessageForm()

    # Mark messages from the user as read upon admin opening the chat.
    room.messages.filter(
        author__is_staff=False,
        is_read=False
    ).update(is_read=True)

    messages_list = room.messages.select_related('author').order_by('created_at')
    paginator = Paginator(messages_list, 50)
    page_number = request.GET.get('page', paginator.num_pages)
    messages_page = paginator.get_page(page_number)

    context = {
        'room': room,
        'messages': messages_page,
        'form': form,
        'room_id': room.id,
    }
    return render(request, 'chat_module/admin_chat_room.html', context)


@require_POST
@csrf_exempt
def mark_messages_read(request):
    '''AJAX endpoint to mark messages as read.'''
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Not authenticated'})

    try:
        data = json.loads(request.body)
        room_id = data.get('room_id')

        # Based on the user type, mark the other party's messages as read.
        if request.user.is_staff:
            ChatMessage.objects.filter(
                room_id=room_id,
                author__is_staff=False,
                is_read=False
            ).update(is_read=True)
        else:
            ChatMessage.objects.filter(
                room_id=room_id,
                author__is_staff=True,
                is_read=False
            ).update(is_read=True)

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def chat_notifications(request):
    '''Get unread message count for notifications.'''
    if request.user.is_staff:
        # For staff, count all unread messages from users.
        unread_count = ChatMessage.objects.filter(
            author__is_staff=False,
            is_read=False
        ).count()
    else:
        # For regular users, count unread messages in their specific room.
        try:
            room = request.user.chat_room
            unread_count = room.unread_count_for_user
        except ChatRoom.DoesNotExist:
            unread_count = 0

    return JsonResponse({
        'unread_count': unread_count
    })