from rest_framework.fields import SerializerMethodField, CharField
from rest_framework.reverse import reverse

from gtphipsi.officers.models import ChapterOfficer, OfficerHistory
from gtphipsi.rest.v1.brothers.serializers import NestedBrotherSerializer
from gtphipsi.rest.v1.serializers import FormattedDates, HrefModelSerializer


class OfficerSerializer(HrefModelSerializer):
    brother = SerializerMethodField('get_brother')
    history = SerializerMethodField('get_history')
    title = CharField(source='get_office_display', read_only=True)
    updated = FormattedDates.new_date_field(required=False)
    view_name = 'officer_details'

    def get_brother(self, officer):
        return NestedBrotherSerializer(officer.brother.badge, request=self.request).data

    def get_history(self, officer):
        history = None
        if OfficerHistory.objects.filter(office=officer.office).exists() and self.is_request_authenticated():
            history = reverse('officer_history', kwargs={'office': officer.office}, request=self.request)
        return history

    def get_href_kwargs(self, officer):
        return {'office': officer.office}

    class Meta:
        model = ChapterOfficer
        exclude = ('id',)


class OfficerHistorySerializer(HrefModelSerializer):
    brother = SerializerMethodField('get_brother')
    start = FormattedDates.new_date_field()
    end = FormattedDates.new_date_field()
    view_name = 'officer_history'

    def get_brother(self, officer_history):
        return NestedBrotherSerializer(officer_history.brother.badge, request=self.request).data

    def get_href_kwargs(self, officer_history):
        return {'office': officer_history.office}

    class Meta:
        model = OfficerHistory
        exclude = ('id',)