# Forms related to brothers of the fraternity.

import hashlib

from django import forms
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

from brothers.models import VisibilitySettings, UserProfile, SUFFIX_CHOICES, STATUS_CHOICES, MAJOR_CHOICES


class PublicVisibilityForm(forms.ModelForm):
    dob = forms.BooleanField(required=False, label='Date of birth')

    class Meta:
        model = VisibilitySettings


class ChapterVisibilityForm(forms.ModelForm):
    dob = forms.BooleanField(required=False, label='Date of birth')

    class Meta:
        model = VisibilitySettings
        exclude = ('full_name', 'big_brother', 'major', 'hometown', 'email')

class UserField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.get_full_name()


class UserForm(forms.Form):
    first_name = forms.CharField(max_length=30)
    middle_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30)
    suffix = forms.ChoiceField(choices=SUFFIX_CHOICES, required=False)
    nickname = forms.CharField(max_length=30, required=False, help_text='The name you prefer to be called (if different from your first name)')
    username = forms.CharField(max_length=30)
    password = forms.CharField(min_length=6, widget=forms.PasswordInput, help_text='Must be at least six characters long')
    confirm = forms.CharField(min_length=6, widget=forms.PasswordInput, label='Confirm password')
    badge = forms.IntegerField(min_value=1)
    status = forms.ChoiceField(choices=STATUS_CHOICES, initial='U')
    big_brother = UserField(queryset=User.objects.exclude(userprofile__isnull=True).exclude(id=models.F('id')), required=False, help_text='Your big brother will only be listed if he has an account')
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

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username is not None and User.objects.filter(username=username).count() > 0:
            self._errors['username'] = self.error_class(['That username is taken.'])
            del self.cleaned_data['username']
        return self.cleaned_data['username'] if 'username' in self.cleaned_data else None

    def clean_confirm(self):
        password = self.cleaned_data.get('password')
        confirm = self.cleaned_data.get('confirm')
        if password is not None and confirm is not None and password != confirm:
            self._errors['confirm'] = self.error_class(['The passwords you typed do not match.'])
            del self.cleaned_data['confirm']
        return self.cleaned_data['confirm'] if 'confirm' in self.cleaned_data else None

    def clean_badge(self):
        badge = self.cleaned_data.get('badge')
        if badge is not None and UserProfile.objects.filter(badge=badge).count() > 0:
            self._errors['badge'] = self.error_class(['A brother with that badge number already exists.'])
            del self.cleaned_data['badge']
        return self.cleaned_data['badge'] if 'badge' in self.cleaned_data else None

    def clean_secret_key(self):
        secret = self.cleaned_data.get('secret_key')
        hash = hashlib.sha224(secret).hexdigest() if secret is not None else None
        if hash is not None and hash != settings.BROTHER_KEY:
            self._errors['secret_key'] = self.error_class(['Nope!'])
            del self.cleaned_data['secret_key']
        return self.cleaned_data['secret_key'] if 'secret_key' in self.cleaned_data else None

    def clean_admin_password(self):
        if not self.cleaned_data.get('make_admin'):
            return ''   # if admin box is unchecked, validate by default
        password = self.cleaned_data.get('admin_password')
        hash = hashlib.sha224(password).hexdigest() if password is not None else None
        if hash is not None and hash != settings.ADMIN_KEY:
            self._errors['admin_password'] = self.error_class(['Wrong.'])
            del self.cleaned_data['admin_password']
        return self.cleaned_data['admin_password'] if 'admin_password' in self.cleaned_data else None


class EditProfileForm(forms.ModelForm):
    big_brother = UserField(queryset=User.objects.exclude(userprofile__isnull=True).exclude(id=models.F('id')), required=False, help_text='Your big brother will only be listed if he has an account')
    initiation = forms.DateField(input_formats=settings.DATE_INPUT_FORMATS, widget=forms.DateInput(format='%B %d, %Y'), required=False)
    graduation = forms.DateField(input_formats=settings.DATE_INPUT_FORMATS, widget=forms.DateInput(format='%B %d, %Y'), required=False)
    dob = forms.DateField(input_formats=settings.DATE_INPUT_FORMATS, widget=forms.DateInput(format='%B %d, %Y'), required=False, label='Date of birth')
    phone = forms.RegexField(regex=r'^\d{3}-\d{3}-\d{4}$', min_length=12, max_length=12, required=False, help_text='XXX-XXX-XXXX')

    class Meta:
        model = UserProfile
        fields = ('big_brother', 'major', 'hometown', 'current_city', 'initiation', 'graduation', 'dob', 'phone')


class EditAccountForm(forms.Form):
    first_name = forms.CharField(max_length=30)
    middle_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30)
    suffix = forms.ChoiceField(choices=SUFFIX_CHOICES, required=False)
    nickname = forms.CharField(max_length=30, required=False, help_text='The name you prefer to be called (if different from your first name)')
    email = forms.EmailField(required=True)
    status = forms.ChoiceField(choices=STATUS_CHOICES, widget=forms.Select(attrs={'onchange': 'updateStatusSelect();'}))


class ChangePasswordForm(forms.Form):
    old_pass = forms.CharField(widget=forms.PasswordInput, label='Current password')
    password = forms.CharField(min_length=6, widget=forms.PasswordInput, label='New password', help_text='Must be at least six characters long')
    confirm = forms.CharField(min_length=6, widget=forms.PasswordInput, label='Confirm new password')
    user = None

    def clean_old_pass(self):
        old_pass = self.cleaned_data.get('old_pass')
        if old_pass is not None and self.user is not None and not self.user.check_password(old_pass):
            self._errors['old_pass'] = self.error_class(['That\'s not right!'])
            del self.cleaned_data['old_pass']
        return self.cleaned_data['old_pass'] if 'old_pass' in self.cleaned_data else None

    def clean_password(self):
        old_pass = self.cleaned_data.get('old_pass')
        password = self.cleaned_data.get('password')
        if old_pass is not None and password is not None and old_pass == password:
            self.errors['password'] = self.error_class(['Your new password may not be the same as your current password.'])
            del self.cleaned_data['password']
        return self.cleaned_data['password'] if 'password' in self.cleaned_data else None

    def clean_confirm(self):
        password = self.cleaned_data.get('password')
        confirm = self.cleaned_data.get('confirm')
        if password is not None and confirm is not None and password != confirm:
            self._errors['confirm'] = self.error_class(['The passwords you typed do not match.'])
            del self.cleaned_data['confirm']
        return self.cleaned_data['confirm'] if 'confirm' in self.cleaned_data else None