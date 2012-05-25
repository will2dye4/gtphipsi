from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('gtphipsi.brothers.views',
    url(r'^$', 'list', name='brothers_list'),
    url(r'^manage/$', 'manage', name='manage_users'),
    url(r'^add/$', 'add', name='add_user'),
    url(r'^edit/(?P<id>\d+)/$', 'edit', name='edit_user'),
    url(r'^groups/$', 'manage_groups', name='manage_groups'),
    url(r'^privacy/$', 'visibility', name='visibility'),
    url(r'^privacy/public/$', 'edit_public_visibility', name='edit_public_visibility'),
    url(r'^privacy/chapter/$', 'edit_chapter_visibility', name='edit_chapter_visibility'),
)