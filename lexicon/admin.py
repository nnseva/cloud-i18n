from django.contrib import admin
from . import models

# Register your models here.
class TranslationInline(admin.StackedInline):
    model = models.Translation
    extra = 0

class PhraseAdmin(admin.ModelAdmin):
    list_display = ('name','has_format','has_plural')

    inlines = [
        TranslationInline,
    ]
    def name(self,obj):
        return unicode(obj)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        parent = None
        if instances:
            parent = instances[0].phrase
        for obj in formset.deleted_objects:
            if not parent:
                parent = obj.phrase
            obj.delete()
        for instance in instances:
            instance.save()
        formset.save_m2m()
        if parent:
            parent.fix_translations()

admin.site.register(models.Phrase,PhraseAdmin)
