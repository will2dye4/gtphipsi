from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('gtphipsi.officers.views',
    url(r'^$', 'officers', name='show_officers'),
    url(r'^add/$', 'add_officer', name='add_officer'),
    url(r'^history/$', 'officer_history', name='officer_history'),
    url(r'^(?P<office>G?P|VGP|[A|B|S]G|Hod|H[i|M]|Phu|IFC)/edit/$', 'edit_officer', name='edit_officer'),
    url(r'^(?P<office>G?P|VGP|[A|B|S]G|Hod|H[i|M]|Phu|IFC)/history/$', 'office_history', name='office_history'),
)