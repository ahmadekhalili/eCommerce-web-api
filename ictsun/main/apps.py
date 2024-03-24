from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


PROJECT_VERBOSE_NAME = _('MRGol')                    #add traslation of this in locale, we used this in places like:  main/templates/registration/log_out.html      main/admin.py/admin.site.site_header & admin.site.site_title       also note this can be used as context_processors in templates like {{ project_verbose_name }}  

class MainConfig(AppConfig):
    name = 'main'
    verbose_name = _('main app')

