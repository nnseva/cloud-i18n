from __future__ import unicode_literals
from django.db import models
from django.utils.translation import ugettext_lazy as _ # todo: self-powered version of the translation module
from django.core.exceptions import ValidationError
from django.db.models import F,Q,Count,Max,Min,Avg

import re

from jsoneditor.fields.django_json_field import JSONField

# Create your models here.
class Project(models.Model):
    '''
    Translation project. A single translation file set for the phrase list in different languages. 
    '''
    url = models.URLField(verbose_name=_("URL"),unique=True,help_text=_("URL of the project"))
    name = models.CharField(max_length=64,verbose_name=_("Name"),db_index=True,help_text=_("Name of the project"))
    description = models.TextField(verbose_name=_("Description"),null=True,blank=True,help_text=_("Description of the project"))
    identity_method = models.CharField(max_length=8,verbose_name=_("Identity Method"),help_text=_("Phrase identity method"),choices=(
        ('orig',_("Original Phrase")),
        ('enum',_("Enum")),
        ('int',_("Integer ID")),
    ))
    options = JSONField(verbose_name=_("Options"),null=True,blank=True,help_text=_("The translation options, like language modes formula"))

    class Meta:
        verbose_name = _("Project")
        verbose_name_plural = _("Projects")

    def __unicode__(self):
        return "%s: %s" % (self.url,self.name)

    def get_phrase(self,msgid):
        if self.identity_method == 'int':
            q = self.phrases.filter(int_identity=int(msgid))
        elif self.identity_method == 'enum':
            q = self.phrases.filter(enum_identity=msgid)
        elif self.identity_method == 'orig':
            q = self.phrases.filter(orig_identity__message=msgid)
        return q[0] if q else None

class ProjectUser(models.Model):
    '''
    Translation project user. Every user can access to the translation in readonly mode,
    but only selected users can access the translation in read-write mode. 
    '''
    project = models.ForeignKey(Project,verbose_name=_("Project"),help_text=_("Project accessed by this user"),related_name="users")
    user = models.ForeignKey("auth.User",verbose_name=_("User"),help_text=_("User accessing this project"),related_name="projects")

    class Meta:
        verbose_name = _("Project User")
        verbose_name_plural = _("Project Users")
        unique_together = (
            ('project','user'),
        )

    def __unicode__(self):
        return "%s - %s" % (self.project.url,self.user)

