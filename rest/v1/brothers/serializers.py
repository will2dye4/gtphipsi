from rest_framework.serializers import CharField, SerializerMethodField, Serializer
from rest_framework.reverse import reverse

from gtphipsi.brothers.models import UserProfile
from gtphipsi.common import get_name_from_badge
from gtphipsi.rest.v1.serializers import HrefModelSerializer
from gtphipsi.settings import API_DATE_INPUT_FORMAT


class NestedBrotherSerializer(Serializer):
    href = SerializerMethodField('get_href')
    name = SerializerMethodField('get_name')
    badge = SerializerMethodField('get_badge')

    def __init__(self, instance, **kwargs):
        super(Serializer, self).__init__(instance)
        self.request = kwargs['request'] if 'request' in kwargs else None

    def get_href(self, badge):
        url = None
        if badge > 0 and UserProfile.objects.filter(badge=badge).exists():
            url = reverse('brother_details', kwargs={'badge': badge}, request=self.request)
        return url

    def get_name(self, badge):
        try:
            return UserProfile.objects.get(badge=badge).common_name()
        except UserProfile.DoesNotExist:
            return get_name_from_badge(badge)

    def get_badge(self, badge):
        return badge


class BrotherSerializer(HrefModelSerializer):
    first_name = SerializerMethodField('get_first_name')
    last_name = SerializerMethodField('get_last_name')
    common_name = CharField(source='common_name', read_only=True)
    full_name = SerializerMethodField('get_full_name')
    preferred_name = CharField(source='preferred_name', read_only=True)
    email = SerializerMethodField('get_email')
    phone = SerializerMethodField('get_phone')
    big_brother = SerializerMethodField('get_big_brother')
    status = CharField(source='get_status_display', read_only=True)
    major = SerializerMethodField('get_major')
    hometown = SerializerMethodField('get_hometown')
    current_city = SerializerMethodField('get_current_city')
    initiation = SerializerMethodField('get_initiation')
    graduation = SerializerMethodField('get_graduation')
    dob = SerializerMethodField('get_dob')
    view_name = 'brother_details'

    _visibility = None

    def _get_visibility(self, profile):
        if self._visibility is None:
            self._visibility = profile.chapter_visibility if self.is_request_authenticated() else profile.public_visibility
        return self._visibility

    def _format_date(self, date):
        return None if date is None else date.strftime(API_DATE_INPUT_FORMAT)

    def get_first_name(self, profile):
        return profile.user.first_name if self._get_visibility(profile).full_name else ''

    def get_last_name(self, profile):
        return profile.user.last_name if self._get_visibility(profile).full_name else ''

    def get_full_name(self, profile):
        return profile.full_name() if self._get_visibility(profile).full_name else ''

    def get_email(self, profile):
        return profile.user.email if self._get_visibility(profile).email else ''

    def get_phone(self, profile):
        return profile.phone if self._get_visibility(profile).phone else ''

    def get_big_brother(self, profile):
        big_brother = None
        if profile.big_brother > 0 and self._get_visibility(profile).big_brother:
            big_brother = NestedBrotherSerializer(profile.big_brother, request=self.request).data
        return big_brother

    def get_major(self, profile):
        major = ''
        if profile.major and self._get_visibility(profile).major:
            major = profile.get_major_display()
        return major

    def get_hometown(self, profile):
        return profile.hometown if self._get_visibility(profile).hometown else ''

    def get_current_city(self, profile):
        return profile.current_city if self._get_visibility(profile).current_city else ''

    def get_initiation(self, profile):
        return self._format_date(profile.initiation) if self._get_visibility(profile).initiation else None

    def get_graduation(self, profile):
        return self._format_date(profile.graduation) if self._get_visibility(profile).graduation else None

    def get_dob(self, profile):
        return self._format_date(profile.dob) if self._get_visibility(profile).dob else None

    def get_href_kwargs(self, profile):
        return {'badge': profile.badge}

    class Meta:
        model = UserProfile
        exclude = ('id', 'user', 'suffix', 'middle_name', 'nickname', 'bits', 'public_visibility', 'chapter_visibility')
