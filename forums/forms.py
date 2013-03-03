from django.forms import ModelForm
from django.forms.fields import CharField
from django.forms.widgets import Textarea

from gtphipsi.forums.models import Forum, Thread, Post


class ForumForm(ModelForm):

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