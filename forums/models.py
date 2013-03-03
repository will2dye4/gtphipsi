from datetime import timedelta

from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse

from gtphipsi.brothers.models import UserProfile


class Forum(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.CharField(max_length=1000, blank=True)
    moderators = models.ManyToManyField(UserProfile, limit_choices_to={'status': 'U'})

    def get_absolute_url(self):
        return reverse('view_forum', kwargs={'slug': self.slug})


class Post(models.Model):
    thread = models.ForeignKey('Thread', related_name='posts')
    user = models.ForeignKey(UserProfile, related_name='posts')
    updated_by = models.ForeignKey(UserProfile, related_name='edited_posts')
    quote = models.ForeignKey('self', related_name='replies', blank=True, null=True)
    number = models.PositiveIntegerField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    body = models.TextField(verbose_name='Message')
    deleted = models.BooleanField(blank=True)

    def get_absolute_url(self):
        if self.number % settings.POSTS_PER_PAGE:
            page = (self.number / settings.POSTS_PER_PAGE) + 1
        else:
            page = (self.number / settings.POSTS_PER_PAGE)
        page_url = reverse('view_thread_page', kwargs={'forum': self.thread.forum.slug, 'id': self.thread.id, 'thread': self.thread.slug, 'page': page})
        return page_url + ('#post_%d' % self.number)

    def is_edited(self):
        return self.updated > (self.created + timedelta(seconds=5))


class Thread(models.Model):
    forum = models.ForeignKey(Forum, related_name='threads')
    owner = models.ForeignKey(UserProfile)
    title = models.CharField(max_length=200)
    slug = models.SlugField()
    updated = models.DateTimeField(auto_now=True)
    subscribers = models.ManyToManyField(UserProfile, blank=True, related_name='subscriptions')

    def get_absolute_url(self):
        return reverse('view_thread', kwargs={'forum': self.forum.slug, 'id': self.id, 'thread': self.slug})

    def latest_post(self):
        if Post.objects.filter(thread=self).count():
            return Post.objects.filter(thread=self).order_by('-created')[0]
        else:
            return None



#class Message(models.Model):
#    public = models.BooleanField(blank=True)
#    sender = models.ForeignKey(UserProfile)
#    recipient = models.ForeignKey(UserProfile)
#    created = models.DateTimeField(auto_now_add=True)
#    subject = models.CharField(max_length=100)
#    body = models.TextField()
#    read = models.BooleanField(blank=True)
