# Models related to chapter rush and rush events.

from django.db import models
from datetime import datetime

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

    def __unicode__(self):
        return self.title()

    def title(self):
        """Returns the title of this rush, in the format '<Season> Rush <Year>'."""
        return '{0} Rush {1}'.format(self.get_season_display(), self.start_date.year)

    class Meta:
        ordering = ['-start_date']


class RushEvent(models.Model):
    rush = models.ForeignKey(Rush, blank=False)
    title = models.CharField(max_length=100, blank=False)
    description = models.TextField(blank=True)
    start = models.DateTimeField(blank=False, null=True)
    end = models.DateTimeField(blank=False, null=True)
    location = models.CharField(max_length=100, blank=True)
    food = models.CharField(max_length=75, blank=True)

    def __unicode__(self):
        return '{0} - {1}'.format(self.title, self.rush.title())

    def is_future(self):
        """Returns True if the event is in the future or is happening now."""
        return self.end > datetime.now()

    class Meta:
        ordering = ['start']
