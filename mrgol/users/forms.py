from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from phonenumber_field.formfields import PhoneNumberField

from .models import User


class CustomUserCreationForm(UserCreationForm):
    #phone = PhoneNumberField()
    class Meta(UserCreationForm):
        model = User
        fields = ('phone',)


class CustomUserChangeForm(UserChangeForm):
    address = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={'style': 'direction: rtl; text-align: right;'}))
    #phone = PhoneNumberField()
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'address']


