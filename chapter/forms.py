"""Forms for the gtphipsi.chapter package.

This module exports the following form classes:
    - AnnouncementForm
    - ContactForm
    - InformationForm

"""

from django.forms import ModelForm

from gtphipsi.chapter.models import Announcement, ContactRecord, InformationCard


class AnnouncementForm(ModelForm):
    """A form for users to create and modify announcements."""

    class Meta:
        """Associate the form with the Announcement model class."""
        model = Announcement
        fields = ('text', 'date', 'public')


class ContactForm(ModelForm):
    """A form for nonmembers to create contact records (via the 'Contact Us' page)."""

    class Meta:
        """Associate the form with the ContactRecord model class."""
        model = ContactRecord
        fields = ('name', 'email', 'message')


class InformationForm(ModelForm):
    """A form for potential members to provide the chapter with information about themselves."""

    class Meta:
        """Associate the form with the InformationCard model class."""
        model = InformationCard
        fields = ('name', 'year', 'email', 'phone', 'interests', 'relatives', 'subscribe')