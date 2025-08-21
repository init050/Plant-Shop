from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'email',
        'username', 
        'get_avatar',
        'is_email_verified',
        'is_active',
        'date_joined'
    )
    
    list_filter = (
        'is_email_verified',
        'is_active',
        'is_staff',
        'date_joined'
    )
    
    search_fields = ('email', 'username', 'phone_number')
    ordering = ('-date_joined',)
    
    readonly_fields = ('date_joined', 'updated_at', 'last_login')
    
    fieldsets = (
        (None, {
            'fields': ('email', 'username', 'password')
        }),
        (_('Personal Info'), {
            'fields': ('phone_number', 'avatar')
        }),
        (_('Email'), {
            'fields': ('is_email_verified', 'pending_email')
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser')
        }),
        (_('Dates'), {
            'fields': ('last_login', 'date_joined', 'updated_at')
        })
    )
    
    add_fieldsets = (
        (None, {
            'fields': ('email', 'username', 'phone_number', 'password1', 'password2')
        }),
    )
    
    actions = ['activate_users', 'verify_emails']
    
    def get_avatar(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="{}" width="30" height="30" style="border-radius: 50%;" />',
                obj.avatar.url
            )
        return '❌'
    get_avatar.short_description = _('Avatar')
    
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} users activated.')
    activate_users.short_description = _('Activate selected users')
    
    def verify_emails(self, request, queryset):
        updated = queryset.update(is_email_verified=True)
        self.message_user(request, f'{updated} emails verified.')
    verify_emails.short_description = _('Verify selected emails')