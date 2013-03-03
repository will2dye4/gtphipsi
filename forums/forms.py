from django.forms import ModelForm
from django.forms.fields import CharField
from django.forms.widgets import Textarea
from django.template.defaultfilters import slugify

from gtphipsi.forums.models import Forum, Thread, Post


class ForumForm(ModelForm):

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name is not None and slugify(name) in ['add', 'subscriptions', 'edit-post']:
            self._errors['name'] = self.error_class(['That name is not allowed.'])
            del self.cleaned_data['name']
        return self.cleaned_data.get('name') if 'name' in self.cleaned_data else None

    class Meta:
        model = Forum
        exclude = ('slug')


class ThreadForm(ModelForm):
    post = CharField(label='Message', widget=Textarea)

    class Meta:
        model = Thread
        fields = ('title',)


class PostForm(ModelForm):

    class Meta:
        model = Post
        fields = ('body',)