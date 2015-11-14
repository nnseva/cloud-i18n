from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _ # todo: self-powered version of the translation module

class I18N_ProjectConfig(AppConfig):
    name = 'i18n_project'
    verbose_name = _("I18N Project")
