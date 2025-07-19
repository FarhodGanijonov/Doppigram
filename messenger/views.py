from django.db import models
from rest_framework import generics, permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Chat
from .serializer import ChatSerializer, MessageSerializer
from django.db.models import Q

class ChatListView(generics.ListAPIView):
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Chat.objects.filter(Q(user1=user) | Q(user2=user))


class ChatCreateView(generics.CreateAPIView):
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user1 = self.request.user
        user2_id = self.request.data.get('user2')

        # oldindan tekshir: chat mavjud bo‘lsa, uni qaytar
        chat, created = Chat.objects.get_or_create(
            user1=min(user1.id, int(user2_id)),
            user2=max(user1.id, int(user2_id))
        )
        self.chat_instance = chat  # bu optional — keyin serializerga berish mumkin

    def create(self, request, *args, **kwargs):
        user1 = self.request.user
        user2_id = self.request.data.get('user2')

        chat, created = Chat.objects.get_or_create(
            user1_id=min(user1.id, int(user2_id)),
            user2_id=max(user1.id, int(user2_id))
        )
        serializer = self.get_serializer(chat)
        return Response(serializer.data)


class MessageListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_id = request.query_params.get("user_id", None)
        if not user_id:
            return Response({"error": "user_id kerak"}, status=400)

        try:
            chat = Chat.objects.get(
                (models.Q(user1=request.user, user2_id=user_id) |
                 models.Q(user1_id=user_id, user2=request.user))
            )
        except Chat.DoesNotExist:
            return Response({"error": "Chat mavjud emas"}, status=404)

        messages = chat.messages.order_by("timestamp")
        serializer = MessageSerializer(messages, many=True, context={'request': request})
        return Response(serializer.data)


# class UploadMessageView(APIView):
#     permission_classes = [IsAuthenticated]
#     parser_classes = [MultiPartParser, FormParser]
#
#     def post(self, request, *args, **kwargs):
#         serializer = MessageUploadSerializer(data=request.data)
#         if serializer.is_valid():
#             msg = serializer.save(sender=request.user)
#             return Response({
#                 "message_id": msg.id,
#                 "chat": msg.chat.id,
#                 "file_url": msg.file.url,
#                 "timestamp": msg.timestamp.isoformat()
#             })
#         return Response(serializer.errors, status=400)
