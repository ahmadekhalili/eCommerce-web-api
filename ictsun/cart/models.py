from users.models import User
from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.utils.translation import gettext_lazy as _
from django.contrib.sessions.backends.db import SessionStore
# note1: if you add or remove a field, you have to apply it in translation.py 'fields' if was required.
# note2: if you make changes in a model, you have to apply changes to it's serializers if needed.


class SesKey(models.Model):
    user = models.ForeignKey(User, on_delete = models.CASCADE, blank=True, null=True, verbose_name=_('user'))
    ses_key = models.CharField(_('ses key'), max_length=60, default='', blank=True)

    class Meta:
        verbose_name = _('ses key')
        verbose_name_plural = _('ses keys')

    def __str__(self):
        return _('ses key') + str(self.id)

    
def save_seskey(sender, **kwargs):
    if kwargs['created']:                                                       
        cartsession = SessionStore()
        cartsession.create()
        save_seskey = SesKey.objects.create(user=kwargs['instance'], ses_key=cartsession.session_key)   

post_save.connect(save_seskey, sender=User)


