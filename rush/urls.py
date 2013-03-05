"""URL configuration for the gtphipsi.rush package.

All URIs beginning with '/rush/' are routed to this URL configuration.

"""

from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('gtphipsi.rush.views',
    ## ============================================= ##
    ##                 Public Pages                  ##
    ## ============================================= ##
    url(r'^$', 'rush', name='rush'),
    url(r'^phi-psi/$', 'rush_phi_psi', name='rush_phi_psi'),
    url(r'^schedule/$', 'schedule', name='rush_schedule'),
    url(r'^info-card/$', 'info_card', name='info_card'),
    url(r'^info-card/thanks/$', 'info_card_thanks', name='info_card_thanks'),

    ## ============================================= ##
    ##              Authenticated Pages              ##
    ## ============================================= ##
    url(r'^list/$', 'list', name='rush_list'),
    url(r'^add/$', 'add', name='add_rush'),
    url(r'^current/$', 'show', name='current_rush'),
    url(r'^edit-event/(?P<id>\d+)/$', 'edit_event', name='edit_rush_event'),
    url(r'^info-cards/$', 'info_card_list', name='info_card_list'),
    url(r'^info-cards/(?P<id>\d+)/$', 'info_card_show', name='info_card_view'),
    url(r'^potentials/$', 'potentials', name='all_potentials'),
    url(r'^potentials/add/$', 'add_potential', name='add_potential'),
    url(r'^potentials/(?P<id>\d+)/$', 'show_potential', name='show_potential'),
    url(r'^potentials/(?P<id>\d+)/edit/$', 'edit_potential', name='edit_potential'),
    url(r'^potentials/update/$', 'update_potentials', name='update_potentials'),
    url(r'^pledges/$', 'pledges', name='all_pledges'),
    url(r'^pledges/add/$', 'add_pledge', name='add_pledge'),
    url(r'^pledges/(?P<id>\d+)/$', 'show_pledge', name='show_pledge'),
    url(r'^pledges/(?P<id>\d+)/edit/$', 'edit_pledge', name='edit_pledge'),
    url(r'^(?P<name>[FSU]\d{4})/$', 'show', name='view_rush'),
    url(r'^(?P<name>[FSU]\d{4})/edit/$', 'edit', name='edit_rush'),
    url(r'^(?P<name>[FSU]\d{4})/add-event/$', 'add_event', name='add_rush_event'),
    url(r'^(?P<name>[FSU]\d{4})/potentials/$', 'potentials', name='potentials'),
    url(r'^(?P<name>[FSU]\d{4})/potentials/add/$', 'add_potential', name='add_rush_potential'),
    url(r'^(?P<name>[FSU]\d{4})/potentials/update/$', 'update_potentials', name='update_rush_potentials'),
    url(r'^(?P<name>[FSU]\d{4})/pledges/$', 'pledges', name='pledges'),
    url(r'^(?P<name>[FSU]\d{4})/pledges/add/$', 'add_pledge', name='add_rush_pledge')
)
