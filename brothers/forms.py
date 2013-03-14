"""Forms for the gtphipsi.brothers package.

This module exports the following form classes:
    - UserForm
    - EditProfileForm
    - EditAccountForm
    - ChangePasswordForm
    - NotificationSettingsForm
    - PublicVisibilityForm
    - ChapterVisibilityForm

This module exports the following widget classes:
    - BrotherSelect

"""

import hashlib

from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.forms.widgets import Select

from gtphipsi.brothers.models import UserProfile, VisibilitySettings, MAJOR_CHOICES, STATUS_CHOICES, SUFFIX_CHOICES
from gtphipsi.common import get_all_big_bro_choices


class BrotherSelect(Select):
    """A select widget customized for members of the chapter (each option displays a brother's name and badge number)."""

    def render_option(self, selected_choices, option_value, option_label):
        """Render a single option (brother) in the format 'First Last ... badge' (e.g., 'George Burdell ... 0')."""
        new_label = ('%s ... %d' % (option_label, option_value) if option_value > 0 else option_label)
        return Select.render_option(self, selected_choices, option_value, new_label)

    def render_options(self, choices, selected_choices):
        """Render all options in the set of choices."""
        return Select.render_options(self, choices, selected_choices)


class UserForm(forms.Form):
    """A form to create new users and user profiles, including all fields for both models (User and UserProfile)."""

    first_name = forms.CharField(max_length=30)
    middle_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30)
    suffix = forms.ChoiceField(choices=SUFFIX_CHOICES, required=False)
    nickname = forms.CharField(max_length=30, required=False,
                               help_text='The name you prefer to be called (if different from your first name)')
    username = forms.CharField(max_length=30)
    password = forms.CharField(min_length=settings.MIN_PASSWORD_LENGTH, widget=forms.PasswordInput,
                               help_text=('Must be at least %d characters long' % settings.MIN_PASSWORD_LENGTH))
    confirm = forms.CharField(min_length=settings.MIN_PASSWORD_LENGTH, widget=forms.PasswordInput, label='Confirm password')
    badge = forms.IntegerField(min_value=1)
    status = forms.ChoiceField(choices=STATUS_CHOICES, initial='U')
    big_brother = forms.ChoiceField(choices=(), required=False, widget=BrotherSelect)
    major = forms.ChoiceField(choices=MAJOR_CHOICES, required=False)
    hometown = forms.CharField(max_length=50, required=False)
    current_city = forms.CharField(max_length=50, required=False)
    initiation = forms.DateField(input_formats=settings.DATE_INPUT_FORMATS, required=False)
    graduation = forms.DateField(input_formats=settings.DATE_INPUT_FORMATS, required=False)
    dob = forms.DateField(input_formats=settings.DATE_INPUT_FORMATS, required=False, label='Date of birth')
    email = forms.EmailField(required=True)
    phone = forms.RegexField(regex=r'^\d{3}-\d{3}-\d{4}$', min_length=12, max_length=12, required=False, help_text='XXX-XXX-XXXX')
    secret_key = forms.CharField(widget=forms.PasswordInput, help_text='Given to brothers by the webmaster')
    make_admin = forms.BooleanField(required=False, help_text='Check this box if you were given a separate admin password')
    admin_password = forms.CharField(widget=forms.PasswordInput, required=False)

    def __init__(self, data=None):
        """Initialize the form and set the list of choices for the 'big_brother' field."""
        super(UserForm, self).__init__(data=data)
        self.fields['big_brother'].choices = get_all_big_bro_choices()

    def clean_username(self):
        """Ensure that the user does not enter a user name that is already taken."""
        username = self.cleaned_data.get('username')
        if username is not None and User.objects.filter(username=username).count() > 0:
            self._errors['username'] = self.error_class(['That username is taken.'])
            del self.cleaned_data['username']
        return self.cleaned_data['username'] if 'username' in self.cleaned_data else None

    def clean_confirm(self):
        """Ensure that the user typed the same password in both the 'password' and 'confirm' fields."""
        password = self.cleaned_data.get('password')
        confirm = self.cleaned_data.get('confirm')
        if password is not None and confirm is not None and password != confirm:
            self._errors['confirm'] = self.error_class(['The passwords you typed do not match.'])
            del self.cleaned_data['confirm']
        return self.cleaned_data['confirm'] if 'confirm' in self.cleaned_data else None

    def clean_badge(self):
        """Ensure that the user does not enter a badge number that has already been used."""
        badge = self.cleaned_data.get('badge')
        if badge is not None and UserProfile.objects.filter(badge=badge).count() > 0:
            self._errors['badge'] = self.error_class(['A brother with that badge number already exists.'])
            del self.cleaned_data['badge']
        return self.cleaned_data['badge'] if 'badge' in self.cleaned_data else None

    def clean_big_brother(self):
        """Ensure that the user does not try to specify himself or a younger member as his big brother."""
        badge = self.cleaned_data.get('badge')
        big_bro_badge = int(self.cleaned_data.get('big_brother'))
        if badge is not None and big_bro_badge > 0:
            error = _get_big_bro_error_message(badge, big_bro_badge)
            if error is not None:
                self._errors['big_brother'] = self.error_class([error])
                del self.cleaned_data['big_brother']
        return self.cleaned_data['big_brother'] if 'big_brother' in self.cleaned_data else None

    def clean_secret_key(self):
        """Ensure that the user typed the correct secret key."""
        if 'secret_key' in self.cleaned_data:
            secret = self.cleaned_data.get('secret_key')
            if secret != settings.BROTHER_KEY:
                hash = hashlib.sha224(secret).hexdigest()
                if hash != settings.BROTHER_KEY:
                    self._errors['secret_key'] = self.error_class(['Nope!'])
                    del self.cleaned_data['secret_key']
        return self.cleaned_data['secret_key'] if 'secret_key' in self.cleaned_data else None

    def clean_admin_password(self):
        """Ensure that the user typed the correct administrator password if they checked the 'make admin' box."""
        if not self.cleaned_data.get('make_admin'):
            return ''   # if admin box is unchecked, validate by default
        if 'admin_password' in self.cleaned_data:
            password = self.cleaned_data.get('admin_password')
            if password != settings.ADMIN_KEY:
                hash = hashlib.sha224(password).hexdigest()
                if hash != settings.ADMIN_KEY:
                    self._errors['admin_password'] = self.error_class(['Wrong.'])
                    del self.cleaned_data['admin_password']
        return self.cleaned_data['admin_password'] if 'admin_password' in self.cleaned_data else None


