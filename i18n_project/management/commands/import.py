import os
from optparse import make_option
from zipfile import is_zipfile, ZipFile

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from i18n_project.utils.import_export import import_file
from i18n_project import models
class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option(
            "-U","--project-url",
            action="store",
            dest="project_url",
            help="Import translation file(s) into this project",
        ),
        make_option(
            "-P","--project-name",
            action="store",
            dest="project_name",
            help="Import translation file(s) into this project",
        ),
        make_option(
            "-L","--language",
            action="store",
            dest="language",
            help="Force language for the file(s)",
        ),
    )
    args = "<file> (<file>...)"
    help = "Import a translation file(s) or a zip of translation file(s)"

    def handle(self, *args, **options):
        if not options['project_url'] and not options['project_name']:
            print "Eiter project URL, or project name should be defined"
            return
        project_url = options['project_url']
        project_name = options['project_name']
        if not project_name:
            project_name = project_url
        language = options['language']
        prj = None
        if project_url:
            prj = models.Project.objects.filter(url=project_url)
            if prj:
                prj = prj[0]
        if not prj:
            if project_name:
                prj = models.Project.objects.filter(name=project_name)
        if not prj:
            if not project_url:
                print "No such project name: %s" % project_name
                return
            prj = models.Project(name=project_name,url=project_url,identity_method='orig') # todo: depending on file type?
        else:
            if project_name:
                prj.name = project_name
            if project_url:
                prj.url = project_url
        prj.save()

        for filename in args:
            if is_zipfile(filename):
                with ZipFile(filename, "r") as zf:
                    for path in zf.namelist():
                        with zf.open(path, "r") as f:
                            if path.endswith("/"):
                                # is a directory
                                continue
                            try:
                                import_file(f, prj, language)
                            except Exception as e:
                                self.stderr.write("Warning: %s" % (e))
            else:
                with open(filename, "r") as f:
                    #try:
                        import_file(f, prj, language)
                    #except Exception as e:
                     #   raise CommandError(e)