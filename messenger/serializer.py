from rest_framework import serializers

from users.models import AbstractUser
from .models import Message, Chat


class ChatSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ['id', 'user', 'last_message', 'created_at']

    def get_user(self, obj):
        context_user = self.context.get('user') or self.context.get('request', {}).user

        if not context_user or not hasattr(context_user, "id"):
            return None

        other_user = obj.user2 if obj.user1 == context_user else obj.user1
        return {
            "id": other_user.id,
            "full_name": other_user.full_name,
            "avatar": other_user.avatar.url if other_user.avatar else None
        }

    def get_last_message(self, obj):
        if not hasattr(obj, "messages"):
            return None
        last_msg = obj.messages.order_by('-timestamp').first()
        if last_msg:
            return {
                'text': last_msg.text,
                'timestamp': last_msg.timestamp.isoformat(),
                'sender_id': last_msg.sender.id,
                'is_read': last_msg.is_read
            }
        return None


class UserShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = AbstractUser
        fields = ['id', 'full_name', 'avatar']



class MessageSerializer(serializers.ModelSerializer):
    sender = UserShortSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'chat', 'sender', 'text', 'file', 'timestamp', 'is_read']


# Faqat `sender` ning ismi bilan — soddalashtirilgan
class MessageSimpleSerializer(serializers.ModelSerializer):
    sender_full_name = serializers.CharField(source='sender.full_name', read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'chat', 'sender', 'sender_full_name', 'text', 'timestamp', 'is_read']


# class MessageUploadSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Message
#         fields = ['chat', 'file']
#
#     def validate_file(self, file):
#         # 🔒 Cheklovlar: ruxsat etilgan turlar va hajm
#         max_size = 10 * 1024 * 1024  # 10MB
#         allowed_types = ['image/jpeg', 'image/png', 'video/mp4', 'application/pdf']
#
#         if file.size > max_size:
#             raise serializers.ValidationError("Fayl hajmi 10MB dan oshmasligi kerak.")
#         if file.content_type not in allowed_types:
#             raise serializers.ValidationError("Ruxsat etilmagan fayl turi.")
#         return file
