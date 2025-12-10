# chat/urls.py
from django.urls import path
from .views import ChatListView, ChatCreateView, MessageListView

urlpatterns = [
    path('chats/', ChatListView.as_view(), name='chat-list'),
    path('chatsa/create/', ChatCreateView.as_view(), name='chat-create'),
    path('messages/', MessageListView.as_view(), name='message-list'),
    # path('messages/upload/', UploadMessageView.as_view(), name='message-upload'),

]
