from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('gtphipsi.chapter.views',
    url(r'^$', 'about', name='about'),
    url(r'^history/$', 'history', name='history'),
    url(r'^creed/$', 'creed', name='creed'),
)