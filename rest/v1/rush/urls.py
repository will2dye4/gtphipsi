from django.conf.urls.defaults import patterns, url

from gtphipsi.rest.v1.rush import views


urlpatterns = patterns('gtphipsi.rest.v1.rush.views',
    url(r'^$', views.RushList.as_view(), name='v1_rush_list'),
    url(r'^current/$', views.CurrentRushDetails.as_view(), name='current_rush_details'),
    url(r'^(?P<name>[FSU]\d{4})/$', views.RushDetails.as_view(), name='rush_details'),
    url(r'^(?P<name>[FSU]\d{4})/events/$', views.RushEventList.as_view(), name='rush_event_list'),
    url(r'^(?P<name>[FSU]\d{4})/potentials/$', views.RushPotentialList.as_view(), name='rush_potentials'),
    url(r'^(?P<name>[FSU]\d{4})/pledges/$', views.RushPledgeList.as_view(), name='rush_pledges'),
    url(r'^info-cards/$', views.InformationCardList.as_view(), name='infocard_list'),
    url(r'^info-cards/(?P<id>\d+)/$', views.InformationCardDetails.as_view(), name='infocard_details'),
    url(r'^potentials/$', views.PotentialList.as_view(), name='potential_list'),
    url(r'^potentials/(?P<id>\d+)/$', views.PotentialDetails.as_view(), name='potential_details'),
    url(r'^pledges/$', views.PledgeList.as_view(), name='pledge_list'),
    url(r'^pledges/(?P<id>\d+)/$', views.PledgeDetails.as_view(), name='pledge_details')
)
