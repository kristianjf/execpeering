from django.conf.urls import url
from execsite.views import site_view, org_data_view

urlpatterns = [
    url(r'^$',
        site_view,
        name="site_index"),
    url(r'^orgs/(?P<org_id>\d+)/$',
        org_data_view,
        name="organizations")
]