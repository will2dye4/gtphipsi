from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('gtphipsi.rush.views',
    url(r'^$', 'rush', name='rush'),
    url(r'^phipsi/$', 'rushphipsi', name='rushphipsi'),
    url(r'^schedule/$', 'schedule', name='schedule'),
    url(r'^infocard/$', 'info_card', name='info_card'),
    url(r'^infocard/thanks/$', 'info_card_thanks', name='info_card_thanks')
)