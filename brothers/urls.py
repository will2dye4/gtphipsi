from django.conf.urls.defaults import *

urlpatterns = patterns('gtphipsi.brothers.views',
    url(r'^$', 'list', name='brothers_list'),
    url(r'^(?P<badge>\d+)/$', 'show', name='view_profile'),
    ### authenticated pages ###
    url(r'^profile/$', 'my_profile', name='my_profile'),
    url(r'^manage/$', 'manage', name='manage_users'),
    url(r'^add/$', 'add', name='add_user'),
    url(r'^edit/$', 'edit', name='edit_profile'),
    url(r'^account/$', 'edit_account', name='edit_my_account'),
    url(r'^(?P<badge>\d+)/account/$', 'edit_account', name='edit_account'),
    url(r'^(?P<badge>\d+)/unlock/$', 'unlock', name='unlock_account'),
    url(r'^password/$', 'change_password', name='change_password'),
    url(r'^password/success/$', 'change_password_success', name='change_password_success'),
    url(r'^groups/$', 'manage_groups', name='manage_groups'),
    url(r'^privacy/$', 'visibility', name='visibility'),
    url(r'^privacy/public/$', 'edit_public_visibility', name='edit_public_visibility'),
    url(r'^privacy/chapter/$', 'edit_chapter_visibility', name='edit_chapter_visibility'),
)