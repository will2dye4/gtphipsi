# Forms related to chapter rush and rush events.

from django.forms import ModelForm, TimeField, DateField, RegexField, BooleanField
from django.conf import settings

from rush.models import Rush, RushEvent, Potential


class RushForm(ModelForm):
    start_date = DateField(input_formats=settings.DATE_INPUT_FORMATS)
    end_date = DateField(input_formats=settings.DATE_INPUT_FORMATS)

    class Meta:
        model = Rush


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


class PotentialForm(ModelForm):
    phone = RegexField(regex=r'^\d{3}-\d{3}-\d{4}$', min_length=12, max_length=12, required=True, help_text='XXX-XXX-XXXX')

    class Meta:
        model = Potential


class PledgeForm(ModelForm):
    phone = RegexField(regex=r'^\d{3}-\d{3}-\d{4}$', min_length=12, max_length=12, required=True, help_text='XXX-XXX-XXXX')
    hidden = BooleanField(required=False, label='Initiated')

    class Meta:
        model = Potential
        exclude = ('pledged',)