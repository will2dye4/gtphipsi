"""Root URL configuration for the gtphipsi web application.

All URIs are routed to this URL configuration, then possibly dispatched to other URL confs in this package's submodules.

"""

from django.conf.urls.defaults import patterns, url, include


# 'Global' pages. These are pages that don't fit neatly into one app (submodule) or another.
urlpatterns = patterns('gtphipsi.views',
    url(r'^$', 'home', name='home'),
    url(r'^login/$', 'sign_in', name='sign_in'),
    url(r'^logout/$', 'sign_out', name='sign_out'),
    url(r'^register/$', 'register', name='register'),
    url(r'^register/success/$', 'register_success', name='register_success'),
    url(r'^calendar/$', 'calendar', name='calendar'),
    url(r'^contact/$', 'contact', name='contact'),
    url(r'^contact/thanks/$', 'contact_thanks', name='contact_thanks'),
    url(r'^forbidden/$', 'forbidden', name='forbidden'),
    url(r'^forgot/$', 'forgot_password', name='forgot_password'),
    url(r'^reset/(?P<id>\d+)/$', 'reset_password', name='reset_password'),
    url(r'^reset/success/$', 'reset_password_success', name='reset_password_success')
)

# Include other URL configurations for app-specific pages.
urlpatterns += patterns('',
     url(r'^brothers/', include('gtphipsi.brothers.urls')),
     url(r'^officers/', include('gtphipsi.officers.urls')),
     url(r'^rush/', include('gtphipsi.rush.urls')),
     url(r'^chapter/', include('gtphipsi.chapter.urls')),
     url(r'^forums/', include('gtphipsi.forums.urls')),
)

# Hack - to continue to support the old rush schedule URI.
urlpatterns += patterns('gtphipsi.rush.views',
    url(r'^rushschedule\.php$', 'old_schedule', name='old_rush_schedule'),
)
