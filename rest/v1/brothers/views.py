from django.shortcuts import get_object_or_404

from gtphipsi.brothers.models import UserProfile
from gtphipsi.rest.v1.brothers.serializers import BrotherSerializer, NestedBrotherSerializer
from gtphipsi.rest.v1.views import RequestAwareListAPIView, RequestAwareRetrieveAPIView


class BaseBrotherList(RequestAwareListAPIView):
    serializer_class = NestedBrotherSerializer

    @staticmethod
    def get_badges(queryset):
        return queryset.values_list('badge', flat=True)


class BrotherList(BaseBrotherList):
    queryset = BaseBrotherList.get_badges(UserProfile.objects.all())


class AlumnusList(BaseBrotherList):
    queryset = BaseBrotherList.get_badges(UserProfile.objects.filter(status='A'))


class UndergraduateList(BaseBrotherList):
    queryset = BaseBrotherList.get_badges(UserProfile.objects.filter(status='U'))


class BrotherDetails(RequestAwareRetrieveAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = BrotherSerializer

    def get_instance(self, **kwargs):
        return get_object_or_404(self.get_serializer_class().Meta.model, badge=kwargs['badge'])
