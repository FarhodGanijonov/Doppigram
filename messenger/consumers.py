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
        self.user = self.scope['user']
        if not self.user or self.user.is_anonymous:
            await self.close()
            return

        self.room_group_name = f"user_{self.user.id}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # USER ULANGAN ZAHOTI TELEGRAM STYLE — CHAT LIST YUBORILADI
        chats = await self.get_user_chats()
        await self.send(text_data=json.dumps({
            "type": "chat_list",
            "chats": chats
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("action")

        # ✅ 1. Xabarlar ro'yxatini olish
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

        # ✅ 2. Chatlar ro'yxatini olish
        elif action == "fetch_chats":
            chats = await self.get_user_chats()
            await self.send(text_data=json.dumps({
                "type": "chat_list",
                "chats": chats
            }))
            return

        # ✅ 3. Yangi xabar yuborish
        text = data.get('text')
        recipient_id = data.get('recipient_id')
        media_data = data.get('media')  # client tomondan base64 formatda keladi

        if not text or not recipient_id:
            await self.send(text_data=json.dumps({"error": "Xabar yoki qabul qiluvchi ID topilmadi"}))
            return

        sender = self.user
        recipient = await self.get_user_by_id(recipient_id)  # 🆕 Bu muhim!

        chat = await self.get_or_create_chat(sender.id, recipient_id)
        # media faylni yaratish
        media_file = None
        if media_data:
            format, filestr = media_data.split(';base64,')
            ext = format.split('/')[-1]
            media_file = ContentFile(base64.b64decode(filestr), name=f"{now().timestamp()}.{ext}")

        # message yaratish
        msg = await self.create_message(chat, sender, text=text, file=media_file)

        serialized_msg = await self.serialize_message(msg)

        await self.channel_layer.group_send(
            f"user_{recipient_id}",
            {
                'type': 'new_message',
                'message': serialized_msg
            }
        )

        await self.send(text_data=json.dumps({
            "type": "new_message",
            "message": serialized_msg
        }))

        # # Qabul qiluvchiga xabar yuborish
        # await self.channel_layer.group_send(
        #     f"user_{recipient_id}",
        #     {
        #         'type': 'new_message',
        #         'chat_id': chat.id,
        #         'message': {
        #             'text': msg.text,
        #             'timestamp': msg.timestamp.isoformat(),
        #             'sender_id': sender.id,
        #             'sender_name': sender.full_name
        #         }
        #     }
        # )
        #
        # # Jo‘natuvchiga xabar yuborish
        # await self.send(text_data=json.dumps({
        #     "type": "new_message",
        #     "chat_id": chat.id,
        #     "message": {
        #         "text": msg.text,
        #         "timestamp": msg.timestamp.isoformat(),
        #         "sender_id": sender.id,
        #         "sender_name": sender.full_name
        #     }
        # }))

        # 🔁 Har ikki foydalanuvchining chat listini yangilash
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
        await self.send(text_data=json.dumps({
            "type": "new_message",
            "chat_id": event["chat_id"],
            "message": event["message"]
        }))

    async def new_chat_activity(self, event):
        await self.send(text_data=json.dumps({
            "type": "new_chat_activity",
            "chat": event["chat"]
        }))

    @database_sync_to_async
    def get_user_by_id(self, user_id):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return User.objects.get(id=user_id)

    @database_sync_to_async
    def get_or_create_chat(self, user1_id, user2_id):
        user1, user2 = sorted([user1_id, user2_id])
        chat, _ = Chat.objects.get_or_create(user1_id=user1, user2_id=user2)
        return chat

    @database_sync_to_async
    def create_message(self, chat, sender, text="", file=None):
        return Message.objects.create(chat=chat, sender=sender, text=text, file=file,  timestamp=now())

    @database_sync_to_async
    def get_chat_messages(self, chat_id):
        from .serializer import MessageSerializer
        try:
            chat = Chat.objects.get(id=chat_id)
        except Chat.DoesNotExist:
            return []
        messages = chat.messages.order_by("timestamp")
        return MessageSerializer(messages, many=True, context={"request": None}).data

    @database_sync_to_async
    def get_user_chats(self):
        from .serializer import ChatSerializer
        qs = Chat.objects.filter(Q(user1=self.user) | Q(user2=self.user))
        return ChatSerializer(qs, many=True, context={"user": self.user}).data

    @database_sync_to_async
    def serialize_chat(self, chat, user):
        from .serializer import ChatSerializer
        return ChatSerializer(chat, context={"user": user}).data

    @database_sync_to_async
    def serialize_message(self, message):
        from .serializer import MessageSerializer
        return MessageSerializer(message, context={"request": None}).data
