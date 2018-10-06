from django.contrib import admin
from execsite.models import Organization, PeerOrganization, Connectivity


# Register your models here.
admin.site.register(Organization)
admin.site.register(PeerOrganization)
admin.site.register(Connectivity)