from django.shortcuts import render, redirect
from execsite.models import OrganizationForm, Organization, PeerOrganization, Connectivity
from prdb_requests.prdb_req import Organization as prdb_org
from utilities.execsite_graphs.es_graphs import sankey_diagram
from django.views.generic.base import TemplateView
from django.http import HttpResponse


def site_view(request):
    """
    Summary view displaying form for query and list of queried sites.
    :param request: object passed from urls
    :return: GET: site.jinja2 template
             POST: query_results.jinja2 template
    """
    if request.method == 'POST':
        form = OrganizationForm(request.POST)
        if form.is_valid():
            org_name = form.cleaned_data['name']
            # Retrieve net information
            org_class = prdb_org(org_name)
            # Retrieve peers, org_metrics, and peer_metrics
            org_class.peer_metrics()
            # Populate Organization Model
            org_record = Organization(name=org_class.org_name)
            org_record.asn = org_class.asn
            org_record.total_peers = org_class.total_peers
            org_record.total_capacity = org_class.total_capacity
            org_record.unique_orgs = org_class.unique_orgs
            org_record.total_exchanges = org_class.total_exchanges
            org_record.save()

            # Populate PeerOrganization Model
            for peer_org in org_class.peer_info:
                for peer_set in org_class.peer_info[peer_org]['peer_sets']:
                    for exchange_point, peer_set_data in peer_set.items():
                        try:
                            PeerOrganization.objects.get(name=peer_org)
                        except PeerOrganization.DoesNotExist:
                            peer_org_record = PeerOrganization(name=peer_org)
                            peer_org_record.save()

                        # Populate Connection Information
                        try:
                            Connectivity.objects.get(
                                org_name=org_record,
                                exchange_point=exchange_point
                            )
                        except Connectivity.DoesNotExist:
                            connection_record = Connectivity(
                                org_name=org_record,
                                peer_name=PeerOrganization.objects.get(name=peer_org)
                            )
                            connection_record.exchange_point = exchange_point
                            connection_record.connection_count = peer_set_data['conn_count']
                            connection_record.capacity = peer_set_data['capacity']
                            connection_record.save()
            return redirect(f'/orgs/{org_record.id}')
        else:
            error = form.errors
            form = OrganizationForm()
            orgs = Organization.objects.all()
            return render(request, 'site.jinja2', {'form': form, 'orgs': orgs, 'error': error})
    form = OrganizationForm()
    orgs = Organization.objects.all()
    return render(request, 'site.jinja2', {'form': form, 'orgs': orgs})


def org_data_view(request, **kwargs):
    """
    Detailed view for organizations.
    :param request: object passed from urls
    :param kwargs: named regex groups from urls
    :return: render query_results.jinja2 template
    """
    org_record = Organization.objects.get(id=kwargs['org_id'])
    peer_org_records = PeerOrganization.objects.filter(org=org_record)
    connection_records = Connectivity.objects.filter(org_name=org_record)
    conn_table = {peer_org:[conn_record for conn_record in connection_records if conn_record.peer_name == peer_org] for peer_org in peer_org_records}
    return render(request, 'query_results.jinja2', {'org_record': org_record, \
                                                    'peer_records': peer_org_records, \
                                                    'conn_records': connection_records, \
                                                    'conn_table': conn_table})


def diagram_view(request, org_ids):
    uniq_orgs = set(org_ids.split('/'))
    org_conn_records = []
    for org in uniq_orgs:
        org_record = Organization.objects.get(id=org)
        connection_record = Connectivity.objects.filter(org_name=org_record)
        org_conn_records.append((org_record, connection_record))
    graph = sankey_diagram(org_conn_records)
    return render(request, 'sankey_diagram.jinja2', {'graph': graph})
