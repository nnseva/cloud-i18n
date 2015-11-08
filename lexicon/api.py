from __future__ import unicode_literals
from django.utils.translation import ugettext as _ # todo: self-powered version of the translation module


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

class TranslationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Translation
        fields = ('url','language','plural_forms','plural_id','message')

class TranslationViewSet(viewsets.ModelViewSet):
    queryset = models.Translation.objects.all()
    serializer_class = TranslationSerializer

from rest_framework.routers import SimpleRouter

router = SimpleRouter()
router.register(r'phrases', PhraseViewSet)
router.register(r'translations', TranslationViewSet)
