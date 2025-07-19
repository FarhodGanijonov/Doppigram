from django.contrib import admin

from users.models import AbstractUser


@admin.register(AbstractUser)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'phone', 'full_name', 'is_active')
    search_fields = ('phone', 'full_name')