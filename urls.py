from django.conf.urls.defaults import patterns, include, url

# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('gtphipsi.views',
    url(r'^$', 'home', name='home'),
    url(r'^login/$', 'login', name='login'),
    url(r'^logout/$', 'logout', name='logout'),
    url(r'^calendar/$', 'calendar', name='calendar')
    # other global pages here
)

urlpatterns += patterns('',
#    url(r'^brothers/', include('gtphipsi.brothers.urls')),
     url(r'^rush/', include('gtphipsi.rush.urls')),
#    url(r'^chapter/', include('gtphipsi.chapter.urls')),
    # other app-specific URLs here
)

# url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
# url(r'^admin/', include(admin.site.urls)),
