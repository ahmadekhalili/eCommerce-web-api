from django.conf import settings
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PaymentConfig(AppConfig):
    name = 'payment'
    verbose_name = _('payment app')
