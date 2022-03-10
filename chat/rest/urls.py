from django.urls import path
from chat.rest import views

app_name = 'chat'

urlpatterns = [
    path('chats/list', views.ChatListView.as_view(), name='chat-list'),
    path('chats/<int:pk>/messages', views.MessageListView.as_view(), name='message-list'),
    path('notifications', views.NotificationsListView.as_view(), name='notifications-list')
]
