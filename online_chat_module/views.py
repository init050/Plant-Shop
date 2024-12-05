from django.shortcuts import render
from django.utils.safestring import mark_safe
import json

# Create your views here.


def chatroom(request):
    return render(request, 'online_chat_module/chat.html')



def room(request, room_name):

    username = request.user.username

    context = {
        'room_name':room_name,
        'username' : mark_safe(json.dumps(username))

    }
    return render(request, 'online_chat_module/room.html', context)