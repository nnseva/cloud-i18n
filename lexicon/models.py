from __future__ import unicode_literals
from django.db import models
from django.utils.translation import ugettext as _ # todo: self-powered version of the translation module

# Create your models here.

class Phrase(models.Model):
    '''
    The word or phrase to be translated. This model identifies and describes it as such. It doesn't contain
    an original prase itself, but is used only to connect phrase originals and translations.
    '''
    has_format = models.BooleanField(verbose_name=_("Has Format Parts"),default=False,editable=False,help_text=_("Format parts found in the phrase"))
    has_plural = models.BooleanField(verbose_name=_("Has Plural Form"),default=False,help_text=_("Plural form is identified by using plural version of the library call"))

    class Meta:
        verbose_name = _("Phrase")
        verbose_name_plural = _("Phrases") # todo: django-specific Meta extension for multiple plural forms

    def get_message(self,lang,plural_id=None):
        tr = self.translations.filter(language=lang,plural_id=plural_id)
        if tr:
            if tr[0].message:
                return tr[0].message
        if '_' in lang:
            lang = lang.split('_')[0]
            tr = self.translations.filter(language=lang,plural_id=plural_id)
            if tr:
                if tr[0].message:
                    return tr[0].message
        lang = 'en'
        tr = self.translations.filter(language=lang,plural_id=plural_id)
        if tr:
            if tr[0].message:
                return tr[0].message
        tr = self.translations.all()
        if tr:
            if tr[0].message:
                return tr[0].message
        return ''

    def __unicode__(self):
        return self.get_message('en') or "phrase: %s" % self.id

class Translation(models.Model):
    '''
    Translated version of the phrase. The original phrase should also be present in this table.
    '''
    phrase = models.ForeignKey(Phrase,verbose_name=_("Phrase"),help_text=_("Phrase identity"),related_name="translations")
    language = models.CharField(max_length=10,verbose_name=_("Language"),help_text=_("The phrase language in form of two-char or four-char identity like 'en' or 'ru_RU'"))
    plural_forms = models.TextField(verbose_name=_("Plural Forms"),null=True,blank=True,help_text=_("The plural forms field value of the gettext file, available only for plural phrase"))
    plural_id = models.IntegerField(verbose_name=_("Plural ID"),null=True,blank=True,help_text=_("Plural ID if the phrase is plural"))
    message = models.TextField(verbose_name=_("Message"),db_index=True,help_text=_("The phrase message in the particular language"))

    class Meta:
        verbose_name = _("Translation")
        verbose_name_plural = _("Translations") # todo: django-specific Meta extension for multiple plural forms
        unique_together = (
            ('phrase','language','plural_id'),
        )

    def __unicode__(self):
        if self.plural_id:
            return "%s [%s]: %s" % (self.language,self.plural_id,self.message)
        return "%s: %s" % (self.language,self.message)
