from django.db import models
from django.contrib.localflavor.us.models import PhoneNumberField

class Announcement(models.Model):
    user = models.ForeignKey('brothers.User')
    created = models.DateTimeField(auto_now_add=True, null=True)
    date = models.DateField(blank=True, null=True)
    text = models.CharField(max_length=250, verbose_name='announcement')

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