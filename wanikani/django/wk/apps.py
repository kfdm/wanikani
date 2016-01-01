from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class WkConfig(AppConfig):
    name = 'wanikani.django.wk'
    verbose_name = _('wanikani')
