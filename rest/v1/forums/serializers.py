from rest_framework.fields import IntegerField, SerializerMethodField
from rest_framework.reverse import reverse

from gtphipsi.forums.models import Forum, Post, Thread
from gtphipsi.rest.v1.brothers.serializers import NestedBrotherSerializer
from gtphipsi.rest.v1.serializers import FormattedDates, HrefModelSerializer, HrefPaginationSerializer


class ForumSerializer(HrefModelSerializer):
    threads_href = SerializerMethodField('get_threads_href')
    moderators = SerializerMethodField('get_moderators')
    view_name = 'forum_details'

    def get_threads_href(self, forum):
        threads_href = None
        if forum.threads.count():
            threads_href = reverse('thread_list', kwargs={'id': forum.id}, request=self.request)
        return threads_href

    def get_moderators(self, forum):
        moderators = []
        for mod in forum.moderators.all():
            moderators.append(NestedBrotherSerializer(mod.badge, request=self.request).data)
        return moderators

    class Meta:
        model = Forum
        exclude = ('id', 'slug')

        
class ThreadSerializer(HrefModelSerializer):
    forum_href = SerializerMethodField('get_forum_href')
    posts_href = SerializerMethodField('get_posts_href')
    latest_post_href = SerializerMethodField('get_latest_post_href')
    owner = SerializerMethodField('get_owner')
    subscribers = SerializerMethodField('get_subscribers')
    updated = FormattedDates.new_date_time_field(required=False)
    view_name = 'thread_details'

    def get_forum_href(self, thread):
        return reverse('forum_details', kwargs={'id': thread.forum.id}, request=self.request)

    def get_posts_href(self, thread):
        return reverse('post_list', kwargs={'forum_id': thread.forum.id, 'thread_id': thread.id}, request=self.request)

    def get_latest_post_href(self, thread):
        kwargs = {'forum_id': thread.forum.id, 'thread_id': thread.id, 'post_id': thread.latest_post().id}
        return reverse('post_details', kwargs=kwargs, request=self.request)

    def get_owner(self, thread):
        return NestedBrotherSerializer(thread.owner.badge, request=self.request).data

    def get_subscribers(self, thread):
        subscribers = []
        for subscriber in thread.subscribers.all():
            subscribers.append(NestedBrotherSerializer(subscriber.badge, request=self.request).data)
        return subscribers

    def get_href_kwargs(self, thread):
        return {'forum_id': thread.forum.id, 'thread_id': thread.id}

    class Meta:
        model = Thread
        exclude = ('id', 'forum', 'slug')


class PaginatedThreadSerializer(HrefPaginationSerializer):
    results_field = 'threads'

    class Meta:
        object_serializer_class = HrefPaginationSerializer.get_object_serializer(ThreadSerializer)


class PostSerializer(HrefModelSerializer):
    thread_href = SerializerMethodField('get_thread_href')
    quote_href = SerializerMethodField('get_quote_href')
    number = IntegerField(required=False, default=0)
    user = SerializerMethodField('get_user')
    updated_by = SerializerMethodField('get_updated_by')
    created = FormattedDates.new_date_time_field(required=False)
    updated = FormattedDates.new_date_time_field(required=False)
    view_name = 'post_details'

    def get_thread_href(self, post):
        kwargs = {'forum_id': post.thread.forum.id, 'thread_id': post.thread.id}
        return reverse('thread_details', kwargs=kwargs, request=self.request)

    def get_quote_href(self, post):
        quote_href = None
        if post.quote is not None:
            kwargs = {'forum_id': post.thread.forum.id, 'thread_id': post.thread.id, 'post_id': post.quote.id}
            quote_href = reverse(self.view_name, kwargs=kwargs, request=self.request)
        return quote_href

    def get_user(self, post):
        return NestedBrotherSerializer(post.user.badge, request=self.request).data

    def get_updated_by(self, post):
        updated_by = None
        if post.updated_by.id != post.user.id:
            updated_by = NestedBrotherSerializer(post.updated_by.badge, request=self.request).data
        return updated_by

    def get_href_kwargs(self, post):
        return {'forum_id': post.thread.forum.id, 'thread_id': post.thread.id, 'post_id': post.id}

    class Meta:
        model = Post
        exclude = ('id', 'thread', 'quote')


class PaginatedPostSerializer(HrefPaginationSerializer):
    results_field = 'posts'
    
    class Meta:
        object_serializer_class = HrefPaginationSerializer.get_object_serializer(PostSerializer)
