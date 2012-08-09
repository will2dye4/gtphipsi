# Forms relating to the chapter and its activities.

from django.forms import ModelForm

from chapter.models import Announcement, ContactRecord, InformationCard


class AnnouncementForm(ModelForm):
    class Meta:
        model = Announcement
        fields = ('text', 'date', 'public')


class ContactForm(ModelForm):
    class Meta:
        model = ContactRecord
        fields = ('name', 'email', 'message')


class InformationForm(ModelForm):
    class Meta:
        model = InformationCard
        fields = ('name', 'year', 'email', 'phone', 'interests', 'relatives', 'subscribe')