"""Integrate with admin module."""

from django.contrib import admin
from django.conf import settings
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

import os
import pymongo
import environ
from pathlib import Path

from .models import User
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .serializers import UserNameSerializer
from main.methods import get_parsed_data

env = environ.Env()
environ.Env.read_env(os.path.join(Path(__file__).resolve().parent.parent.parent, '.env'))
shopdb_mongo = pymongo.MongoClient("mongodb://localhost:27017/")[env('MONGO_USERNAME')]


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

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        self.save_to_mongo(request, form, change)

    def save_to_mongo(self, request, form, change):
        if change:
            user = form.instance
            posts_ids = list(user.written_posts.values_list('id', flat=True))
            data = get_parsed_data(user, UserNameSerializer)
            mycol = shopdb_mongo[settings.MONGO_POST_COL]
            mycol.update_many({'id': {'$in': posts_ids}}, {'$set': {'json.author': data}})

admin.site.register(User, UserAdmin)
