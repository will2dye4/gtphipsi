from rest_framework.permissions import IsAuthenticated
from rest_framework.reverse import reverse

from gtphipsi.chapter.models import Announcement, ContactRecord
from gtphipsi.rest.v1.chapter.serializers import AnnouncementSerializer, ContactRecordSerializer, \
    PaginatedAnnouncementSerializer
from gtphipsi.rest.v1.permissions import IsAuthenticatedOrWriteOnly
from gtphipsi.rest.v1.views import PaginatedRequestAwareListAPIView, PaginatedRequestAwareListCreateAPIView, \
   RequestAwareListCreateAPIView, RequestAwareRetrieveAPIView, parse_date
from gtphipsi.settings import ANNOUNCEMENTS_PER_PAGE


class AnnouncementList(PaginatedRequestAwareListCreateAPIView):
    queryset = Announcement.objects.all()
    serializer_class = AnnouncementSerializer
    pagination_serializer_class = PaginatedAnnouncementSerializer
    permission_classes = (IsAuthenticated,)

    def get_page_size(self):
        return ANNOUNCEMENTS_PER_PAGE

    def pre_save(self, announcement):
        data = self.request.DATA
        announcement.date = parse_date(data.get('date', None))
        announcement.text = data.get('text')
        announcement.public = data.get('public', True)
        announcement.user = self.request.user

    def get_location(self, announcement):
        return reverse('announcement_details', kwargs={'id': announcement.id}, request=self.request)


class PublicAnnouncementList(PaginatedRequestAwareListAPIView):
    queryset = Announcement.objects.filter(public=True)
    serializer_class = AnnouncementSerializer
    pagination_serializer_class = PaginatedAnnouncementSerializer

    def get_page_size(self):
        return ANNOUNCEMENTS_PER_PAGE


class AnnouncementDetails(RequestAwareRetrieveAPIView):
    queryset = Announcement.objects.all()
    serializer_class = AnnouncementSerializer


class ContactList(RequestAwareListCreateAPIView):
    queryset = ContactRecord.objects.all()
    serializer_class = ContactRecordSerializer
    permission_classes = (IsAuthenticatedOrWriteOnly,)

    def pre_save(self, contact):
        data = self.request.DATA
        contact.name = data.get('name')
        contact.email = data.get('email')
        contact.phone = data.get('phone', '')
        contact.message = data.get('message')

    def get_location(self, contact):
        return reverse('contact_details', kwargs={'id': contact.id}, request=self.request)


class ContactDetails(RequestAwareRetrieveAPIView):
    queryset = Announcement.objects.all()
    serializer_class = ContactRecordSerializer
    permission_classes = (IsAuthenticated,)