class EditProfileForm(forms.ModelForm):
    """A form to modify user profiles, based on the UserProfile model class.

    The 'middle_name', 'suffix', 'nickname', and 'status' fields are excluded from the form. These fields are located
    in the EditAccountForm instead. The 'badge' and 'user' fields never change, and the visibility settings can be
    modified using the forms for the pertinent models (ChapterVisibilityForm and PublicVisibilityForm).

    """

    big_brother = forms.ChoiceField(choices=(), required=False, widget=BrotherSelect)
    initiation = forms.DateField(input_formats=settings.DATE_INPUT_FORMATS, widget=forms.DateInput(format='%B %d, %Y'),
                                 required=False)
    graduation = forms.DateField(input_formats=settings.DATE_INPUT_FORMATS, widget=forms.DateInput(format='%B %d, %Y'),
                                 required=False)
    dob = forms.DateField(input_formats=settings.DATE_INPUT_FORMATS, widget=forms.DateInput(format='%B %d, %Y'),
                          required=False, label='Date of birth')
    phone = forms.RegexField(regex=r'^\d{3}-\d{3}-\d{4}$', min_length=12, max_length=12, required=False, help_text='XXX-XXX-XXXX')

    def __init__(self, data=None, instance=None):
        """Initialize the form and set the list of choices for the 'big_brother' field."""
        super(EditProfileForm, self).__init__(data=data, instance=instance)
        self.fields['big_brother'].choices = get_all_big_bro_choices()

    def clean_big_brother(self):
        """Ensure that the user does not try to specify himself or a younger member as his big brother."""
        big_bro_badge = int(self.cleaned_data.get('big_brother'))
        if self.instance is not None and big_bro_badge > 0:
            error = _get_big_bro_error_message(self.instance.badge, big_bro_badge)
            if error is not None:
                self._errors['big_brother'] = self.error_class([error])
                del self.cleaned_data['big_brother']
        return self.cleaned_data['big_brother'] if 'big_brother' in self.cleaned_data else None

    class Meta:
        """Associate the form with the UserProfile model."""
        model = UserProfile
        fields = ('big_brother', 'major', 'hometown', 'current_city', 'initiation', 'graduation', 'dob', 'phone')


