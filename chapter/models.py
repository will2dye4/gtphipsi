from django.db import models
from django.forms import ModelForm
from django.core.validators import MaxLengthValidator
from django.contrib.auth.models import User
from django.contrib.localflavor.us.models import PhoneNumberField
from datetime import datetime, timedelta

YEAR_CHOICES = (
    ('IF', 'Incoming Freshman'),
    ('FR', 'Freshman'),
    ('SO', 'Sophomore'),
    ('JR', 'Junior'),
    ('SR', 'Senior'),
    ('GR', 'Graduate Student'),
)


class Announcement(models.Model):
    user = models.ForeignKey(User)
    created = models.DateTimeField(auto_now_add=True, null=True)
    date = models.DateField(blank=True, null=True)
    text = models.CharField(max_length=250, verbose_name='announcement')
    public = models.BooleanField(default=True, help_text='Deselect to make this announcement only visible to brothers.')

    @classmethod
    def most_recent(cls, public=True):
        """Returns the five most recent announcements posted in the past six months."""
        six_months_ago = datetime.now() - timedelta(days=180)
        if public:
            queryset = cls.objects.exclude(public=False).filter(created__gte=six_months_ago.strftime('%Y-%m-%d'))[:5]
        else:
            queryset = cls.objects.filter(created__gte=six_months_ago.strftime('%Y-%m-%d'))[:5]
        return queryset if queryset.count() > 0 else cls.objects.none()

    def __unicode__(self):
        return self.text

    class Meta:
        ordering = ['-created', '-date', 'text']


class AnnouncementForm(ModelForm):
    class Meta:
        model = Announcement
        fields = ('text', 'date', 'public')


class ContactRecord(models.Model):
    name = models.CharField(max_length=50)
    email = models.EmailField()
    phone = PhoneNumberField(blank=True, help_text="XXX-XXX-XXXX")
    message = models.TextField(default='--', validators=[MaxLengthValidator(500)])
    created = models.DateTimeField(auto_now_add=True, null=True)

    def __unicode__(self):
        return 'Contact Request from %s on %s' % (self.name, self.created.strftime('%b %d, %Y'))

    class Meta:
        ordering = ['-created']


class ContactForm(ModelForm):
    class Meta:
        model = ContactRecord
        fields = ('name', 'email', 'message')


class InformationCard(ContactRecord):
    year = models.CharField(choices=YEAR_CHOICES, max_length=3)
    interests = models.CharField(max_length=150, blank=True)
    relatives = models.CharField(max_length=150, blank=True, verbose_name="Phi Psi Relatives", help_text="If any, please include chapter and year.")
    subscribe = models.BooleanField(default=False, help_text="Get updates on the chapter's activities.")

    def __unicode__(self):
        return 'Information Card from %s on %s' % (self.name, self.created.strftime('%b %d, %Y'))

    class Meta:
        ordering = ['-created']

    
class InformationForm(ModelForm):
    class Meta:
        model = InformationCard
        fields = ('name', 'year', 'email', 'phone', 'interests', 'relatives', 'subscribe')