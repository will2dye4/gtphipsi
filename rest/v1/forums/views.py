import re

from django.db.models import Max
from django.shortcuts import get_object_or_404, get_list_or_404
from django.template.defaultfilters import slugify

from rest_framework.exceptions import ParseError
from rest_framework.permissions import IsAuthenticated
from rest_framework.reverse import reverse

from gtphipsi.common import bb_code_escape
from gtphipsi.forums.models import Forum, Post, Thread
from gtphipsi.rest.v1.forums.serializers import ForumSerializer, PaginatedPostSerializer, PaginatedThreadSerializer, \
    PostSerializer, ThreadSerializer
from gtphipsi.rest.v1.views import PaginatedRequestAwareListCreateAPIView, RequestAwareListAPIView, \
    RequestAwareRetrieveAPIView
from gtphipsi.settings import POSTS_PER_PAGE


class ForumList(RequestAwareListAPIView):
    queryset = Forum.objects.all()
    serializer_class = ForumSerializer
    permission_classes = (IsAuthenticated,)


class ForumDetails(RequestAwareRetrieveAPIView):
    queryset = Forum.objects.all()
    serializer_class = ForumSerializer
    permission_classes = (IsAuthenticated,)


class PaginatedThreadList(PaginatedRequestAwareListCreateAPIView):
    queryset = Thread.objects.all()
    serializer_class = ThreadSerializer
    pagination_serializer_class = PaginatedThreadSerializer
    permission_classes = (IsAuthenticated,)

    def get_page_size(self):
        return POSTS_PER_PAGE

    def get_list(self, **kwargs):
        return get_list_or_404(Thread, forum__id=kwargs['id'])

    def pre_save(self, thread):
        data = self.request.DATA
        if 'post' not in data:
            raise ParseError('New thread must contain the body of the first post')
        thread.title = data.get('title')
        thread.slug = slugify(thread.title)
        thread.owner = self.request.user.get_profile()
        thread.forum = Forum.objects.get(id=int(self.request.parser_context['kwargs']['id']))

    def post_save(self, thread, created=False):
        request = self.request
        profile = self.request.user.get_profile()
        thread.subscribers.add(profile)
        thread.save()
        body = bb_code_escape(request.DATA.get('post'))
        post = Post.objects.create(thread=thread, user=profile, updated_by=profile, number=1, deleted=False, body=body)
        post.save()

    def get_location(self, thread):
        kwargs = {'forum_id': thread.forum.id, 'thread_id': thread.id}
        return reverse('thread_details', kwargs=kwargs, request=self.request)


class SubscribedThreadList(PaginatedThreadList):

    def get_list(self, **kwargs):
        return self.request.user.get_profile().subscriptions.all()


class UserThreadList(PaginatedThreadList):

    def get_list(self, **kwargs):
        profile = self.request.user.get_profile()
        return Thread.objects.filter(owner=profile)


class ThreadDetails(RequestAwareRetrieveAPIView):
    queryset = Thread.objects.all()
    serializer_class = ThreadSerializer
    permission_classes = (IsAuthenticated,)

    def get_instance(self, **kwargs):
        return get_object_or_404(self.get_serializer_class().Meta.model, id=kwargs['thread_id'])


class PaginatedPostList(PaginatedRequestAwareListCreateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    pagination_serializer_class = PaginatedPostSerializer
    permission_classes = (IsAuthenticated,)

    _POST_HREF_PATTERN = re.compile(r'.*/posts/(?P<quote_id>\d+)/')

    @staticmethod
    def _get_quote_id_from_href(href):
        match = PaginatedPostList._POST_HREF_PATTERN.match(href)
        return 0 if match is None else int(match.group('quote_id'))

    def get_page_size(self):
        return POSTS_PER_PAGE

    def get_list(self, **kwargs):
        return get_list_or_404(Post, thread__id=kwargs['thread_id'], thread__forum__id=kwargs['forum_id'])

    def pre_save(self, post):
        data = self.request.DATA
        thread = Thread.objects.get(id=int(self.request.parser_context['kwargs']['thread_id']))
        post.body = bb_code_escape(data.get('body'))
        if 'quote_href' in data:
            quote_id = PaginatedPostList._get_quote_id_from_href(data.get('quote_href'))
            try:
                post.quote = Post.objects.get(thread=thread, id=quote_id)
            except Post.DoesNotExist:
                raise ParseError('Invalid quote href')

        post.deleted = False
        post.thread = thread
        post.user = self.request.user.get_profile()
        post.updated_by = post.user
        last_post = Post.objects.filter(thread=thread).aggregate(last_post=Max('number'))['last_post']
        post.number = last_post + 1

    def get_location(self, post):
        kwargs = {'forum_id': post.thread.forum.id, 'thread_id': post.thread.id, 'post_id': post.id}
        return reverse('post_details', kwargs=kwargs, request=self.request)


class PostDetails(RequestAwareRetrieveAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = (IsAuthenticated,)

    def get_instance(self, **kwargs):
        return get_object_or_404(self.get_serializer_class().Meta.model, id=kwargs['post_id'])
