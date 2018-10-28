from django.db import models
from django.forms import ModelForm
from django.core.validators import ValidationError


class Organization(models.Model):
    name = models.CharField(max_length=128, unique=True)
    asn = models.IntegerField(null=True, blank=True, unique=True)
    total_peers = models.IntegerField(null=True, blank=True)
    total_capacity = models.IntegerField(null=True, blank=True)
    total_exchanges = models.IntegerField(null=True, blank=True)
    unique_orgs = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.name


class PeerOrganization(models.Model):
    name = models.CharField(max_length=128, unique=True)
    org = models.ManyToManyField(Organization,
                                 through='Connectivity',
                                 related_name='connections',
                                 through_fields=('peer_name', 'org_name')
                                 )


    def __str__(self):
        return self.name


class Connectivity(models.Model):
    org_name = models.ForeignKey(Organization, on_delete=models.CASCADE)
    peer_name = models.ForeignKey(PeerOrganization, on_delete=models.CASCADE)
    exchange_point = models.CharField(max_length=128, null=True, blank=True)
    connection_count = models.IntegerField(null=True, blank=True)
    capacity = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Connections'

    def __str__(self):
        return f'{self.org_name}:{self.exchange_point}'


class OrganizationForm(ModelForm):
    def clean_name(self):
        if [org.name for org in Organization.objects.all() if self.data['name'] in org.name]:
            raise ValidationError('The name provided has a partial or full match to an existing organization.',
                                  code='invalid',
                                  params={'name': self.data['name']}
                                  )
    class Meta:
        model = Organization
        fields = ['name']
