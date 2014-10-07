from django.shortcuts import get_object_or_404

from rest_framework.permissions import IsAuthenticated

from gtphipsi.officers.models import ChapterOfficer, OfficerHistory
from gtphipsi.rest.v1.officers.serializers import OfficerSerializer, OfficerHistorySerializer
from gtphipsi.rest.v1.views import RequestAwareListAPIView, RequestAwareRetrieveAPIView


class OfficerList(RequestAwareListAPIView):
    queryset = ChapterOfficer.objects.all()
    serializer_class = OfficerSerializer


class OfficerDetails(RequestAwareRetrieveAPIView):
    queryset = ChapterOfficer.objects.all()
    serializer_class = OfficerSerializer

    def get_instance(self, **kwargs):
        return get_object_or_404(self.get_serializer_class().Meta.model, office=kwargs['office'])


class OfficerHistoryList(RequestAwareRetrieveAPIView):
    queryset = OfficerHistory.objects.all()
    serializer_class = OfficerHistorySerializer
    permission_classes = (IsAuthenticated,)

    def get_instance(self, **kwargs):
        return OfficerHistory.objects.filter(office=kwargs['office'])
