from django.conf import settings

from social.backends.utils import *
from urlparse import urlparse, urlunparse

def backend_descriptor(b):
    icon = ''
    au = getattr(b,'AUTHORIZATION_URL',None)
    if au:
        url = urlparse(au)
        icon = urlunparse((url[0],url[1],'favicon.ico','','',''))

    return getattr(settings,'SOCIAL_BACKEND_DESCRIPTORS',{}).get(b.name,{
        'verbose_name': ' '.join([n.capitalize() for n in b.name.split('-') if not n.startswith('oauth')]),
        'name': b.name,
        'icon': icon
    })
    
def social_backends(request):
    available = load_backends(getattr(settings,'AUTHENTICATION_BACKENDS',()))
    return {'social_backends': [ backend_descriptor(available[k]) for k in available ] }