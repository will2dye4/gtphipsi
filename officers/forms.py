"""Forms for the gtphipsi.officers package.

This module exports the following form classes:
    - OfficerForm

This module exports the following field classes:
    - BrotherModelChoiceField

"""

from django.forms import Form, ModelChoiceField

from gtphipsi.brothers.models import UserProfile


class BrotherModelChoiceField(ModelChoiceField):
    """A model choice field tailored to members of the chapter (each option displays a brother's name and badge number)."""

    def label_from_instance(self, bro):
        """Return an option label from a UserProfile instance in the format 'First Last ... badge'."""
        return '%s ... %d' % (bro.common_name(), bro.badge)


class OfficerForm(Form):
    """A form to create or modify an officer position (identifying which brother currently holds the position)."""

    brother = BrotherModelChoiceField(queryset=UserProfile.objects.filter(status='U'), label='Office holder')
