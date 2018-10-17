from django.conf.urls import url
from django.urls import re_path
from execsite.views import site_view, org_data_view, test_view

urlpatterns = [
    url(r'^$',
        site_view,
        name="site_index"),
    url(r'^orgs/(?P<org_id>\d+)/$',
        org_data_view,
        name="organizations"),
    url(r'test/(?P<org_ids>[\d+/]+)/$', test_view)
]