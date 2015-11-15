from django.conf import settings
from django.contrib.auth.models import *

def user_admin_enable(user, *av, **kw):
    if not user.is_staff:
        user.is_staff = True
        user.save()
    if not user.groups.all():
        groups = Group.objects.filter(name__in=getattr(settings,'USER_REGISTERED_GROUPS',[]))
        if groups:
            user.groups.add(*groups)