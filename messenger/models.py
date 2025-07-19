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
    chat = models.ForeignKey(Chat, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, related_name='messages', on_delete=models.CASCADE)
    text = models.TextField()
    file = models.FileField(upload_to='chat/files/', blank=True, null=True)  # media fayl
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"From {self.sender} | {self.text[:20]}"
