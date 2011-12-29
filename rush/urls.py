from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('gtphipsi.rush.views',
    url(r'^$', 'rush', name='rush'),
    url(r'^phipsi/$', 'rushphipsi', name='rushphipsi'),
    url(r'^schedule/$', 'schedule', name='schedule'),
    url(r'^infocard/$', 'info_card', name='info_card'),
    url(r'^infocard/thanks/$', 'info_card_thanks', name='info_card_thanks'),
    ### authenticated pages ###
    url(r'^list/$', 'list', name='rush_list'),
    url(r'^current/$', 'current', name='current_rush'),
    url(r'^view/(?P<id>\d+)/$', 'show', name='view_rush'),
    url(r'^add/$', 'add', name='add_rush'),
    url(r'^edit/(?P<id>\d+)/$', 'edit', name='edit_rush'),
    url(r'^add-event/(?P<id>\d+)/$', 'add_event', name='add_rush_event'),
    url(r'^edit-event/(?P<id>\d+)/$', 'edit_event', name='edit_rush_event'),
    url(r'^infocards/$', 'info_card_list', name='info_card_list'),
    url(r'^infocards/(?P<id>\d+)/$', 'info_card_show', name='info_card_view')
)