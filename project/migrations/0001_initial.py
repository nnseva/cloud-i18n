# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('lexicon', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.URLField(help_text='URL of the project', unique=True, verbose_name='URL')),
                ('name', models.CharField(help_text='Name of the project', max_length=64, verbose_name='Name', db_index=True)),
                ('description', models.TextField(help_text='Description of the project', verbose_name='Description')),
                ('identity_method', models.CharField(help_text='Phrase identity method', max_length=8, verbose_name='Identity Method', choices=[('orig', 'Original Phrase'), ('enum', 'Enum'), ('int', 'Integer ID')])),
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
                ('orig_identity', models.ForeignKey(related_name='project_phrases', blank=True, to='lexicon.Translation', help_text='Original Identity of the phrase within this project', null=True, verbose_name='Original Identity')),
                ('phrase', models.ForeignKey(related_name='projects', verbose_name='Phrase', to='lexicon.Phrase', help_text='Phrase contained in this project')),
                ('project', models.ForeignKey(related_name='phrases', verbose_name='Project', to='project.Project', help_text='Project containing this phrase')),
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
                ('project', models.ForeignKey(related_name='users', verbose_name='Project', to='project.Project', help_text='Project accessed by this user')),
                ('user', models.ForeignKey(related_name='projects', verbose_name='User', to=settings.AUTH_USER_MODEL, help_text='User accessing this project')),
            ],
            options={
                'verbose_name': 'Project User',
                'verbose_name_plural': 'Project Users',
            },
        ),
        migrations.AlterUniqueTogether(
            name='projectuser',
            unique_together=set([('project', 'user')]),
        ),
        migrations.AlterUniqueTogether(
            name='projectphrase',
            unique_together=set([('project', 'phrase'), ('project', 'enum_identity', 'int_identity', 'orig_identity')]),
        ),
    ]
