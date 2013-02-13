from django.forms import ModelChoiceField, Form

from gtphipsi.brothers.models import UserProfile


class BrotherModelChoiceField(ModelChoiceField):
    def label_from_instance(self, bro):
        return '%s ... %d' % (bro.common_name(), bro.badge)


class OfficerForm(Form):
    brother = BrotherModelChoiceField(queryset=UserProfile.objects.filter(status='U'), label='Office holder')

