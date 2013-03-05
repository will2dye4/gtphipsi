"""URL configuration for the gtphipsi.chapter package.

All URIs beginning with '/chapter/' are routed to this URL configuration.

"""

from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('gtphipsi.chapter.views',
    ## ============================================= ##
    ##                 Public Pages                  ##
    ## ============================================= ##
    url(r'^$', 'about', name='about'),
    url(r'^history/$', 'history', name='history'),
    url(r'^creed/$', 'creed', name='creed'),
    url(r'^announcements/$', 'announcements', name='announcements'),

    ## ============================================= ##
    ##              Authenticated Pages              ##
    ## ============================================= ##
    url(r'^announcements/add/$', 'add_announcement', name='add_announcement'),
    url(r'^announcements/edit/(?P<id>\d+)/$', 'edit_announcement', name='edit_announcement')
)