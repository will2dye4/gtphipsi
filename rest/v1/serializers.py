from rest_framework.fields import DateField, DateTimeField, SerializerMethodField, TimeField
from rest_framework.pagination import PaginationSerializer
from rest_framework.reverse import reverse
from rest_framework.serializers import ModelSerializer

from gtphipsi.settings import API_DATE_INPUT_FORMAT, API_DATE_TIME_INPUT_FORMAT, API_TIME_INPUT_FORMAT


class HrefModelSerializer(ModelSerializer):
    href = SerializerMethodField('get_href')

    def __init__(self, *args, **kwargs):
        if 'request' in kwargs:
            self.request = kwargs['request']
            del kwargs['request']
        else:
            self.request = None
        super(ModelSerializer, self).__init__(*args, **kwargs)

    def is_request_authenticated(self):
        return self.request.user.is_authenticated()

    def get_href(self, obj):
        return reverse(self.view_name, kwargs=self.get_href_kwargs(obj), request=self.request)

    def get_href_kwargs(self, obj):
        return {'id': obj.id}


class HrefPaginationSerializer(PaginationSerializer):

    @staticmethod
    def get_object_serializer(clazz):
        class ProxySerializer(clazz):
            def __init__(self, *args, **kwargs):
                super(HrefModelSerializer, self).__init__(*args, **kwargs)
                self.request = kwargs['context']['request'] if 'context' in kwargs else None
        return ProxySerializer

    def __init__(self, page, *args, **kwargs):
        super(PaginationSerializer, self).__init__(page, *args, **kwargs)
        self.request = kwargs['context']['request'] if 'context' in kwargs else None


class FormattedDates:

    @staticmethod
    def new_date_field(**kwargs):
        return DateField(format=API_DATE_INPUT_FORMAT, input_formats=[API_DATE_INPUT_FORMAT], **kwargs)

    @staticmethod
    def new_date_time_field(**kwargs):
        return DateTimeField(format=API_DATE_TIME_INPUT_FORMAT, input_formats=[API_DATE_TIME_INPUT_FORMAT], **kwargs)

    @staticmethod
    def new_time_field(**kwargs):
        return TimeField(format=API_TIME_INPUT_FORMAT, input_formats=[API_TIME_INPUT_FORMAT], **kwargs)

    def __init__(self):
        pass
