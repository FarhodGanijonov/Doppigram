from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

class Chat(models.Model):
    user1 = models.ForeignKey(User, related_name='chats1', on_delete=models.CASCADE)
    user2 = models.ForeignKey(User, related_name='chats2', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user1', 'user2')

    def __str__(self):
        return f"Chat: {self.user1} & {self.user2}"


class Message(models.Model):
    MESSAGE_TYPES = (
        ("text", "Text"),
        ("image", "Image"),
        ("video", "Video"),
        ("audio", "Audio"),
        ("round_video", "Round Video"),
    )

    chat = models.ForeignKey(Chat, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, related_name='messages', on_delete=models.CASCADE)

    type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default="text")

    text = models.TextField(blank=True)

    file = models.FileField(upload_to='chat/files/', blank=True, null=True)

    duration = models.FloatField(null=True, blank=True)  # video/audio davomiyligi
    waveform = models.JSONField(null=True, blank=True)   # voice (voice note) waves

    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.type.upper()} from {self.sender}"
