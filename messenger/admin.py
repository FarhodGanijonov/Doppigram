from django.contrib import admin

from messenger.models import Chat, Message


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('id', 'user1', 'user2', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user1__username', 'user2__username')
    ordering = ('-created_at',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'chat', 'sender', 'short_text', 'timestamp', 'is_read')
    list_filter = ('is_read', 'timestamp')
    search_fields = ('sender__username', 'chat__user1__username', 'chat__user2__username', 'text')
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp',)

    def short_text(self, obj):
        return obj.text[:30] + ("..." if len(obj.text) > 30 else "")
    short_text.short_description = 'Text'
