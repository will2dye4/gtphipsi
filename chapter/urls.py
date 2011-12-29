from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('gtphipsi.chapter.views',
    url(r'^$', 'about', name='about'),
    url(r'^history/$', 'history', name='history'),
    url(r'^creed/$', 'creed', name='creed'),
    url(r'^announcements/$', 'announcements', name='announcements'),
    url(r'^announcements/add/$', 'add_announcement', name='add_announcement'),
    url(r'^announcements/edit/(?P<id>\d+)/$', 'edit_announcement', name='edit_announcement')
)