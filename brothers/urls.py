from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('gtphipsi.brothers.views',
    url(r'^$', 'list', name='brothers_list'),
)