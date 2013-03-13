"""Forms for the gtphipsi.officers package.

This module exports the following form classes:
    - OfficerForm
    - OfficerHistoryForm

This module exports the following field classes:
    - BrotherModelChoiceField

"""

from datetime import date

from django.conf import settings
from django.forms import DateField, Form, ModelForm, ModelChoiceField

from gtphipsi.brothers.models import UserProfile
from gtphipsi.officers.models import OfficerHistory


class BrotherModelChoiceField(ModelChoiceField):
    """A model choice field tailored to members of the chapter (each option displays a brother's name and badge number)."""

    def label_from_instance(self, bro):
        """Return an option label from a UserProfile instance in the format 'First Last ... badge'."""
        return '%s ... %d' % (bro.common_name(), bro.badge)


class OfficerForm(Form):
    """A form to create or modify an officer position (identifying which brother currently holds the position)."""

    brother = BrotherModelChoiceField(queryset=UserProfile.objects.filter(status='U'), label='Office holder')


class OfficerHistoryForm(ModelForm):
    """A form to create an officer history record, based on the OfficerHistory model class."""

    brother = BrotherModelChoiceField(queryset=UserProfile.objects.all(), label='Office holder')
    end = DateField(input_formats=settings.DATE_INPUT_FORMATS, label='End date')

    def clean_start(self):
        """Ensure that the start date is in the past and after the chapter's installation (May 20, 2000)."""
        start = self.cleaned_data.get('start')
        if start is not None:
            if start > date.today():
                self._errors['start'] = self.error_class(['The start date must be in the past.'])
                del self.cleaned_data['start']
            elif start < date(2000, 5, 20):
                self._errors['start'] = self.error_class(['The start date must be after the chapter\'s installation.'])
                del self.cleaned_data['start']
        return self.cleaned_data['start'] if 'start' in self.cleaned_data else None

    def clean_end(self):
        """Ensure that the end date is in the past, after the chapter's installation, and after the start date."""
        end = self.cleaned_data.get('end')
        start = self.cleaned_data.get('start')
        if end is not None:
            if end > date.today():
                self._errors['end'] = self.error_class(['The end date must be in the past.'])
                del self.cleaned_data['end']
            elif end < date(2000, 5, 20):
                self._errors['end'] = self.error_class(['The end date must be after the chapter\'s installation.'])
                del self.cleaned_data['end']
            elif start is not None and end < start:
                self._errors['end'] = self.error_class(['The end date must be later than the start date.'])
                del self.cleaned_data['end']
        return self.cleaned_data['end'] if 'end' in self.cleaned_data else None

    class Meta:
        """Associate the form with the OfficerHistory model."""
        model = OfficerHistory
        exclude = ('office',)
