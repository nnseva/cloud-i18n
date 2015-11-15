from django.contrib import admin
from . import models
from django.contrib.auth import models as auth_models
from django.utils.translation import ugettext_lazy as _ # todo: self-powered version of the translation module

# Register your models here.
class ProjectUserInline(admin.TabularInline):
    model = models.ProjectUser
    extra = 0

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'user':
            kwargs["queryset"] = auth_models.User.objects.filter(projects__in=request.user.projects.all())
        return super(ProjectUserInline, self).formfield_for_foreignkey(db_field, request, **kwargs)

class ProjectAdmin(admin.ModelAdmin):
    list_display = ('url','name')

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
    parameter_name = 'project'

    def lookups(self, request, model_admin):
        if request.user.is_superuser:
            r = [(p,unicode(p)) for p in models.Project.objects.all()]
        else:
            r = [(p.project,unicode(p.project)) for p in request.user.projects.all()]
        return r

    def queryset(self,request, queryset):
        if self.value():
            return queryset.filter(project=self.value())
        return queryset

class TranslationInline(admin.StackedInline):
    model = models.Translation
    extra = 0

class PhraseAdmin(admin.ModelAdmin):

    def get_list_display(self,*av,**kw):
        return ('project','identity','has_mode')

    inlines = [
        TranslationInline,
    ]

    def name(self,obj):
        return unicode(obj)

    def get_list_filter(self,request,*av,**kw):
        return (VisibleProjectsFilter,)

    def get_fields(self,request,obj=None):
        if not obj:
            return ['project',]+[im+'_identity' for im,imv in models.Project._meta.get_field_by_name('identity_method')[0].choices if im != 'orig']
        return ('project',obj.project.identity_method+'_identity')

    def get_readonly_fields(self,request,obj=None):
        if not obj:
            return ()
        return ('project',)

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
