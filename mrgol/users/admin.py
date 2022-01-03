"""Integrate with admin module."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
 
from .models import User
from .forms import CustomUserCreationForm, CustomUserChangeForm

#@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Define admin model for custom User model with no email field."""
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

    
    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'national_code', 'email', 'job', 'address')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'password1', 'password2'),
        }),
    )
    list_display = ('phone', 'first_name', 'last_name', 'is_staff')
    search_fields = ('phone', 'first_name', 'last_name')
    ordering = ('id',)                     #do ordering by id


admin.site.register(User, UserAdmin)
