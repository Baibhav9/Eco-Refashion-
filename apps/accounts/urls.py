from django.urls import path

from .forms import CustomPasswordChangeForm
from .views import LogoutView, LoginView, RegisterView, UserProfileView, CustomPasswordChangeView, UserProfileUpdate
from django.contrib.auth import views as auth_views

app_name = 'accounts'
urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path("profile/", UserProfileView.as_view(), name="profile"),

    path("profile_update/", UserProfileUpdate.as_view(), name="profile_update"),
    path('profile/change-password/', auth_views.PasswordChangeView.as_view(
        form_class=CustomPasswordChangeForm,
        template_name='accounts/change_password.html',
        success_url='/accounts/profile/'
    ), name='change_password'),
    path('profile/change-password/', CustomPasswordChangeView.as_view(), name='change_password'),

]
