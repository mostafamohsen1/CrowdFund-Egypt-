from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ['-date_joined']
    list_display = ['email', 'first_name', 'last_name', 'phone_number', 'is_email_verified', 'is_staff', 'date_joined']
    list_filter = ['is_email_verified', 'is_staff', 'is_superuser', 'is_active']
    search_fields = ['email', 'first_name', 'last_name', 'phone_number']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'phone_number', 'profile_picture', 'birthdate', 'facebook_profile', 'country')}),
        (_('Verification & Status'), {'fields': ('is_email_verified', 'verification_token', 'token_created_at')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    readonly_fields = ['verification_token', 'token_created_at', 'date_joined', 'last_login']
