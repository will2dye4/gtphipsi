from django.db import models
from django.contrib.auth.models import User
from django.contrib.localflavor.us.models import PhoneNumberField
from datetime import datetime, timedelta

class Announcement(models.Model):
    user = models.ForeignKey(User)
    created = models.DateTimeField(auto_now_add=True, null=True)
    date = models.DateField(blank=True, null=True)
    text = models.CharField(max_length=250, verbose_name='announcement')

    @classmethod
    def most_recent(cls):
        """Returns the five most recent announcements posted in the past six months."""
        six_months_ago = datetime.now() - timedelta(days=180)
        queryset = cls.objects.filter(created__gte=six_months_ago.strftime('%Y-%m-%d'))[:5]
        return queryset if len(queryset) > 0 else cls.objects.none()

    def __unicode__(self):
        return self.text

    class Meta:
        ordering = ['-created', '-date', 'text']


class ContactRecord(models.Model):
    name = models.CharField(max_length=50)
    email = models.EmailField()
    phone = PhoneNumberField(blank=True)
    message = models.TextField()
    created = models.DateTimeField(auto_now_add=True, null=True)

    def __unicode__(self):
        return 'Contact Request from %s on %s' % (self.name, self.created.strftime('%b %d, %Y'))

    class Meta:
        ordering = ['-created']