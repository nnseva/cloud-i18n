from django.contrib import admin
from . import models
from django.contrib.auth import models as auth_models
from django.utils.translation import ugettext_lazy as _ # todo: self-powered version of the translation module
from django.db.models import F,Q,Count,Max,Min,Avg

# Register your models here.
class ProjectUserInline(admin.TabularInline):
    model = models.ProjectUser
    extra = 0

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'user':
            kwargs["queryset"] = auth_models.User.objects.filter(projects__in=request.user.projects.all())
        return super(ProjectUserInline, self).formfield_for_foreignkey(db_field, request, **kwargs)

class ProjectAdmin(admin.ModelAdmin):
    fields = ('url','name','description','identity_method','tags','options')
    list_display = ('url','name')
    search_fields = ('url','name')

    inlines = [
        ProjectUserInline,
    ]

    def get_queryset(self, request):
        if request.user.is_superuser:
            r = models.Project.objects.all()
        else:
            r = models.Project.objects.filter(users__user=request.user)
        return r

    def save_model(self,request, obj, form, change):
        super(ProjectAdmin,self).save_model(request, obj, form, change)
        if not change: # a new one
            obj.users.create(user=request.user)

admin.site.register(models.Project,ProjectAdmin)

class VisibleProjectsFilter(admin.SimpleListFilter):
    title = models.Project._meta.verbose_name
    parameter_name = 'project_id'

    def lookups(self, request, model_admin):
        if request.user.is_superuser:
            r = [(p.id,unicode(p)) for p in models.Project.objects.all()]
        else:
            r = [(p.project.id,unicode(p.project)) for p in request.user.projects.all()]
        return r

    def queryset(self,request, queryset):
        if self.value():
            return queryset.filter(project_id=self.value())
        return queryset

class HasModeFilter(admin.SimpleListFilter):
    title = models.ProjectPhrase.get_has_mode.short_description
    parameter_name = 'has_mode'

    def lookups(self, request, model_admin):
        return (
            ('True',_("Yes")),
            ('False',_("No"))
        )

    def queryset(self,request, queryset):
        if self.value() == 'True':
            return queryset.annotate(mds=Count('translations__mode_id')).filter(mds__gt=1)
        elif self.value() == 'False':
            return queryset.annotate(mds=Count('translations__mode_id')).filter(mds__lte=1)
        return queryset

class HasFormatFilter(admin.SimpleListFilter):
    title = models.ProjectPhrase.get_has_format.short_description
    parameter_name = 'has_format'

    def lookups(self, request, model_admin):
        return (
            ('True',_("Yes")),
            ('False',_("No"))
        )

    def queryset(self,request, queryset):
        if self.value() == 'True':
            return queryset.filter(options__contains='"format":')
        elif self.value() == 'False':
            return queryset.exclude(options__contains='"format":')
        return queryset

class HasFuzzyFilter(admin.SimpleListFilter):
    title = models.ProjectPhrase.get_has_fuzzy.short_description
    parameter_name = 'has_fuzzy'

    def lookups(self, request, model_admin):
        return (
            ('True',_("Yes")),
            ('False',_("No"))
        )

    def queryset(self,request, queryset):
        if self.value() == 'True':
            return queryset.filter(options__contains='"fuzzy": true')
        elif self.value() == 'False':
            return queryset.exclude(options__contains='"fuzzy": true')
        return queryset


from django.utils.safestring import mark_safe

def _message_formatted(obj):
        replacements = []
        if obj.options.get('format'):
            f = obj.options['format']
            replacements = obj.options['formats'][f].get('replacements',[])
        prefix = obj.options.get('prefix','') or ''
        suffix = obj.options.get('suffix','') or ''
        replacements.sort(key=lambda x:x['start'])
        msg = obj.message
        msg_ret = ""
        start = 0
        for r in replacements:
            msg_ret += '%s<span style="background-color:lightblue">%s</span>' % (msg[start:r['start']],r['local'])
            start = r['stop']
        msg_ret += msg[start:]
        return mark_safe('<pre>%(prefix)s%(msg)s%(suffix)s</pre>' % {
            'msg':msg_ret,
            'prefix':prefix,
            'suffix':suffix
        })

class TranslationInline(admin.StackedInline):
    model = models.Translation
    extra = 0
    readonly_fields = ['message']

class PhraseAdmin(admin.ModelAdmin):

    def get_list_display(self,*av,**kw):
        return ('identity','project','get_has_mode','get_has_format','get_has_fuzzy')

    inlines = [
        TranslationInline,
    ]

    def name(self,obj):
        return unicode(obj)

    def get_list_filter(self,request,*av,**kw):
        return (VisibleProjectsFilter,HasModeFilter,HasFormatFilter,HasFuzzyFilter)

    def get_fields(self,request,obj=None):
        if not obj:
            return ['project']+[im+'_identity' for im,imv in models.Project._meta.get_field_by_name('identity_method')[0].choices if im != 'orig']+['options']
        return ('project',obj.project.identity_method+'_identity','tags','options')

    def get_search_fields(self,request,*av,**kw):
        return ('enum_identity','int_identity','translations__message')

    def get_readonly_fields(self,request,obj=None):
        if not obj:
            return ()
        return ('project',)

    def get_ordering(self,request):
        return ['enum_identity','int_identity','orig_identity__message']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'orig_identity':
            id = request.path.split('/')[-2]
            if id.isdigit():
                kwargs["queryset"] = models.Translation.objects.filter(phrase__id=id)
            else:
                kwargs["queryset"] = models.Translation.objects.none()
        if db_field.name == 'project':
            kwargs["queryset"] = models.Project.objects.filter(users__user=request.user)
        return super(PhraseAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

    def save_formset(self, request, form, formset, change):
        super(PhraseAdmin,self).save_formset(request, form, formset, change)
        phrase = formset.instance
        project = phrase.project
        if project.identity_method == 'orig' and not phrase.orig_identity and phrase.translations.all():
            if phrase.translations.filter(language='en'):
                phrase.orig_identity = phrase.translations.filter(language='en')[0]
            elif phrase.translations.filter(language__startswith='en_'):
                phrase.orig_identity = phrase.translations.filter(language__startswith='en_')[0]
            else:
                phrase.orig_identity = phrase.translations.all()[0]
            phrase.save()

    def get_queryset(self, request):
        if request.user.is_superuser:
            r = models.ProjectPhrase.objects.all()
        else:
            r = models.ProjectPhrase.objects.filter(project__users__user=request.user)
        return r

admin.site.register(models.ProjectPhrase,PhraseAdmin)
