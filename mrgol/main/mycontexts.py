from django.conf import settings
from .apps import PROJECT_VERBOSE_NAME
from django.utils.translation import gettext_lazy as _

def project_verbose(request=None):                         #for model fields, form fiels, models, forms and apps we have verbose but for project no!! so we definded it for using in admin templates and others maybe. add this in settings.py/TEMPLATES/context_processors
    return {'project_verbose_name': str(PROJECT_VERBOSE_NAME)}
