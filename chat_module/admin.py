from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from .models import ChatRoom, ChatMessage


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'user', 'get_user_email', 'is_active', 
        'message_count', 'last_activity', 'created_at'
    ]
    list_filter = ['is_active', 'created_at', 'last_activity']
    search_fields = ['title', 'user__email', 'user__username']
    readonly_fields = ['created_at', 'last_activity']
    raw_id_fields = ['user']
    
    fieldsets = (
        (None, {
            'fields': ('user', 'title', 'is_active')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'last_activity'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['activate_rooms', 'deactivate_rooms']
    
    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = _('User Email')
    
    def message_count(self, obj):
        count = obj.messages.count()
        if count > 0:
            url = reverse('admin:chat_module_chatmessage_changelist')
            return format_html(
                '<a href="{}?room__id__exact={}">{} messages</a>',
                url, obj.id, count
            )
        return '0 messages'
    message_count.short_description = _('Messages')
    
    def activate_rooms(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} rooms activated.')
    activate_rooms.short_description = _('Activate selected rooms')
    
    def deactivate_rooms(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} rooms deactivated.')
    deactivate_rooms.short_description = _('Deactivate selected rooms')


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = [
        'get_message_preview', 'author', 'get_author_type', 
        'room', 'is_read', 'created_at'
    ]
    list_filter = ['is_read', 'created_at', 'author__is_staff']
    search_fields = ['content', 'author__email', 'room__title']
    readonly_fields = ['created_at']
    raw_id_fields = ['room', 'author']
    
    fieldsets = (
        (None, {
            'fields': ('room', 'author', 'content')
        }),
        (_('Status'), {
            'fields': ('is_read',)
        }),
        (_('Timestamp'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def get_message_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    get_message_preview.short_description = _('Message')
    
    def get_author_type(self, obj):
        if obj.author.is_staff:
            return format_html('<span style="color: green;">Admin</span>')
        return format_html('<span style="color: blue;">User</span>')
    get_author_type.short_description = _('Author Type')
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} messages marked as read.')
    mark_as_read.short_description = _('Mark selected messages as read')
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} messages marked as unread.')
    mark_as_unread.short_description = _('Mark selected messages as unread')