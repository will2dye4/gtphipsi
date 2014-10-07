from django.conf.urls.defaults import patterns, url
from rest.v1.officers.views import OfficerDetails, OfficerList, OfficerHistoryList


urlpatterns = patterns('gtphipsi.rest.v1.officers.views',
    url(r'^$', OfficerList.as_view(), name='officer_list'),
    url(r'^(?P<office>G?P|VGP|[A|B|S]G|Hod|H[i|M]|Phu|IFC)/$', OfficerDetails.as_view(), name='officer_details'),
    url(r'^(?P<office>G?P|VGP|[A|B|S]G|Hod|H[i|M]|Phu|IFC)/history/$', OfficerHistoryList.as_view(), name='officer_history')
)