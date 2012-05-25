from django.conf.urls.defaults import patterns, include, url

# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('gtphipsi.views',
    url(r'^$', 'home', name='home'),
    url(r'^login/$', 'sign_in', name='sign_in'),
    url(r'^logout/$', 'sign_out', name='sign_out'),
    url(r'^register/$', 'register', name='register'),
    url(r'^register/success/$', 'register_success', name='register_success'),
    url(r'^calendar/$', 'calendar', name='calendar'),
    url(r'^contact/$', 'contact', name='contact'),
    url(r'^contact/thanks/$', 'contact_thanks', name='contact_thanks'),
    url(r'^forbidden/$', 'forbidden', name='forbidden')
    # other global pages here
)

urlpatterns += patterns('',
     url(r'^brothers/', include('gtphipsi.brothers.urls')),
     url(r'^rush/', include('gtphipsi.rush.urls')),
     url(r'^chapter/', include('gtphipsi.chapter.urls')),
    # other app-specific URLs here
)

# url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
# url(r'^admin/', include(admin.site.urls)),
