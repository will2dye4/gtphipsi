# Models related to chapter rush and rush events.

from datetime import datetime

from django.db import models
from django.core.urlresolvers import reverse


SEASON_CHOICES = (
    ('F', 'Fall'),
    ('S', 'Spring'),
    ('U', 'Summer')
)


class Rush(models.Model):
    season = models.CharField(choices=SEASON_CHOICES, max_length=10, blank=False)
    start_date = models.DateField(blank=False, null=True)
    end_date = models.DateField(blank=False, null=True)
    pledges = models.PositiveIntegerField(blank=True, default=0)
    visible = models.BooleanField(default=True)

    @classmethod
    def current(cls):
        queryset = cls.objects.filter(visible=True).order_by('-start_date')
        return queryset[0] if queryset.count() > 0 else None

    def __unicode__(self):
        return self.title()

    def title(self):
        """Returns the title of this rush, in the format '<Season> Rush <Year>'."""
        return '%s Rush %d' % (self.get_season_display(), self.start_date.year)

    def is_current(self):
        return Rush.current() == self

    def get_unique_name(self):
        return '%s%d' % (self.season, self.start_date.year)

    def get_absolute_url(self):
        return reverse('view_rush', kwargs={'name': self.get_unique_name()})

    class Meta:
        ordering = ['-start_date']


class RushEvent(models.Model):
    rush = models.ForeignKey(Rush, blank=False, related_name='events')
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    date = models.DateField(null=True)
    start = models.TimeField(null=True)
    end = models.TimeField(null=True)
    location = models.CharField(max_length=100, blank=True)
    food = models.CharField(max_length=75, blank=True)

    def __unicode__(self):
        return '%s - %s' % (self.title, self.rush.title())

    def is_future(self):
        """Returns True if the event is in the future or is happening now."""
        return self.end > datetime.now()

    class Meta:
        ordering = ['date', 'start']