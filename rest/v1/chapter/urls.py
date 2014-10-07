from django.conf.urls.defaults import patterns, url

from gtphipsi.rest.v1.chapter.views import AnnouncementDetails, AnnouncementList, ContactDetails, ContactList, \
    PublicAnnouncementList


urlpatterns = patterns('gtphipsi.rest.v1.chapter.views',
    url(r'^announcements/$', AnnouncementList.as_view(), name='announcement_list'),
    url(r'^announcements/public/$', PublicAnnouncementList.as_view(), name='public_announcement_list'),
    url(r'^announcements/(?P<id>\d+)/$', AnnouncementDetails.as_view(), name='announcement_details'),
    url(r'^contact-records/$', ContactList.as_view(), name='contact_list'),
    url(r'^contact-records/(?P<id>\d+)/$', ContactDetails.as_view(), name='contact_details')
)