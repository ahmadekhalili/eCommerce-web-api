from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager

from rest_framework import serializers

from phonenumber_field.modelfields import PhoneNumberField

from .mymethods import user_name_shown


def validate_national_code(date):
    if len(date) != 10:
        raise ValidationError(_("10 digit national code"))
    
class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""
    use_in_migrations = True

    def _create_user(self, phone, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not phone:
            raise ValueError('The given email must be set')
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, phone, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(phone, password, **extra_fields)

    def create_superuser(self, phone, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(phone, password, **extra_fields)




class User(AbstractUser):                #User post_save in cart.models.SesKey, meant create SesKey after creating user. 
    username = None                     #note: (blank=True, unique=True) raise error!! blank should be False
    phone = PhoneNumberField(_('phone number'), blank=False, null=False, unique=True)
    national_code = models.CharField(_('national code'), max_length=20, validators=[validate_national_code], blank=False, null=True, unique=True, db_index=False)
    email = models.EmailField(_('email address'), blank=True, null=True)
    job = models.CharField(_('job'), max_length=50, blank=True, null=True)
    address = models.CharField(_('address'), max_length=255, blank=True, null=True)
    visible = models.BooleanField(_('delete'), default=True, db_index=True)                  #we use visible for deleting an object, for deleting visible=False, in fact we must dont delete any object.  


    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        #abstract = True                                    #puting this will rase error (abstract will assign correctly by parrent class PermissionsMixin)
    
    def __str__(self):
        return user_name_shown(self)                   
