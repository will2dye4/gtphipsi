"""Forms for the gtphipsi.forums package.

This module exports the following form classes:
    - ForumForm
    - PostForm
    - ThreadForm

"""

from django.forms import ModelForm
from django.forms.fields import CharField
from django.forms.widgets import Textarea
from django.template.defaultfilters import slugify

from gtphipsi.forums.models import Forum, Post, Thread


class ForumForm(ModelForm):
    """A form to create and modify forums, based on the Forum model class.

    The 'slug' field is omitted from the form because it is generated automatically from the forum's name.

    """

    def clean_name(self):
        """Return a 'cleaned' value for the forum's name.

        Due to the nature of the forum URLs, forums with names such as 'Subscriptions' or 'Edit Post' are problematic,
        so we ensure that forums with such names are not created. The need to create forums with such names is likely
        never to arise, so this limitation should not be an issue.
        
        """
        name = self.cleaned_data.get('name')
        if name is not None and slugify(name) in ['add', 'subscriptions', 'edit-post']:
            self._errors['name'] = self.error_class(['That name is not allowed.'])
            del self.cleaned_data['name']
        return self.cleaned_data.get('name') if 'name' in self.cleaned_data else None

    class Meta:
        """Associate the form with the Forum model."""
        model = Forum
        exclude = ('slug',)


class PostForm(ModelForm):
    """A form to create and modify posts, based on the Post model class.

    Only the 'body' field is included in the form. All other fields are managed by the view functions behind the scenes,
    except the 'created' and 'updated' fields, which are updated by Django automatically.

    """

    class Meta:
        """Associate the form with the Post model."""
        model = Post
        fields = ('body',)


class ThreadForm(ModelForm):
    """A form to create and modify threads, based on the Thread model class.

    Thread forms include the title of the thread and the content of the thread's first post. Empty threads should never
    exist, so a new thread must also have a new post (the original post) associated with it.

    """

    post = CharField(label='Message', widget=Textarea)

    class Meta:
        """Associate the form with the Thread model."""
        model = Thread
        fields = ('title',)
