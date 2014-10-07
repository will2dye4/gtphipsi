from django.conf.urls.defaults import patterns, url

from gtphipsi.rest.v1.brothers.views import AlumnusList, BrotherDetails, BrotherList, UndergraduateList


urlpatterns = patterns('gtphipsi.rest.v1.brothers.views',
    url(r'^$', BrotherList.as_view(), name='brother_list'),
    url(r'^alumni/$', AlumnusList.as_view(), name='alumni_list'),
    url(r'^undergrads/$', UndergraduateList.as_view(), name='undergrad_list'),
    url(r'^(?P<badge>\d+)/$', BrotherDetails.as_view(), name='brother_details'),
)
