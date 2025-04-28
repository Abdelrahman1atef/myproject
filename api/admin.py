# api/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import AppUser

@admin.register(AppUser)
class CustomUserAdmin(UserAdmin):
    # Define fieldsets for editing existing users
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal Info'), {'fields': ('first_name', 'last_name', 'birthdate', 'gender', 'auth_type', 'social_id', 'profile_picture')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff')}),
        (_('Important Dates'), {'fields': ('last_login', 'created_at', 'updated_at')}),
    )

    # Define fieldsets for adding new users
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )

    # Define which fields to display in the admin list view
    list_display = ('email', 'first_name', 'last_name', 'is_active', 'is_staff')

    # Define filters for the admin list view
    list_filter = ('is_active', 'is_staff')

    # Define fields to search by
    search_fields = ('email', 'first_name', 'last_name')

    # Define the default ordering for the admin list view
    ordering = ('email',)

    # Remove references to groups and user_permissions
    filter_horizontal = ()