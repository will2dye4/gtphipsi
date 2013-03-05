"""Models for the gtphipsi.forums package.

This module exports the following model classes:
    - Forum
    - Post
    - Thread

"""

from datetime import timedelta

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models

from gtphipsi.brothers.models import UserProfile


class Forum(models.Model):

    """A forum, the top level of the forum hierarchy.

    Zero or more threads belong to a forum.

    """

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)    # used in URLs instead of name
    description = models.CharField(max_length=1000, blank=True)
    moderators = models.ManyToManyField(UserProfile, limit_choices_to={'status': 'U'})

    def get_absolute_url(self):
        """Return the absolute URL path for the forum."""
        return reverse('view_forum', kwargs={'slug': self.slug})


class Post(models.Model):

    """A post, the bottom level of the forum hierarchy.

    Every post belongs to a thread. A post may be in reply to a previous post, in which case the previous post is
    accessible through the 'quote' field of the reply post. A post may also be edited by someone other than its
    creator (e.g., a forum moderator), so the 'updated_by' field identifies the user who most recently edited the post.

    If a user deletes a post from a thread, the post's 'deleted' field is set to True, but the post is not actually
    deleted from the database. This is to avoid renumbering all subsequent posts within a thread after deleting a post
    from the middle of the thread. A post is only deleted from the database when its parent thread is deleted.

    """

    thread = models.ForeignKey('Thread', related_name='posts')
    user = models.ForeignKey(UserProfile, related_name='posts')
    updated_by = models.ForeignKey(UserProfile, related_name='edited_posts')
    quote = models.ForeignKey('self', related_name='replies', blank=True, null=True)    # the quoted post, if any
    number = models.PositiveIntegerField()  # the post's number within the thread (the thread's first post is #1)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    body = models.TextField(verbose_name='Message')
    deleted = models.BooleanField(blank=True)   # a post is not deleted from the database until its thread is deleted

    def get_absolute_url(self):
        """Return the absolute URL path for the post."""
        if self.number % settings.POSTS_PER_PAGE:
            page = (self.number / settings.POSTS_PER_PAGE) + 1
        else:
            page = (self.number / settings.POSTS_PER_PAGE)
        page_url = reverse('view_thread_page', kwargs={'forum': self.thread.forum.slug, 'id': self.thread.id, 'thread': self.thread.slug, 'page': page})
        return page_url + ('#post_%d' % self.number)

    def is_edited(self):
        """Return True if the post has been edited, False otherwise."""
        return self.updated > (self.created + timedelta(seconds=5))


class Thread(models.Model):

    """A thread, the middle level of the forum hierarchy.

    Every thread belongs to a forum. One or more posts belong to a thread. A thread's 'owner' is the user who created
    the thread (i.e., the original poster). A thread may have zero or more 'subscribers', users who wish to follow
    the thread and have easy access to it through the 'Subscribed Threads' page.

    """

    forum = models.ForeignKey(Forum, related_name='threads')
    owner = models.ForeignKey(UserProfile)
    title = models.CharField(max_length=200)
    slug = models.SlugField()          # used in URLs instead of name
    updated = models.DateTimeField(auto_now=True)
    subscribers = models.ManyToManyField(UserProfile, blank=True, related_name='subscriptions')

    def get_absolute_url(self):
        """Return the absolute URL path for the thread."""
        return reverse('view_thread', kwargs={'forum': self.forum.slug, 'id': self.id, 'thread': self.slug})

    def latest_post(self):
        """Return the thread's latest post (most recently created, not most recently updated)."""
        return Post.objects.filter(thread=self).order_by('-created')[0]


#class Message(models.Model):
#    public = models.BooleanField(blank=True)
#    sender = models.ForeignKey(UserProfile)
#    recipient = models.ForeignKey(UserProfile)
#    created = models.DateTimeField(auto_now_add=True)
#    subject = models.CharField(max_length=100)
#    body = models.TextField()
#    read = models.BooleanField(blank=True)
