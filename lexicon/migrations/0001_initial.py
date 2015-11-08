# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Phrase',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('has_format', models.BooleanField(default=False, help_text='Format parts found in the phrase', verbose_name='Has Format Parts', editable=False)),
                ('has_plural', models.BooleanField(default=False, help_text='Plural form is identified by using plural version of the library call', verbose_name='Has Plural Form')),
            ],
            options={
                'verbose_name': 'Phrase',
                'verbose_name_plural': 'Phrases',
            },
        ),
        migrations.CreateModel(
            name='Translation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('language', models.CharField(help_text="The phrase language in form of two-char or four-char identity like 'en' or 'ru_RU'", max_length=10, verbose_name='Language')),
                ('plural_forms', models.TextField(help_text='The plural forms field value of the gettext file, available only for plural phrase', null=True, verbose_name='Plural Forms', blank=True)),
                ('plural_id', models.IntegerField(help_text='Plural ID if the phrase is plural', null=True, verbose_name='Plural ID', blank=True)),
                ('message', models.TextField(help_text='The phrase message in the particular language', verbose_name='Message', db_index=True)),
                ('phrase', models.ForeignKey(related_name='translations', verbose_name='Phrase', to='lexicon.Phrase', help_text='Phrase identity')),
            ],
            options={
                'verbose_name': 'Translation',
                'verbose_name_plural': 'Translations',
            },
        ),
        migrations.AlterUniqueTogether(
            name='translation',
            unique_together=set([('phrase', 'language', 'plural_id')]),
        ),
    ]
