from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('gtphipsi.forums.views',
    url(r'^$', 'forums', name='forums'),
    url(r'^add/$', 'add_forum', name='add_forum'),
    url(r'^subscriptions/$', 'subscriptions', name='subscribed_threads'),
    url(r'^(?P<slug>[a-zA-Z0-9\-]+)/$', 'view_forum', name='view_forum'),
    url(r'^(?P<slug>[a-zA-Z0-9\-]+)/edit/$', 'edit_forum', name='edit_forum'),
    url(r'^(?P<slug>[a-zA-Z0-9\-]+)/new-thread/$', 'add_thread', name='add_thread'),
    url(r'^(?P<forum>[a-zA-Z0-9\-]+)/(?P<id>\d+)/(?P<thread>[a-zA-Z0-9\-]+)/$', 'view_thread', name='view_thread'),
    url(r'^(?P<forum>[a-zA-Z0-9\-]+)/(?P<id>\d+)/(?P<thread>[a-zA-Z0-9\-]+)/(?P<page>\d+)/$', 'view_thread', name='view_thread_page'),
    url(r'^(?P<forum>[a-zA-Z0-9\-]+)/(?P<id>\d+)/(?P<thread>[a-zA-Z0-9\-]+)/edit/$', 'edit_thread', name='edit_thread'),
    url(r'^(?P<forum>[a-zA-Z0-9\-]+)/(?P<id>\d+)/(?P<thread>[a-zA-Z0-9\-]+)/reply/$', 'add_post', name='add_post'),
    url(r'^edit-post/(?P<id>\d+)/$', 'edit_post', name='edit_post'),
)