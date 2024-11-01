from django.urls import path
from  . import views

urlpatterns = [
    path('', views.chatroom , name='chat')
]
