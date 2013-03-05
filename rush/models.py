"""Models for the gtphipsi.rush package.

This module exports the following model classes:
    - Rush
    - RushEvent
    - Potential

This module exports the following tuples of field choices:
    - SEASON_CHOICES

"""

from datetime import datetime

from django.contrib.localflavor.us.models import PhoneNumberField
from django.core.urlresolvers import reverse
from django.db import models


# Academic seasons at Georgia Tech.
SEASON_CHOICES = (
    ('F', 'Fall'),
    ('S', 'Spring'),
    ('U', 'Summer')
)


class Rush(models.Model):
    """An entire rush (i.e., IFC coordinated rush week)."""

    season = models.CharField(choices=SEASON_CHOICES, max_length=1)
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    visible = models.BooleanField(blank=True, default=True)
    updated = models.DateTimeField(auto_now=True)

    @classmethod
    def current(cls):
        """Return the most recent rush instance that has been marked as 'visible'."""
        queryset = cls.objects.filter(visible=True).order_by('-start_date')
        return queryset[0] if queryset.count() > 0 else None

    def __unicode__(self):
        """Return a Unicode string representation of the rush."""
        return unicode(self.title())

    def title(self):
        """Return the title of the rush, in the format '<season> Rush <year>' (e.g., 'Spring Rush 1852')."""
        return '%s Rush %d' % (self.get_season_display(), self.start_date.year)

    def is_current(self):
        """Return True if the rush is the most recent visible rush, False otherwise."""
        return Rush.current() == self

    def get_unique_name(self):
        """Return a unique name for the rush (used in URLs)."""
        return '%s%d' % (self.season, self.start_date.year)

    def get_absolute_url(self):
        """Return the absolute URL path for the rush."""
        return reverse('view_rush', kwargs={'name': self.get_unique_name()})

    class Meta:
        """Define a default sort of start date descending (most recent first)."""
        ordering = ['-start_date']


class RushEvent(models.Model):
    """A single rush event associated with a rush instance."""

    rush = models.ForeignKey(Rush, related_name='events')
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    date = models.DateField(null=True)
    start = models.TimeField(null=True)
    end = models.TimeField(null=True)
    location = models.CharField(max_length=100, blank=True)
    food = models.CharField(max_length=75, blank=True)

    def __unicode__(self):
        """Return a Unicode string representation of the rush event."""
        return u'%s - %s' % (self.title, self.rush.title())

    def get_absolute_url(self):
        """Return the absolute URL path to the rush event, which is actually the path to the event's rush."""
        return self.rush.get_absolute_url()

    def is_future(self):
        """Return True if the event is in the future or is happening now, False otherwise."""
        return self.end > datetime.now()

    class Meta:
        """Define a default sort of date ascending, then start time ascending."""
        ordering = ['date', 'start']


class Potential(models.Model):
    """Information about a potential member or pledge."""

    rush = models.ForeignKey(Rush, related_name='potentials', blank=True, null=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    phone = PhoneNumberField(blank=True)
    email = models.EmailField(blank=True)
    notes = models.TextField(blank=True)
    hidden = models.BooleanField(blank=True)
    pledged = models.BooleanField(blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def get_absolute_url(self):
        if self.pledged:
            path = reverse('show_pledge', kwargs={'id': self.id})
        else:
            path = reverse('show_potential', kwargs={'id': self.id})
        return path
