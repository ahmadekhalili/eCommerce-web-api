from django.conf import settings
from django.apps import AppConfig


class PaymentConfig(AppConfig):
    name = 'payment'
    verbose_name = 'بخش پرداخت' if settings.ERROR_LANGUAGE=='pr' else 'payment'
