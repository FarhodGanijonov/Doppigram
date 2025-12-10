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
        WebSocketga ulanish.
        1) Userni sessiondan olish
        2) Anon user bo'lsa - ulanishni yopish
        3) Userga xos group yaratish (user_12)
        4) Ulanishni qabul qilish
        5) Ulangan paytda userning chatlar ro'yxatini qaytarish
        """
        self.user = self.scope['user']
        if not self.user or self.user.is_anonymous:
            await self.close()
            return

        # Har bir user uchun alohida kanal group (xabar yuborish shuning orqali)
        self.room_group_name = f"user_{self.user.id}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Ulanuvchi userga chatlar ro'yxatini qaytarish
        chats = await self.get_user_chats()
        await self.send(text_data=json.dumps({
            "type": "chat_list",
            "chats": chats
        }))

    async def disconnect(self, close_code):
        """
        WebSocket uzilganda user kanal gruppasidan chiqariladi.
        """
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        """
        Frontenddan kelgan xabarlarni qabul qilish.
        Action'ga qarab turli vazifalar bajariladi:
        - fetch_messages: chatning barcha message'larini olish
        - fetch_chats: foydalanuvchiga tegishli chatlarni olish
        - Yangi xabar yuborish
        """
        data = json.loads(text_data)
        action = data.get("action")

        if action == "fetch_messages":
            """
            Frontdan chat_id kelsa, shu chatning barcha xabarlarini backenddan olib yuboramiz.
            """
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

        elif action == "fetch_chats":
            """
            Foydalanuvchiga tegishli chatlar ro'yxatini qaytarish.
            """
            chats = await self.get_user_chats()
            await self.send(text_data=json.dumps({
                "type": "chat_list",
                "chats": chats
            }))
            return

        # Xabar yuborish uchun umumiy qism
        recipient_id = data.get("recipient_id")
        message_type = data.get("type", "text")  # text/photo/audio/video
        text = data.get("text")
        media_data = data.get("media")  # base64 encoded file
        duration = data.get("duration")  # audio length
        waveform = data.get("waveform")  # audio visualization

        # Xabarni tekshirish: matn yoki media bo'lishi shart
        if not recipient_id or (not text and not media_data):
            await self.send(text_data=json.dumps({"error": "Xabar yoki media bo'lishi kerak"}))
            return

        sender = self.user
        recipient = await self.get_user_by_id(recipient_id)

        # Chat yaratish yoki mavjudini olish
        chat = await self.get_or_create_chat(sender.id, recipient_id)

        """
        media_data: 'data:image/png;base64,....'
        Uni base64 dan faylga o'giramiz va Message modelga saqlaymiz.
        """
        media_file = None
        if media_data:
            header, b64 = media_data.split(";base64,")
            ext = header.split("/")[-1]
            media_file = ContentFile(base64.b64decode(b64), name=f"{now().timestamp()}.{ext}")

        msg = await self.create_message(
            chat=chat,
            sender=sender,
            message_type=message_type,
            text=text or "",
            file=media_file,
            duration=duration,
            waveform=waveform
        )

        serialized_msg = await self.serialize_message(msg)

        # Recipientga yuborish (group_send)
        """
        Boshqa userga real-time xabar yuborish.
        Ular `new_message` methodi orqali qabul qiladi.
        """
        await self.channel_layer.group_send(
            f"user_{recipient_id}",
            {
                'type': 'new_message',
                'chat_id': chat.id,
                'message': serialized_msg
            }
        )

        await self.send(text_data=json.dumps({
            "type": "new_message",
            "chat_id": chat.id,
            "message": serialized_msg
        }))

    # EVENT HANDLER
    async def new_message(self, event):
        """
        group_send orqali yuborilgan xabarlarni qabul qiluvchi method.
        Bu method avtomatik chaqiriladi.
        """
        await self.send(text_data=json.dumps({
            "type": "new_message",
            "chat_id": event["chat_id"],
            "message": event["message"]
        }))

    # DB METHODS

    @database_sync_to_async
    def get_user_by_id(self, user_id):
        """
        User ID orqali userni olish (sync -> async).
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return User.objects.get(id=user_id)

    @database_sync_to_async
    def get_or_create_chat(self, user1_id, user2_id):
        """
        Ikki user o'rtasidagi chatni olish yoki yaratish.
        Chat har doim user ID bo'yicha sort qilinadi (tartib muhim).
        """
        user1, user2 = sorted([user1_id, user2_id])
        chat, _ = Chat.objects.get_or_create(user1_id=user1, user2_id=user2)
        return chat

    @database_sync_to_async
    def create_message(self, chat, sender, message_type, text="", file=None, duration=None, waveform=None):
        """
        Yangi xabar yaratish.
        Xabar turi (text, image, audio, video) avtomatik ishlaydi.
        """
        return Message.objects.create(
            chat=chat,
            sender=sender,
            type=message_type,
            text=text,
            file=file,
            duration=duration,
            waveform=waveform,
            timestamp=now()
        )

    @database_sync_to_async
    def get_chat_messages(self, chat_id):
        """
        Chatdagi barcha xabarlarni olish va serializer orqali formatlash.
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
        Userga tegishli barcha chatlarni olish.
        user1=user yoki user2=user bo’lsa - chat ro’yxatga qo’shiladi.
        """
        from .serializer import ChatSerializer
        qs = Chat.objects.filter(Q(user1=self.user) | Q(user2=self.user))
        return ChatSerializer(qs, many=True, context={"user": self.user}).data

    @database_sync_to_async
    def serialize_message(self, message):
        """
        Message modelini JSON ko'rinishiga o'tkazish.
        """
        from .serializer import MessageSerializer
        return MessageSerializer(message, context={"request": None}).data
