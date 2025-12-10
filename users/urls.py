from django.urls import path
from users.views import UserPasswordChangeView, UserRegistrationView, UserLoginView, UserMeView, UserUpdateProfileView, \
    LogoutView, ContactSearchView, UserListView

urlpatterns = [
    path('registerr/', UserRegistrationView.as_view(), name='user-register'),
    path('login/', UserLoginView.as_view(), name='user-login'),
    path('change-password/', UserPasswordChangeView.as_view(), name='user-change-password'),
    path('me/', UserMeView.as_view(), name='user-me'),
    path('me/update/', UserUpdateProfileView.as_view(), name='user-update'),
    path('logout/', LogoutView.as_view(), name='user-logout'),
    path('contacts/', ContactSearchView.as_view(), name='contact-search'),
    path("users/lists/", UserListView.as_view(), name="user-list"),

]
