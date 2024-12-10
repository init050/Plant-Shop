import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer 
from .serializers import MessaageSerializers
from .models import Message
from rest_framework.renderers import JSONRenderer
from django.contrib.auth import get_user_model






class ChatConsumer(WebsocketConsumer):


    def new_message(self, data):
        pass



    def fetch_message(self, data):
        pass



    def message_serializers(self, qs):
        pass



    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        async_to_sync(self.channel_layer.group.add)(
            self.room_group_name, self.channel_name
        )

    
    commands = {
        'new_message':new_message,
        'fetch_message':fetch_message,
    }



    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group.discard){
            self.room_group_name , self.channel_layer
        }

    
    def receive(self, text_data):
        text_data_json = json.load[text_data]
        
        


    def send_to_chat_message(self, message):
        pass



    def chat_message(self, event):
        pass