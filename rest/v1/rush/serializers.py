from rest_framework.fields import CharField, RegexField, SerializerMethodField
from rest_framework.reverse import reverse

from gtphipsi.chapter.models import ContactRecord, InformationCard
from gtphipsi.rush.models import Rush, RushEvent, Potential
from gtphipsi.rest.v1.serializers import FormattedDates, HrefModelSerializer
from gtphipsi.settings import PHONE_NUMBER_FORMAT


class InformationCardSerializer(HrefModelSerializer):
    name = CharField(max_length=ContactRecord.MAX_NAME_LENGTH)
    phone = RegexField(PHONE_NUMBER_FORMAT, required=False)
    year = CharField(source='get_year_display')
    interests = CharField(max_length=InformationCard.MAX_INTERESTS_LENGTH, required=False)
    relatives = CharField(max_length=InformationCard.MAX_RELATIVES_LENGTH, required=False)
    created = FormattedDates.new_date_time_field(required=False)
    view_name = 'infocard_details'

    class Meta:
        model = InformationCard
        exclude = ('id', 'message')


class RushSerializer(HrefModelSerializer):
    events_href = SerializerMethodField('get_events_href')
    pledges_href = SerializerMethodField('get_pledges_href')
    potentials_href = SerializerMethodField('get_potentials_href')
    season = CharField(source='get_season_display', read_only=True)
    start_date = FormattedDates.new_date_field()
    end_date = FormattedDates.new_date_field()
    updated = FormattedDates.new_date_time_field(required=False)
    view_name = 'rush_details'

    def get_events_href(self, rush):
        href = None
        if rush.events.count():
            href = reverse('rush_event_list', kwargs={'name': rush.get_unique_name()}, request=self.request)
        return href

    def get_pledges_href(self, rush):
        href = None
        if self.is_request_authenticated() and rush.potentials.filter(pledged=True).count():
            href = reverse('rush_pledges', kwargs={'name': rush.get_unique_name()}, request=self.request)
        return href

    def get_potentials_href(self, rush):
        href = None
        if self.is_request_authenticated() and rush.potentials.filter(pledged=False).count():
            href = reverse('rush_potentials', kwargs={'name': rush.get_unique_name()}, request=self.request)
        return href

    def get_href_kwargs(self, rush):
        return {'name': rush.get_unique_name()}

    class Meta:
        model = Rush
        exclude = ('id',)


class RushEventSerializer(HrefModelSerializer):
    rush_href = SerializerMethodField('get_rush_href')
    date = FormattedDates.new_date_field()
    start = FormattedDates.new_time_field()
    end = FormattedDates.new_time_field()

    def get_rush_href(self, rush_event):
        return reverse('rush_details', kwargs={'name': rush_event.rush.get_unique_name()}, request=self.request)

    class Meta:
        model = RushEvent
        exclude = ('id', 'href', 'rush')


class PotentialSerializer(HrefModelSerializer):
    rush_href = SerializerMethodField('get_rush_href')
    created = FormattedDates.new_date_time_field(required=False)
    view_name = 'potential_details'

    def get_rush_href(self, potential):
        href = None
        if potential.rush is not None:
            href = reverse('rush_details', kwargs={'name': potential.rush.get_unique_name()}, request=self.request)
        return href

    class Meta:
        model = Potential
        exclude = ('id', 'pledged', 'hidden', 'rush')


class PledgeSerializer(PotentialSerializer):
    view_name = 'pledge_details'
