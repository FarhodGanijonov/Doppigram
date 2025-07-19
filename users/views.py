from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from users.models import AbstractUser
from users.serializer import UserRegistrationSerializer, UserLoginSerializer, UserPasswordChangeSerializer, \
    UserProfileSerializer, ContactSearchSerializer


class UserRegistrationView(generics.CreateAPIView):
    queryset = AbstractUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)

        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": self.get_serializer(user).data
        }, status=status.HTTP_201_CREATED)



class UserLoginView(generics.GenericAPIView):
    serializer_class = UserLoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data

        refresh = RefreshToken.for_user(user)

        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": UserRegistrationSerializer(user).data,
        }, status=status.HTTP_200_OK)


class UserPasswordChangeView(generics.GenericAPIView):
    serializer_class = UserPasswordChangeSerializer
    permission_classes = [IsAuthenticated]  # faqat user roli bo‘lsa

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Password updated successfully."})


class UserMeView(generics.RetrieveAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class UserUpdateProfileView(generics.UpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()  # tokenni bloklaydi
            return Response({"message": "Logout muvaffaqiyatli bajarildi."}, status=status.HTTP_205_RESET_CONTENT)
        except KeyError:
            return Response({"error": "refresh token yuborilmadi."}, status=status.HTTP_400_BAD_REQUEST)
        except TokenError:
            return Response({"error": "Token yaroqsiz yoki allaqachon bekor qilingan."}, status=status.HTTP_400_BAD_REQUEST)


class ContactSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ContactSearchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        contact_list = serializer.validated_data['contacts']

        users = AbstractUser.objects.filter(phone__in=contact_list).exclude(id=request.user.id)
        data = UserProfileSerializer(users, many=True, context={'request': request}).data
        return Response(data)