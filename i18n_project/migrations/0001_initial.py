# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings
import jsoneditor.fields.django_json_field


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.URLField(help_text='URL of the project', unique=True, verbose_name='URL')),
                ('name', models.CharField(help_text='Name of the project', max_length=64, verbose_name='Name', db_index=True)),
                ('description', models.TextField(help_text='Description of the project', null=True, verbose_name='Description', blank=True)),
                ('identity_method', models.CharField(help_text='Phrase identity method', max_length=8, verbose_name='Identity Method', choices=[('orig', 'Original Phrase'), ('enum', 'Enum'), ('int', 'Integer ID')])),
                ('options', jsoneditor.fields.django_json_field.JSONField(default='null', help_text='The translation options, like language modes formula', null=True, verbose_name='Options', blank=True)),
            ],
            options={
                'verbose_name': 'Project',
                'verbose_name_plural': 'Projects',
            },
        ),
        migrations.CreateModel(
            name='ProjectPhrase',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('enum_identity', models.CharField(max_length=64, blank=True, help_text='Enum Identity of the phrase within this project', null=True, verbose_name='Enum Identity', db_index=True)),
                ('int_identity', models.IntegerField(help_text='Integer Identity of the phrase within this project', null=True, verbose_name='Integer Identity', db_index=True, blank=True)),
                ('options', jsoneditor.fields.django_json_field.JSONField(default='null', help_text='The translation options, like language modes formula', null=True, verbose_name='Options', blank=True)),
            ],
            options={
                'verbose_name': 'Project Phrase',
                'verbose_name_plural': 'Project Phrases',
            },
        ),
        migrations.CreateModel(
            name='ProjectUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('project', models.ForeignKey(related_name='users', verbose_name='Project', to='i18n_project.Project', help_text='Project accessed by this user')),
                ('user', models.ForeignKey(related_name='projects', verbose_name='User', to=settings.AUTH_USER_MODEL, help_text='User accessing this project')),
            ],
            options={
                'verbose_name': 'Project User',
                'verbose_name_plural': 'Project Users',
            },
        ),
        migrations.CreateModel(
            name='Translation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('language', models.CharField(help_text="The phrase language in form of two-char or four-char identity like 'en' or 'ru_RU'", max_length=10, verbose_name='Language')),
                ('message', models.TextField(help_text='The normalized phraze message in the particular language', verbose_name='Message', editable=False, db_index=True)),
                ('original', models.TextField(help_text='The original phrase message in the particular language', verbose_name='Original', db_index=True)),
                ('mode_id', models.IntegerField(help_text='Mode ID if the phrase has several modes depending on parameters', null=True, verbose_name='Mode ID', blank=True)),
                ('options', jsoneditor.fields.django_json_field.JSONField(default='null', help_text='The translation options, like collected placehosders and modes formula', null=True, verbose_name='Options', blank=True)),
                ('phrase', models.ForeignKey(related_name='translations', verbose_name='Phrase', to='i18n_project.ProjectPhrase', help_text='Phrase identity')),
            ],
            options={
                'ordering': ('phrase', 'language', 'mode_id'),
                'verbose_name': 'Translation',
                'verbose_name_plural': 'Translations',
            },
        ),
        migrations.AddField(
            model_name='projectphrase',
            name='orig_identity',
            field=models.ForeignKey(related_name='project_phrases', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='i18n_project.Translation', help_text='Original Identity of the phrase within this project', null=True, verbose_name='Original Identity'),
        ),
        migrations.AddField(
            model_name='projectphrase',
            name='project',
            field=models.ForeignKey(related_name='phrases', verbose_name='Project', to='i18n_project.Project', help_text='Project containing this phrase'),
        ),
        migrations.AlterUniqueTogether(
            name='translation',
            unique_together=set([('phrase', 'language', 'mode_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='projectuser',
            unique_together=set([('project', 'user')]),
        ),
        migrations.AlterUniqueTogether(
            name='projectphrase',
            unique_together=set([('project', 'enum_identity', 'int_identity', 'orig_identity')]),
        ),
    ]
