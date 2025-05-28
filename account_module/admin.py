from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User

# @admin.register(User)
# class CustomUserAdmin(UserAdmin):
#     list_display = ('username', 'email', 'is_email_verified', 'is_staff', 'is_active', 'date_joined')
#     list_filter = ('is_email_verified', 'is_staff', 'is_active', 'date_joined')
#     search_fields = ('username', 'email', 'phone_number')
#     ordering = ('-date_joined',)
    
#     fieldsets = (
#         (None, {'fields': ('username', 'password')}),
#         (_('Personal info'), {'fields': ('email', 'phone_number', 'avatar', 'bio', 'date_of_birth')}),
#         (_('Social'), {'fields': ('social_links',)}),
#         (_('Security'), {'fields': ('email_active_code', 'is_email_verified', 'last_login_ip')}),
#         (_('Permissions'), {
#             'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
#         }),
#         (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
#     )
    
#     add_fieldsets = (
#         (None, {
#             'classes': ('wide',),
#             'fields': ('username', 'email', 'password1', 'password2'),
#         }),
#     )
    
#     def get_readonly_fields(self, request, obj=None):
#         if obj:  # editing an existing object
#             return ('last_login', 'date_joined', 'last_login_ip')
#         return ('last_login', 'date_joined')


admin.site.register(User)