"""Forms for the gtphipsi.rush package.

This module exports the following form classes:
    - RushForm
    - RushEventForm
    - PotentialForm
    - PledgeForm

"""

from django.conf import settings
from django.forms import BooleanField, DateField, ModelForm, RegexField, TimeField

from gtphipsi.messages import get_message
from gtphipsi.rush.models import Rush, RushEvent, Potential


class RushForm(ModelForm):
    """A form to create and modify rushes (i.e., IFC coordinated rush weeks), based on the Rush model class."""

    start_date = DateField(input_formats=settings.DATE_INPUT_FORMATS)
    end_date = DateField(input_formats=settings.DATE_INPUT_FORMATS)

    class Meta:
        """Associate the form with the Rush model."""
        model = Rush


class RushEventForm(ModelForm):
    """A form to create and modify individual rush events, based on the RushEvent model class."""

    date = DateField(input_formats=settings.DATE_INPUT_FORMATS)
    start = TimeField(label='Start time', input_formats=settings.TIME_INPUT_FORMATS,
                      error_messages={'invalid': get_message('time.format.invalid')})
    end = TimeField(label='End time', input_formats=settings.TIME_INPUT_FORMATS,
                    error_messages={'invalid': get_message('time.format.invalid')})

    def clean_date(self):
        """Ensure that the rush event's date falls within the rush's date range."""
        rush = self.cleaned_data.get('rush')
        date = self.cleaned_data.get('date')
        if rush is not None and date is not None and (date < rush.start_date or date > rush.end_date):
            start = rush.start_date.strftime('%b %d')
            end = rush.end_date.strftime('%b %d, %Y')
            self._errors['date'] = self.error_class(['The date is outside the valid range (%s - %s).' % (start, end)])
            del self.cleaned_data['date']
        return self.cleaned_data['date'] if 'date' in self.cleaned_data else None

    class Meta:
        """Associate the form with the RushEvent model."""
        model = RushEvent
        fields = ('title', 'date', 'start', 'end', 'description', 'location', 'link', 'food')


class PotentialForm(ModelForm):
    """A form to create and modify records of potential members, based on the Potential model class."""

    phone = RegexField(regex=r'^\d{3}-\d{3}-\d{4}$', min_length=12, max_length=12, required=True, help_text='XXX-XXX-XXXX')

    class Meta:
        """Associate the form with the Potential model."""
        model = Potential


class PledgeForm(ModelForm):
    """A form to create and modify records of pledges, based on the Potential model class with slight modifications."""

    phone = RegexField(regex=r'^\d{3}-\d{3}-\d{4}$', min_length=12, max_length=12, required=True, help_text='XXX-XXX-XXXX')
    hidden = BooleanField(required=False, label='Initiated')

    class Meta:
        """Associate the form with the Potential model."""
        model = Potential
        exclude = ('pledged',)
