from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.validators import MaxLengthValidator

from phonenumber_field.formfields import PhoneNumberField

from .models import User


class CustomUserCreationForm(UserCreationForm):
    #phone = PhoneNumberField()
    class Meta(UserCreationForm):
        model = User
        fields = ('phone',)


class CustomUserChangeForm(UserChangeForm):
    address = forms.CharField(validators=[MaxLengthValidator(255)], required=False, widget=forms.Textarea, label=_('address'))
    #phone = PhoneNumberField()
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'address']


