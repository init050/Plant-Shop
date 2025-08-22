from django.urls import path
from . import views

app_name = 'chat_module'

urlpatterns = [
    path('', views.user_chat_room, name='user_chat'),
    path('notifications/', views.chat_notifications, name='notifications'),
    path('mark-read/', views.mark_messages_read, name='mark_read'),
    
    path('admin/', views.admin_chat_list, name='admin_list'),
    path('admin/room/<int:room_id>/', views.admin_chat_room, name='admin_room'),
]