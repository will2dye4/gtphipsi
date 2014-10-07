from rest_framework.fields import CharField, RegexField, SerializerMethodField

from gtphipsi.chapter.models import Announcement, ContactRecord
from gtphipsi.rest.v1.brothers.serializers import NestedBrotherSerializer
from gtphipsi.rest.v1.serializers import FormattedDates, HrefModelSerializer, HrefPaginationSerializer
from gtphipsi.settings import PHONE_NUMBER_FORMAT


class AnnouncementSerializer(HrefModelSerializer):
    user = SerializerMethodField('get_user')
    date = FormattedDates.new_date_field(required=False)
    created = FormattedDates.new_date_time_field(required=False)
    view_name = 'announcement_details'

    def get_user(self, announcement):
        badge = announcement.user.get_profile().badge
        return NestedBrotherSerializer(badge, request=self.request).data

    class Meta:
        model = Announcement
        exclude = ('id',)


class PaginatedAnnouncementSerializer(HrefPaginationSerializer):
    results_field = 'announcements'

    class Meta:
        object_serializer_class = HrefPaginationSerializer.get_object_serializer(AnnouncementSerializer)

        
class ContactRecordSerializer(HrefModelSerializer):
    name = CharField(max_length=ContactRecord.MAX_NAME_LENGTH)
    phone = RegexField(PHONE_NUMBER_FORMAT, required=False)
    message = CharField(max_length=ContactRecord.MAX_MESSAGE_LENGTH)
    created = FormattedDates.new_date_time_field(required=False)
    view_name = 'contact_details'

    class Meta:
        model = ContactRecord
        exclude = ('id',)