class ProjectPhrase(models.Model):
    '''
    The word or phrase to be translated as sush. It doesn't contain
    an original prase itself, but is used only to connect phrase originals and translations.
    '''
    enum_identity = models.CharField(max_length=64,verbose_name=_("Enum Identity"),db_index=True,null=True,blank=True,help_text=_("Enum Identity of the phrase within this project"))
    int_identity = models.IntegerField(verbose_name=_("Integer Identity"),db_index=True,null=True,blank=True,help_text=_("Integer Identity of the phrase within this project"))
    orig_identity = models.ForeignKey("i18n_project.Translation",verbose_name=_("Original Identity"),db_index=True,null=True,blank=True,on_delete=models.SET_NULL, help_text=_("Original Identity of the phrase within this project"),related_name="project_phrases")
    options = JSONField(verbose_name=_("Options"),null=True,blank=True,help_text=_("The translation options, like language modes formula"))
    project = models.ForeignKey(Project,verbose_name=_("Project"),help_text=_("Project containing this phrase"),related_name="phrases")

    class Meta:
        verbose_name = _("Project Phrase")
        verbose_name_plural = _("Project Phrases")
        unique_together = (
            ('project','enum_identity','int_identity','orig_identity'),
        )

    def get_identity(self):
        if not self.project:
            return None
        return getattr(self,self.project.identity_method+"_identity")

    get_identity.short_description = _("Identity")
    identity = property(get_identity)

    def clean(self):
        for im,imv in Project._meta.get_field_by_name('identity_method')[0].choices:
            if im == self.project.identity_method:
                if not getattr(self,im+'_identity'):
                    if im == 'orig' and not self.translations.all():
                        pass # omit to enable filling identity later
                    else:
                        raise ValidationError(_("Identity field %s_identity should not be None") % im)
            elif getattr(self,im+'_identity'):
                raise ValidationError(_("Not working identity field %s_identity should be set to None") % im)
        if self.orig_identity:
            if self.orig_identity.phrase.id != self.id:
                raise ValidationError(_("The original identity field should refer to this phrase translation"))

    def get_languages(self):
        return [lng['language'] for lng in self.translations.all().values('language').distinct()]

    languages = property(get_languages)

    def get_has_mode(self):
        return bool(type(self).objects.filter(id=self.id).annotate(mds=Count('translations__mode_id')).filter(mds__gt=1))
    get_has_mode.short_description = _("Has Mode")
    get_has_mode.boolean = True

    has_mode = property(get_has_mode)

    def get_has_format(self):
        return bool(self.options and self.options.get('format',None))
    get_has_format.short_description = _("Has Format")
    get_has_format.boolean = True

    has_format = property(get_has_format)

    def get_has_fuzzy(self):
        return bool(self.options and self.options.get('fuzzy',None))
    get_has_fuzzy.short_description = _("Has Fuzzy")
    get_has_fuzzy.boolean = True

    has_fuzzy = property(get_has_fuzzy)

    def get_message(self,lang,mode_id=None):
        tr = self.get_tr(lang,mode_id)
        if tr:
            return tr.message
        return ''

    def get_original(self,lang,mode_id=None):
        tr = self.get_tr(lang,mode_id)
        if tr:
            return tr.original
        return ''

    def get_tr(self,lang,mode_id=None):
        if mode_id is None and self.has_mode:
            mode_id = self.translations.aggregate(models.Min('mode_id'))['mode_id__min']
        tr = self.translations.filter(language=lang,mode_id=mode_id)
        if tr:
            if tr[0].message:
                return tr[0]
        if '_' in lang:
            lang = lang.split('_')[0]
            tr = self.translations.filter(language=lang,mode_id=mode_id)
            if tr:
                if tr[0].message:
                    return tr[0]
        lang = 'en'
        tr = self.translations.filter(language=lang,mode_id=mode_id)
        if tr:
            if tr[0].message:
                return tr[0]
        tr = self.translations.all()
        if tr:
            if tr[0].message:
                return tr[0]

    def fix_translations(self):
        if not self.has_mode:
            for t in self.translations.all():
                if t.mode_id is not None:
                    t.mode_id = None
                    t.save()

    def __unicode__(self):
        return "%s - %s" % (self.project.url,self.get_message('en') or "phrase: %s" % self.id)

class Translation(models.Model):
    '''
    Translated version of the phrase. The original phrase is also present here.
    '''
    phrase = models.ForeignKey(ProjectPhrase,verbose_name=_("Phrase"),help_text=_("Phrase identity"),related_name="translations")
    language = models.CharField(max_length=10,verbose_name=_("Language"),help_text=_("The phrase language in form of two-char or four-char identity like 'en' or 'ru_RU'"))
    message = models.TextField(verbose_name=_("Message"),db_index=True,editable=False,help_text=_("The normalized phraze message in the particular language"))
    original = models.TextField(verbose_name=_("Original"),db_index=True,help_text=_("The original phrase message in the particular language"))

    mode_id = models.IntegerField(verbose_name=_("Mode ID"),null=True,blank=True,help_text=_("Mode ID if the phrase has several modes depending on parameters"))
    options = JSONField(verbose_name=_("Options"),null=True,blank=True,help_text=_("The translation options, like collected placehosders and modes formula"))

    class Meta:
        verbose_name = _("Translation")
        verbose_name_plural = _("Translations") # todo: django-specific Meta extension for multiple plural forms
        unique_together = (
            ('phrase','language','mode_id'),
        )
        ordering = ('phrase','language','mode_id')

    def __unicode__(self):
        if self.mode_id is not None:
            return "%s [%s]: %s" % (self.language,self.mode_id,self.message)
        return "%s: %s" % (self.language,self.message)

    def normalize(self):
        '''Convert original to normalized message using current settings'''
        from utils.import_export import extract_message
        self.options = self.options or {}
        self.message = extract_message(self.original,self.phrase.options,self.options)

    def save(self,*av,**kw):
        self.normalize()
        super(Translation,self).save(*av,**kw)
