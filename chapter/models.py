"""Models for the gtphipsi.chapter package.

This module exports the following model classes:
    - Announcement
    - ContactRecord
    - InformationCard

This module exports the following tuple of field choices:
    - YEAR_CHOICES

"""

from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.contrib.localflavor.us.models import PhoneNumberField
from django.core.urlresolvers import reverse
from django.core.validators import MaxLengthValidator
from django.db import models


# Possible 'years' in college (based on academic standing).
YEAR_CHOICES = (
    ('IF', 'Incoming Freshman'),
    ('FR', 'Freshman'),
    ('SO', 'Sophomore'),
    ('JR', 'Junior'),
    ('SR', 'Senior'),
    ('GR', 'Graduate Student'),
)


class Announcement(models.Model):
    """An announcement posted by a user, either publicly to everyone who visits the site or just to other members."""

    user = models.ForeignKey(User, related_name='announcements')
    created = models.DateTimeField(auto_now_add=True, null=True)
    date = models.DateField(blank=True, null=True)
    text = models.CharField(max_length=250, verbose_name='announcement')
    public = models.BooleanField(default=True, help_text='Deselect to make this announcement only visible to brothers.')

    @classmethod
    def most_recent(cls, public=True):
        """Return the five most recent announcements posted in the past six months.

        Optional parameters:
            - public    =>  whether to include only public announcements (as a boolean): defaults to public only

        """
        six_months_ago = datetime.now() - timedelta(days=180)
        if public:
            queryset = cls.objects.filter(public=True).filter(created__gte=six_months_ago.strftime('%Y-%m-%d'))[:5]
        else:
            queryset = cls.objects.filter(created__gte=six_months_ago.strftime('%Y-%m-%d'))[:5]
        return queryset if queryset.count() > 0 else cls.objects.none()

    def __unicode__(self):
        """Return a Unicode string representation of the announcement."""
        return unicode(self.text)

    class Meta:
        """Define a default sort by date created descending, then by date descending, then by text ascending."""
        ordering = ['-created', '-date', 'text']


class ContactRecord(models.Model):
    """A contact record, used by nonmembers to contact the chapter."""

    name = models.CharField(max_length=50)
    email = models.EmailField()
    phone = PhoneNumberField(blank=True, help_text="XXX-XXX-XXXX")
    message = models.TextField(default='--', validators=[MaxLengthValidator(500)])
    created = models.DateTimeField(auto_now_add=True, null=True)

    def __unicode__(self):
        """Return a Unicode string representation of the contact record."""
        return u'Contact Request from %s on %s' % (self.name, self.created.strftime('%b %d, %Y'))

    def to_string(self):
        """Return a string representation of the contact record."""
        return 'Name: %s\nEmail: %s\nMessage: %s' % (self.name, self.email, self.message)

    class Meta:
        """Define a default sort by date created descending (most recent first)."""
        ordering = ['-created']


class InformationCard(ContactRecord):
    """An information card, used by potential members to provide information about themselves to the chapter."""

    year = models.CharField(choices=YEAR_CHOICES, max_length=3)
    interests = models.CharField(max_length=150, blank=True)
    relatives = models.CharField(max_length=150, blank=True, verbose_name="Phi Psi Relatives",
                                 help_text="If any, please include chapter and year.")
    subscribe = models.BooleanField(default=False, help_text="Get updates on the chapter's activities.")

    @classmethod
    def all_subscriber_emails(cls):
        """Return a list of the email addresses from all information cards having 'subscribe' set to True."""
        return cls.objects.filter(subscribe=True).distinct().values_list('email', flat=True)

    def __unicode__(self):
        """Return a Unicode string representation of the information card."""
        return u'Information Card from %s on %s' % (self.name, self.created.strftime('%b %d, %Y'))

    def get_absolute_url(self):
        """Return the absolute URL path for the information card."""
        return reverse('info_card_view', kwargs={'id': self.id})

    def to_string(self):
        """Return a string representation of the information card."""
        str = 'Name: %s\nEmail: %s\nYear: %s' % (self.name, self.email, self.get_year_display())
        if self.phone:
            str += '\nPhone: %s' % self.phone
        if self.interests:
            str += '\nInterests: %s' % self.interests
        if self.relatives:
            str += '\nRelatives: %s' % self.relatives
        return str

    class Meta:
        """Define a default sort by date created descending (most recent first)."""
        ordering = ['-created']