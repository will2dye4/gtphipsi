from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('gtphipsi.rush.views',
    url(r'^$', 'rush', name='rush'),
    url(r'^phipsi/$', 'rushphipsi', name='rushphipsi'),
    url(r'^schedule/$', 'schedule', name='schedule'),
    url(r'^infocard/$', 'info_card', name='info_card'),
    url(r'^infocard/thanks/$', 'info_card_thanks', name='info_card_thanks'),
    ### authenticated pages ###
    url(r'^list/$', 'list', name='rush_list'),
    url(r'^add/$', 'add', name='add_rush'),
    url(r'^current/$', 'show', name='current_rush'),
    url(r'^(?P<name>[FSU]\d{4})/$', 'show', name='view_rush'),
    url(r'^(?P<name>[FSU]\d{4})/edit/$', 'edit', name='edit_rush'),
    url(r'^(?P<name>[FSU]\d{4})/add-event/$', 'add_event', name='add_rush_event'),
    url(r'^edit-event/(?P<id>\d+)/$', 'edit_event', name='edit_rush_event'),
    url(r'^infocards/$', 'info_card_list', name='info_card_list'),
    url(r'^infocards/(?P<id>\d+)/$', 'info_card_show', name='info_card_view')
)