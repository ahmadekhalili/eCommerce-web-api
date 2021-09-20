from django.conf import settings
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class OrdersConfig(AppConfig):
    name = 'orders'
    verbose_name = _('orders app')
