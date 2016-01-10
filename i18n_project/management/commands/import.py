import os
import re
from optparse import make_option
from zipfile import is_zipfile, ZipFile

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from i18n_project.utils.import_export import import_file
from i18n_project import models
class Command(BaseCommand):
    LANGUAGE_EXT = r"\.([^.]*)\.po$"
    LANGUAGE_PATH_1 = "%(e)s([^%(e)s]*)%(e)s^%(e)s*$" % { 'e':os.pathsep }
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
        make_option(
            "-S","--search-language",
            action="store",
            dest="search_language",
            help="Search language for the file(s) in the file path using regular expression: the first matched group will be used, use (?:...) to exclude group from the result",
        ),
        make_option(
            "--search-language-ext",
            action="store_const",
            dest="search_language",
            const=LANGUAGE_EXT,
            help="Search language for the file(s) just before the extension using RE %s" % LANGUAGE_EXT,
        ),
        make_option(
            "--search-language-path-1",
            action="store_const",
            dest="search_language",
            const=LANGUAGE_PATH_1,
            help="Search language for the file(s) just before the file name RE %s" % LANGUAGE_PATH_1,
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
        search_language = options['search_language']
        if search_language:
            search_language = re.compile(search_language)
        prj = None
        if project_url:
            prj = models.Project.objects.filter(url=project_url)
            if prj:
                if options['verbosity'] > 1: self.stdout.write("Found project %s" % prj)
                prj = prj[0]
        if not prj:
            if project_name:
                prj = models.Project.objects.filter(name=project_name)
            if prj:
                if options['verbosity'] > 1: self.stdout.write("Found project %s" % prj)
                prj = prj[0]
        if not prj:
            if not project_url:
                self.stderr.write("No such project name: %s" % project_name)
                return
            prj = models.Project(name=project_name,url=project_url,identity_method='orig') # todo: depending on file type?
            if options['verbosity'] > 1: self.stdout.write("Created project %s" % prj)
        else:
            if project_name:
                prj.name = project_name
            if project_url:
                prj.url = project_url
            if options['verbosity'] > 1: self.stdout.write("Fixed project %s" % prj)
        prj.save()

        for filename in args:
            if is_zipfile(filename):
                if options['verbosity'] > 1: self.stdout.write("Importing zip file %s" % filename)
                with ZipFile(filename, "r") as zf:
                    for path in zf.namelist():
                        with zf.open(path, "r") as f:
                            if path.endswith("/"):
                                # is a directory
                                continue
                            try:
                                lang = language
                                if search_language:
                                    lang = search_language.search(path)
                                    if not lang:
                                        self.stderr.write("Warning: language part not found in the path: %s" % (path))
                                        continue
                                    lang = lang.group(1)
                                if options['verbosity'] > 1: self.stdout.write("Importing file %s from the zip using language %s" % (path,lang))
                                import_file(f, prj, lang)
                            except Exception as e:
                                self.stderr.write("Warning: %s" % (e))
            else:
                with open(filename, "r") as f:
                    try:
                        lang = language
                        if search_language:
                            lang = search_language.search(filename)
                            if not lang:
                                self.stderr.write("Warning: language part not found in the path: %s" % (filename))
                                continue
                            lang = lang.group(1)
                        if options['verbosity'] > 1: self.stdout.write("Importing file %s using language %s" % (filename,lang))
                        import_file(f, prj, lang)
                    except Exception as e:
                        self.stderr.write("Warning: %s" % (e))
