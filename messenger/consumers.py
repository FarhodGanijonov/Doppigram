import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Chat, Message
from django.utils.timezone import now

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']

        # ❌ Token yo‘q yoki noto‘g‘ri bo‘lsa ulanishni to‘xtatamiz
        if not self.user or self.user.is_anonymous:
            await self.close()
            return

        # Har bir foydalanuvchi uchun alohida kanal nomi
        self.room_group_name = f"user_{self.user.id}"

        # Guruhga qo‘shamiz
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        text = data.get('text')
        recipient_id = data.get('recipient_id')  # qaysi userga jonatilyapti

        if not text or not recipient_id:
            await self.send(text_data=json.dumps({"error": "Xabar yoki qabul qiluvchi ID topilmadi"}))
            return

        sender = self.user

        # Chat topiladi yoki yaratilib ketadi
        chat = await self.get_or_create_chat(sender.id, recipient_id)

        # Xabar bazaga yoziladi
        msg = await self.create_message(chat, sender, text)

        # Qabul qiluvchiga jonatiladi
        await self.channel_layer.group_send(
            f"user_{recipient_id}",
            {
                'type': 'chat_message',
                'message': msg.text,
                'sender_id': sender.id,
                'sender_name': sender.full_name,
                'timestamp': msg.timestamp.isoformat()
            }
        )

        # Jo‘natuvchiga ham qaytadi
        await self.send(text_data=json.dumps({
            "message": msg.text,
            "sender_id": sender.id,
            "timestamp": msg.timestamp.isoformat()
        }))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def get_or_create_chat(self, user1_id, user2_id):
        user1, user2 = sorted([user1_id, user2_id])
        chat, created = Chat.objects.get_or_create(user1_id=user1, user2_id=user2)
        return chat

    @database_sync_to_async
    def create_message(self, chat, sender, text):
        return Message.objects.create(chat=chat, sender=sender, text=text, timestamp=now())
