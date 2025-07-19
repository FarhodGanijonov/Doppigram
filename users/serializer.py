from rest_framework import serializers
from .models import AbstractUser

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirmation = serializers.CharField(write_only=True)

    class Meta:
        model = AbstractUser
        fields = ['id', 'full_name', 'phone', 'password', 'password_confirmation']

    def validate(self, data):
        if data['password'] != data['password_confirmation']:
            raise serializers.ValidationError("Parollar bir xil emas.")
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirmation')
        user = AbstractUser(
            full_name=validated_data['full_name'],
            phone=validated_data['phone'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user



class UserLoginSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        phone = data.get('phone')
        password = data.get('password')
        user = AbstractUser.objects.filter(phone=phone).first()

        if user and user.check_password(password):
            if not user.is_active:
                raise serializers.ValidationError("Foydalanuvchi faol emas.")
            return user
        raise serializers.ValidationError("Noto‘g‘ri telefon raqam yoki parol.")


class UserPasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_new_password = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Eski parol noto‘g‘ri.")
        return value

    def validate(self, data):
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError("Yangi parollar bir xil emas.")
        return data

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AbstractUser
        fields = ['id', 'phone', 'full_name', 'avatar', 'bio', 'created_at']
        read_only_fields = ['id', 'phone', 'created_at']

class ContactSearchSerializer(serializers.Serializer):
    contacts = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=False
    )