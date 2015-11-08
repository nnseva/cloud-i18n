from django.contrib import admin
from . import models

# Register your models here.
class ProjectUserInline(admin.TabularInline):
    model = models.ProjectUser
    extra = 0

class ProjectAdmin(admin.ModelAdmin):
    list_display = ('url','name')

    inlines = [
        ProjectUserInline,
    ]

admin.site.register(models.Project,ProjectAdmin)
