from django.shortcuts import render

# Create your views here.


def chatroom(request):
    return render(request, 'online_chat_module/chat.html')



def room(request, room_name):
    return render(request, 'online_chat_module/room.html', {'room_name':room_name})