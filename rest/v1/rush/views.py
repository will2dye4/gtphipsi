from django.shortcuts import get_list_or_404

from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.reverse import reverse

from gtphipsi.chapter.models import InformationCard
from gtphipsi.common import get_rush_or_404
from gtphipsi.rush.models import Potential, Rush, RushEvent
from gtphipsi.rest.v1.permissions import IsAuthenticatedOrWriteOnly
from gtphipsi.rest.v1.rush.permissions import IsAuthenticatedOrCurrentRush
from gtphipsi.rest.v1.rush.serializers import InformationCardSerializer, PledgeSerializer, PotentialSerializer, \
    RushEventSerializer, RushSerializer
from gtphipsi.rest.v1.views import RequestAwareListAPIView, RequestAwareListCreateAPIView, \
    RequestAwareRetrieveAPIView, parse_date, parse_time


class InformationCardList(RequestAwareListCreateAPIView):
    queryset = InformationCard.objects.all()
    serializer_class = InformationCardSerializer
    permission_classes = (IsAuthenticatedOrWriteOnly,)

    def pre_save(self, card):
        data = self.request.DATA
        card.name = data.get('name')
        card.email = data.get('email')
        card.phone = data.get('phone', '')
        card.year = data.get('year')
        card.interests = data.get('interests', '')
        card.relatives = data.get('relatives', '')
        card.subscribe = data.get('subscribe', False)

    def get_location(self, card):
        return reverse('infocard_details', kwargs={'id': card.id}, request=self.request)


class InformationCardDetails(RequestAwareRetrieveAPIView):
    queryset = InformationCard.objects.all()
    serializer_class = InformationCardSerializer
    permission_classes = (IsAuthenticated,)


class RushList(RequestAwareListCreateAPIView):
    queryset = Rush.objects.all()
    serializer_class = RushSerializer
    permission_classes = (IsAuthenticated,)

    def pre_save(self, rush):
        data = self.request.DATA
        rush.season = data.get('season')
        rush.start_date = parse_date(data.get('start_date'))
        rush.end_date = parse_date(data.get('end_date'))
        rush.visible = data.get('visible', True)

    def get_location(self, rush):
        return reverse('rush_details', kwargs={'name': rush.get_unique_name()}, request=self.request)


class RushDetails(RequestAwareRetrieveAPIView):
    queryset = Rush.objects.all()
    serializer_class = RushSerializer
    permission_classes = (IsAuthenticatedOrCurrentRush,)

    def get_instance(self, **kwargs):
        return get_rush_or_404(kwargs['name'])


class CurrentRushDetails(RushDetails):
    permission_classes = (AllowAny,)

    def get_instance(self, **kwargs):
        return Rush.current()


class RushEventList(RequestAwareListCreateAPIView):
    queryset = RushEvent.objects.all()
    serializer_class = RushEventSerializer
    permission_classes = (IsAuthenticatedOrCurrentRush,)

    def get_list(self, **kwargs):
        rush = get_rush_or_404(kwargs['name'])
        return RushEvent.objects.filter(rush=rush)

    def pre_save(self, event):
        data = self.request.DATA
        event.rush = get_rush_or_404(self.request.parser_context['kwargs']['name'])
        event.date = parse_date(data.get('date'))
        event.start = parse_time(data.get('start'))
        event.end = parse_time(data.get('end'))
        event.title = data.get('title')
        event.description = data.get('description', '')
        event.location = data.get('location', '')
        event.link = data.get('link', '')
        event.food = data.get('food', '')

    def get_location(self, event):
        return reverse('rush_event_list', kwargs={'name': event.rush.get_unique_name()}, request=self.request)


class PotentialList(RequestAwareListAPIView):
    queryset = Potential.objects.filter(pledged=False, hidden=False)
    serializer_class = PotentialSerializer
    permission_classes = (IsAuthenticated,)


class PotentialDetails(RequestAwareRetrieveAPIView):
    queryset = Potential.objects.filter(pledged=False, hidden=False)
    serializer_class = PotentialSerializer
    permission_classes = (IsAuthenticated,)


class PledgeList(RequestAwareListAPIView):
    queryset = Potential.objects.filter(pledged=True, hidden=False)
    serializer_class = PledgeSerializer
    permission_classes = (IsAuthenticated,)


class PledgeDetails(RequestAwareRetrieveAPIView):
    queryset = Potential.objects.filter(pledged=True, hidden=False)
    serializer_class = PledgeSerializer
    permission_classes = (IsAuthenticated,)


class RushPotentialList(PotentialDetails):

    def get_instance(self, **kwargs):
        rush = get_rush_or_404(kwargs['name'])
        return get_list_or_404(Potential, pledged=False, hidden=False, rush__id=rush.id)


class RushPledgeList(PledgeDetails):

    def get_instance(self, **kwargs):
        rush = get_rush_or_404(kwargs['name'])
        return get_list_or_404(Potential, pledged=True, hidden=False, rush__id=rush.id)