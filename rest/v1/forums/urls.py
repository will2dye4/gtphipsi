from django.conf.urls.defaults import patterns, url

from gtphipsi.rest.v1.forums.views import ForumDetails, ForumList, PaginatedPostList, PaginatedThreadList, \
    PostDetails, SubscribedThreadList, ThreadDetails, UserThreadList


urlpatterns = patterns('gtphipsi.rest.v1.forums.views',
    url(r'^$', ForumList.as_view(), name='forum_list'),
    url(r'^subscriptions/$', SubscribedThreadList.as_view(), name='subscribed_thread_list'),
    url(r'^my-threads/$', UserThreadList.as_view(), name='user_thread_list'),
    url(r'^(?P<id>\d+)/$', ForumDetails.as_view(), name='forum_details'),
    url(r'^(?P<id>\d+)/threads/$', PaginatedThreadList.as_view(), name='thread_list'),
    url(r'^(?P<forum_id>\d+)/threads/(?P<thread_id>\d+)/$', ThreadDetails.as_view(), name='thread_details'),
    url(r'^(?P<forum_id>\d+)/threads/(?P<thread_id>\d+)/posts/$', PaginatedPostList.as_view(), name='post_list'),
    url(r'^(?P<forum_id>\d+)/threads/(?P<thread_id>\d+)/posts/(?P<post_id>\d+)/$', PostDetails.as_view(), name='post_details')
)