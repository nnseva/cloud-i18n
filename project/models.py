from __future__ import unicode_literals
from django.db import models
from django.utils.translation import ugettext as _ # todo: self-powered version of the translation module
from django.core.exceptions import ValidationError

# Create your models here.
class Project(models.Model):
    url = models.URLField(verbose_name=_("URL"),unique=True,help_text=_("URL of the project"))
    name = models.CharField(max_length=64,verbose_name=_("Name"),db_index=True,help_text=_("Name of the project"))
    description = models.TextField(verbose_name=_("Description"),help_text=_("Description of the project"))
    identity_method = models.CharField(max_length=8,verbose_name=_("Identity Method"),help_text=_("Phrase identity method"),choices=(
        ('orig',_("Original Phrase")),
        ('enum',_("Enum")),
        ('int',_("Integer ID")),
    ))

    class Meta:
        verbose_name = _("Project")
        verbose_name_plural = _("Projects")

    def __unicode__(self):
        return "%s: %s" % (self.url,self.name)

class ProjectUser(models.Model):
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
    enum_identity = models.CharField(max_length=64,verbose_name=_("Enum Identity"),db_index=True,null=True,blank=True,help_text=_("Enum Identity of the phrase within this project"))
    int_identity = models.IntegerField(verbose_name=_("Integer Identity"),db_index=True,null=True,blank=True,help_text=_("Integer Identity of the phrase within this project"))
    orig_identity = models.ForeignKey("lexicon.Translation",verbose_name=_("Original Identity"),db_index=True,null=True,blank=True,help_text=_("Original Identity of the phrase within this project"),related_name="project_phrases")
    project = models.ForeignKey(Project,verbose_name=_("Project"),help_text=_("Project containing this phrase"),related_name="phrases")
    phrase = models.ForeignKey("lexicon.Phrase",verbose_name=_("Phrase"),help_text=_("Phrase contained in this project"),related_name="projects")

    class Meta:
        verbose_name = _("Project Phrase")
        verbose_name_plural = _("Project Phrases")
        unique_together = (
            ('project','phrase'),
            ('project','enum_identity','int_identity','orig_identity'),
        )

    def identity(self):
        if not self.project:
            return None
        return getattr(self,self.project.identity_method+"_identity")

    def clean(self):
        for im,imv in Project._meta.get_field_by_name('identity_method')[0].choices:
            if im == self.project.identity_method:
                if not getattr(self,im+'_identity'):
                    raise ValidationError(_("Identity field %s_identity should not be None") % im)
            if getattr(self,im+'_identity'):
                raise ValidationError(_("Not working identity field %s_identity should be set to None") % im)
        if self.orig_identity:
            if self.orig_identity.phrase != self.phrase:
                raise ValidationError(_("The original identity field should refer to the same phrase") % im)

    def __unicode__(self):
        return "%s - %s" % (self.project.url,self.identity())
