import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import ChatRoom, ChatMessage

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_room_{self.room_id}'
        self.user = self.scope['user']

        if not await self.user_can_access_room():
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        '''
        Handles messages received from the WebSocket.
        It can process two types of messages: 'message' for chat content
        and 'typing' for sending typing indicators.
        '''
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type', 'message')

            if message_type == 'message':
                message = text_data_json.get('message', '')
                if message.strip():
                    chat_message = await self.save_message(message)

                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'chat_message',
                            'message': message,
                            'author_email': self.user.email,
                            'author_avatar': self.user.avatar.url if hasattr(self.user, 'avatar') and self.user.avatar else '',
                            'created_at': chat_message.created_at.strftime('%H:%M'),
                            'is_staff': self.user.is_staff,
                        }
                    )

            elif message_type == 'typing':
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'typing_indicator',
                        'user_email': self.user.email,
                        'is_typing': text_data_json.get('is_typing', False),
                    }
                )

        except json.JSONDecodeError:
            # Ignore messages that are not valid JSON
            pass

    async def chat_message(self, event):
        '''Sends a chat message to the WebSocket.'''
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message'],
            'author_email': event['author_email'],
            'author_avatar': event['author_avatar'],
            'created_at': event['created_at'],
            'is_staff': event['is_staff'],
        }))

    async def typing_indicator(self, event):
        '''Sends a typing indicator to the WebSocket.'''
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'user_email': event['user_email'],
            'is_typing': event['is_typing'],
        }))

    @database_sync_to_async
    def user_can_access_room(self):
        '''
        Checks if the current user has permission to access the chat room.
        A user can access if they are the room's owner or a staff member.
        '''
        try:
            room = ChatRoom.objects.get(id=self.room_id)
            return room.user == self.user or self.user.is_staff
        except ChatRoom.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, content):
        '''
        Saves a new chat message to the database.
        This is run in a sync-to-async wrapper because it performs DB operations.
        '''
        room = ChatRoom.objects.get(id=self.room_id)
        message = ChatMessage.objects.create(
            room=room,
            author=self.user,
            content=content
        )
        return message