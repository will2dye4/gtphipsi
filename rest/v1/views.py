from datetime import datetime

from django.core.paginator import PageNotAnInteger, EmptyPage, Paginator
from django.shortcuts import get_object_or_404

from rest_framework.generics import ListAPIView, ListCreateAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST

from gtphipsi.settings import API_DATE_INPUT_FORMAT, API_TIME_INPUT_FORMAT


class RequestAwareListAPIView(ListAPIView):

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer_class()(self.get_list(**kwargs), request=request)
        return Response(serializer.data)

    def get_list(self, **kwargs):
        return self.get_queryset()


class PaginatedRequestAwareListAPIView(RequestAwareListAPIView):

    def list(self, request, *args, **kwargs):
        page = self._get_page_from_request(request, **kwargs)
        serializer = self.pagination_serializer_class(page, context={'request': request})
        return Response(serializer.data)

    def get_page_size(self):
        pass

    def _get_page_from_request(self, request, **kwargs):
        paginator = Paginator(self.get_list(**kwargs), self.get_page_size())
        page_num = request.QUERY_PARAMS.get('page')
        try:
            page = paginator.page(page_num)
        except (TypeError, PageNotAnInteger):
            page = paginator.page(1)
        except EmptyPage:
            page = paginator.page(paginator.num_pages)
        return page


class RequestAwareListCreateAPIView(ListCreateAPIView):

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer_class()(self.get_list(**kwargs), request=request)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer_class()(data=request.DATA, request=request)
        if serializer.is_valid():
            obj = self.get_serializer_class().Meta.model()
            self.pre_save(obj)
            obj.save(force_insert=True)
            self.post_save(obj, True)
            return self.get_created_response(obj)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def get_list(self, **kwargs):
        return self.get_queryset()

    def get_location(self, obj):
        pass

    def get_created_response(self, obj):
        serializer = self.get_serializer_class()(obj, request=self.request)
        return Response(serializer.data, status=HTTP_201_CREATED, headers={'Location': self.get_location(obj)})


class PaginatedRequestAwareListCreateAPIView(RequestAwareListCreateAPIView):

    def list(self, request, *args, **kwargs):
        page = self._get_page_from_request(request, **kwargs)
        serializer = self.pagination_serializer_class(page, context={'request': request})
        return Response(serializer.data)

    def get_page_size(self):
        pass

    def _get_page_from_request(self, request, **kwargs):
        paginator = Paginator(self.get_list(**kwargs), self.get_page_size())
        page_num = request.QUERY_PARAMS.get('page')
        try:
            page = paginator.page(page_num)
        except (TypeError, PageNotAnInteger):
            page = paginator.page(1)
        except EmptyPage:
            page = paginator.page(paginator.num_pages)
        return page


class RequestAwareRetrieveAPIView(RetrieveAPIView):

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer_class()(self.get_instance(**kwargs), request=request)
        return Response(serializer.data)

    def get_instance(self, **kwargs):
        return get_object_or_404(self.get_serializer_class().Meta.model, id=kwargs['id'])


def parse_date(date_string):
    return datetime.strptime(date_string, API_DATE_INPUT_FORMAT).date()


def parse_time(time_string):
    return datetime.strptime(time_string, API_TIME_INPUT_FORMAT).time()