class EditAccountForm(forms.Form):
    """A form to modify user accounts and some data about user profiles (middle name, suffix, nickname, and status)."""

    first_name = forms.CharField(max_length=30)
    middle_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30)
    suffix = forms.ChoiceField(choices=SUFFIX_CHOICES, required=False)
    nickname = forms.CharField(max_length=30, required=False,
                               help_text='The name you prefer to be called (if different from your first name)')
    email = forms.EmailField(required=True)
    status = forms.ChoiceField(choices=STATUS_CHOICES, widget=forms.Select(attrs={'onchange': 'updateStatusSelect();'}))


class ChangePasswordForm(forms.Form):
    """A form to change a user's password."""

    old_pass = forms.CharField(widget=forms.PasswordInput, label='Current password')
    password = forms.CharField(min_length=6, widget=forms.PasswordInput, label='New password',
                               help_text=('Must be at least %d characters long' % settings.MIN_PASSWORD_LENGTH))
    confirm = forms.CharField(min_length=6, widget=forms.PasswordInput, label='Confirm new password')
    user = None

    def clean_old_pass(self):
        """Ensure that the user entered the correct value for his current password."""
        old_pass = self.cleaned_data.get('old_pass')
        if old_pass is not None and self.user is not None and not self.user.check_password(old_pass):
            self._errors['old_pass'] = self.error_class(['That\'s not right!'])
            del self.cleaned_data['old_pass']
        return self.cleaned_data['old_pass'] if 'old_pass' in self.cleaned_data else None

    def clean_password(self):
        """Ensure that the user did not enter the same value for his old password and his new password."""
        old_pass = self.cleaned_data.get('old_pass')
        password = self.cleaned_data.get('password')
        if old_pass is not None and password is not None and old_pass == password:
            self.errors['password'] = self.error_class(['Your new password may not be the same as your current password.'])
            del self.cleaned_data['password']
        return self.cleaned_data['password'] if 'password' in self.cleaned_data else None

    def clean_confirm(self):
        """Ensure that the user typed the same password in both the 'password' and 'confirm' fields."""
        password = self.cleaned_data.get('password')
        confirm = self.cleaned_data.get('confirm')
        if password is not None and confirm is not None and password != confirm:
            self._errors['confirm'] = self.error_class(['The passwords you typed do not match.'])
            del self.cleaned_data['confirm']
        return self.cleaned_data['confirm'] if 'confirm' in self.cleaned_data else None


class NotificationSettingsForm(forms.Form):
    """A form to modify a user's notification settings."""

    infocard = forms.BooleanField(required=False, label='New information cards are submitted')
    contact = forms.BooleanField(required=False, label='New contact forms are submitted')
    announcement = forms.BooleanField(required=False, label='New announcements are posted')


class PublicVisibilityForm(forms.ModelForm):
    """A form to modify a user's public visibility settings, based on the VisibilitySettings model class."""

    dob = forms.BooleanField(required=False, label='Date of birth')

    class Meta:
        """Associate the form with the VisibilitySettings model."""
        model = VisibilitySettings


class ChapterVisibilityForm(forms.ModelForm):
    """A form to modify a user's chapter visibility settings, based on the VisibilitySettings model class.

    The following fields may not be hidden from fellow members and thus are excluded from the form: 'full_name',
    'big_brother', 'major', 'hometown', and 'email'.

    """

    dob = forms.BooleanField(required=False, label='Date of birth')

    class Meta:
        """Associate the form with the VisibilitySettings model."""
        model = VisibilitySettings
        exclude = ('full_name', 'big_brother', 'major', 'hometown', 'email')






## ============================================= ##
##                                               ##
##               Private Functions               ##
##                                               ##
## ============================================= ##


def _get_big_bro_error_message(user_badge, big_bro_badge):
    """Return None if the big brother's badge is less than the user's badge, an error message otherwise."""
    error = None
    if big_bro_badge == user_badge:
        error = 'You may not be your own big brother.'
    elif big_bro_badge > user_badge:
        error = 'Your big brother may not have a higher badge number than you.'
    return error