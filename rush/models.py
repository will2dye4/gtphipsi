# Models related to chapter rush and rush events.

from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse
from django.forms import ModelForm, TimeField, DateField
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

    def get_absolute_url(self):
        return reverse('view_rush', kwargs={'id': self.id})

    class Meta:
        ordering = ['-start_date']


class RushForm(ModelForm):
    start_date = DateField(input_formats=settings.DATE_INPUT_FORMATS)
    end_date = DateField(input_formats=settings.DATE_INPUT_FORMATS)

    class Meta:
        model = Rush


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


class RushEventForm(ModelForm):
    date = DateField(input_formats=settings.DATE_INPUT_FORMATS)
    start = TimeField(label='Start time', input_formats=settings.TIME_INPUT_FORMATS, error_messages={'invalid': 'Enter a valid time (e.g., 2 PM, 2:30 PM, 14:30, 14:30:59).'})
    end = TimeField(label='End time', input_formats=settings.TIME_INPUT_FORMATS, error_messages={'invalid': 'Enter a valid time (e.g., 2 PM, 2:30 PM, 14:30, 14:30:59).'})

    def clean_date(self):
        rush = self.cleaned_data.get('rush')
        date = self.cleaned_data.get('date')
        if rush is not None and date is not None and (date < rush.start_date or date > rush.end_date):
            self._errors['date'] = self.error_class(['The date is outside the valid range (%s - %s).' % (rush.start_date.strftime('%b %d'), rush.end_date.strftime('%b %d, %Y'))])
            del self.cleaned_data['date']
        return self.cleaned_data['date'] if 'date' in self.cleaned_data else None

    class Meta:
        model = RushEvent
        fields = ('title', 'date', 'start', 'end', 'description', 'location', 'food')