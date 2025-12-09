import json
import base64
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.db.models import Q
from django.utils.timezone import now
from django.core.files.base import ContentFile

from .models import Chat, Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """
        Foydalanuvchi WebSocket orqali ulanadi.
        Agar foydalanuvchi anonim bo'lsa, ulanish yopiladi.
        Agar foydalanuvchi autentifikatsiyalangan bo'lsa:
            - Kanalga qo'shiladi
            - Chat list (telegram style) avtomatik jo'natiladi
        """
        self.user = self.scope['user']
        if not self.user or self.user.is_anonymous:
            await self.close()
            return

        self.room_group_name = f"user_{self.user.id}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Ulanuvchi zahoti chat listni yuborish
        chats = await self.get_user_chats()
        await self.send(text_data=json.dumps({
            "type": "chat_list",
            "chats": chats
        }))

    async def disconnect(self, close_code):
        """
        Foydalanuvchi ulanib bo'lganidan so'ng kanalni tark etadi
        """
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        """
        WebSocket orqali kelgan xabarlarni qabul qilish va ishlash
        Text va media qo'llab-quvvatlanadi
        """
        data = json.loads(text_data)
        action = data.get("action")

        # Chat xabarlarini olish
        if action == "fetch_messages":
            chat_id = data.get("chat_id")
            if chat_id:
                messages = await self.get_chat_messages(chat_id)
                await self.send(text_data=json.dumps({
                    "type": "messages_list",
                    "chat_id": chat_id,
                    "messages": messages
                }))
            else:
                await self.send(text_data=json.dumps({"error": "chat_id kerak"}))
            return

        # Chatlar ro'yxatini olish
        elif action == "fetch_chats":
            chats = await self.get_user_chats()
            await self.send(text_data=json.dumps({
                "type": "chat_list",
                "chats": chats
            }))
            return

        # Yangi xabar yuborish (text + media)
        text = data.get('text')
        recipient_id = data.get('recipient_id')
        media_data = data.get('media')  # base64 formatda keladigan media

        if not recipient_id or (not text and not media_data):
            await self.send(text_data=json.dumps({"error": "Xabar yoki media kerak"}))
            return

        sender = self.user
        recipient = await self.get_user_by_id(recipient_id)

        # Chat mavjud bo'lmasa yaratish
        chat = await self.get_or_create_chat(sender.id, recipient_id)

        # Media faylni ContentFile orqali yaratish
        media_file = None
        if media_data:
            format, filestr = media_data.split(';base64,')
            ext = format.split('/')[-1]
            media_file = ContentFile(base64.b64decode(filestr), name=f"{now().timestamp()}.{ext}")

        # Xabar yaratish
        msg = await self.create_message(chat, sender, text=text, file=media_file)

        # Xabarni serializer orqali tayyorlash
        serialized_msg = await self.serialize_message(msg)

        # Recipientga xabarni yuborish
        await self.channel_layer.group_send(
            f"user_{recipient_id}",
            {
                'type': 'new_message',      # xabar qabul qiluvchi metod nomi
                'chat_id': chat.id,         # chat id
                'message': serialized_msg   # xabar obj
            }
        )

        # Senderga xabarni qaytarish
        await self.send(text_data=json.dumps({
            "type": "new_message",
            "chat_id": chat.id,
            "message": serialized_msg
        }))

        # Har ikki foydalanuvchi chat listini yangilash
        for uid in [sender.id, recipient.id]:
            user_obj = sender if uid == sender.id else recipient
            chat_data = await self.serialize_chat(chat, user_obj)
            await self.channel_layer.group_send(
                f"user_{uid}",
                {
                    'type': 'new_chat_activity',
                    'chat': chat_data
                }
            )

    async def new_message(self, event):
        """
        Channel orqali kelgan xabarni foydalanuvchiga yuborish
        """
        await self.send(text_data=json.dumps({
            "type": "new_message",
            "chat_id": event["chat_id"],
            "message": event["message"]
        }))

    async def new_chat_activity(self, event):
        """
        Chat list yangilanishini foydalanuvchiga yuborish
        """
        await self.send(text_data=json.dumps({
            "type": "new_chat_activity",
            "chat": event["chat"]
        }))


    #  DATABASE OPERATIONS
    @database_sync_to_async
    def get_user_by_id(self, user_id):
        """
        User id orqali user obj olish
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return User.objects.get(id=user_id)

    @database_sync_to_async
    def get_or_create_chat(self, user1_id, user2_id):
        """
        Chat mavjud bo'lmasa yaratadi
        """
        user1, user2 = sorted([user1_id, user2_id])
        chat, _ = Chat.objects.get_or_create(user1_id=user1, user2_id=user2)
        return chat

    @database_sync_to_async
    def create_message(self, chat, sender, text="", file=None):
        """
        Message yaratish funksiyasi
        text va file (media) qo'llab-quvvatlanadi
        """
        return Message.objects.create(chat=chat, sender=sender, text=text, file=file,  timestamp=now())

    @database_sync_to_async
    def get_chat_messages(self, chat_id):
        """
        Berilgan chat_id ga oid barcha xabarlarni olish
        """
        from .serializer import MessageSerializer
        try:
            chat = Chat.objects.get(id=chat_id)
        except Chat.DoesNotExist:
            return []
        messages = chat.messages.order_by("timestamp")
        return MessageSerializer(messages, many=True, context={"request": None}).data

    @database_sync_to_async
    def get_user_chats(self):
        """
        Foydalanuvchiga tegishli chatlar ro'yxatini olish
        """
        from .serializer import ChatSerializer
        qs = Chat.objects.filter(Q(user1=self.user) | Q(user2=self.user))
        return ChatSerializer(qs, many=True, context={"user": self.user}).data

    @database_sync_to_async
    def serialize_chat(self, chat, user):
        """
        Chat objni serializer orqali JSON formatga o'tkazish
        """
        from .serializer import ChatSerializer
        return ChatSerializer(chat, context={"user": user}).data

    @database_sync_to_async
    def serialize_message(self, message):
        """
        Message objni serializer orqali JSON formatga o'tkazish
        """
        from .serializer import MessageSerializer
        return MessageSerializer(message, context={"request": None}).data
