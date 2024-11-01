from django.shortcuts import render

# Create your views here.


def chatroom(request):
    return render(request, 'online_chat_module/chat.html')