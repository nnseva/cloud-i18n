from __future__ import unicode_literals
from django.utils.translation import ugettext_lazy as _ # todo: self-powered version of the translation module

from rest_framework import viewsets
from rest_framework import serializers

from . import models

class PhraseSerializer(serializers.HyperlinkedModelSerializer):
    translations = serializers.HyperlinkedRelatedField(many=True, queryset=models.Translation.objects.all(), view_name='translation-detail')

    class Meta:
        model = models.Phrase
        fields = ('url', 'has_format','has_plural', 'translations')

class PhraseViewSet(viewsets.ModelViewSet):
    queryset = models.Phrase.objects.all()
    serializer_class = PhraseSerializer
    filter_fields = ('has_format', 'has_plural','translations__language')

class TranslationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Translation
        fields = ('url','language','plural_forms','plural_id','message','phrase')

class TranslationViewSet(viewsets.ModelViewSet):
    queryset = models.Translation.objects.all()
    serializer_class = TranslationSerializer
    filter_fields = ('language','plural_forms','plural_id','message')
