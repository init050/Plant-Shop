from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.urls import reverse


class ChatRoomManager(models.Manager):
    def get_or_create_room(self, user):
        """Get existing room or create new one for user"""
        room, created = self.get_or_create(
            user=user,
            defaults={'title': f'Support - {user.email}'}
        )
        return room, created
    
    def active_rooms(self):
        """Get rooms with recent activity"""
        return self.filter(is_active=True).order_by('-last_activity')


class ChatRoom(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_('User'),
        related_name='chat_room'
    )
    title = models.CharField(_('Title'), max_length=200)
    is_active = models.BooleanField(_('Is Active'), default=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    last_activity = models.DateTimeField(_('Last Activity'), auto_now=True)
    
    objects = ChatRoomManager()
    
    class Meta:
        verbose_name = _('Chat Room')
        verbose_name_plural = _('Chat Rooms')
        ordering = ['-last_activity']
    
    def __str__(self):
        return f'{self.title}'
    
    def get_absolute_url(self):
        return reverse('chat_module:room_detail', kwargs={'pk': self.pk})
    
    @property
    def unread_count_for_user(self):
        return self.messages.filter(
            author__is_staff=True,
            is_read=False
        ).count()
    
    @property  
    def unread_count_for_admin(self):
        return self.messages.filter(
            author__is_staff=False,
            is_read=False
        ).count()


class ChatMessage(models.Model):
    room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_('Room')
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_('Author')
    )
    content = models.TextField(_('Content'))
    is_read = models.BooleanField(_('Is Read'), default=False)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Chat Message')
        verbose_name_plural = _('Chat Messages')
        ordering = ['created_at']
    
    def __str__(self):
        return f'{self.author.email}: {self.content[:50]}'
    
    def save(self, *args, **kwargs):
        # Update room's last activity when new message is created
        super().save(*args, **kwargs)
        ChatRoom.objects.filter(pk=self.room.pk).update(
            last_activity=self.created_at
        )