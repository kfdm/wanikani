from django.db import models
from django.utils.translation import ugettext_lazy as _

class ApiKey(models.Model):
    user = models.OneToOneField(
        'auth.User',
        on_delete=models.CASCADE,
        primary_key=True,
        verbose_name=_('user')
    )
    key = models.CharField(max_length=32, verbose_name=_('apikey'))

    class Meta:
        verbose_name = _('apikey')
        unique_together = ('user', 'key')
