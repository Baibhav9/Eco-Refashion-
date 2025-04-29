from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


class CustomUserAdmin(UserAdmin):
    # If you want to show the role in the admin list:
    fieldsets = (
        (None, {'fields': ('username', 'password', 'role', 'phone')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'user_permissions', 'groups')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    list_display = ('username', 'email', 'role', 'is_staff', 'is_superuser')

admin.site.register(CustomUser, CustomUserAdmin)
