# Models related to brothers of the fraternity and permissions for administrative activity on the site.
# All administrator users will necessarily be brothers of the chapter.

from django.db import models
from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.localflavor.us.models import PhoneNumberField
#from django.db.models.signals import post_save -- see comment at the bottom of the file

STATUS_BITS = {
    'LOCKED_OUT': 0x1,
}

# Possible suffixes for names.
SUFFIX_CHOICES = (
    ('', '---------'),
    ('S', 'Sr.'),
    ('J', 'Jr.'),
    ('2', 'II'),
    ('3', 'III'),
    ('4', 'IV')
)

# Current status in the chapter.
STATUS_CHOICES = (
    ('U', 'Undergraduate'),
    ('O', 'Out of Town'),
    ('A', 'Alumnus')
)

# This list was last updated on 12/3/2011.
MAJOR_CHOICES = (
    ('College of Architecture', (
            ('AR', 'Architecture'),
            ('BC', 'Building Construction'),
            ('ID', 'Industrial Design')
        )
    ),
    ('College of Computing', (
            ('CS', 'Computer Science'),
            ('CM', 'Computational Media')
        )
    ),
    ('College of Engineering', (
            ('AE', 'Aerospace Engineering'),
            ('BME', 'Biomedical Engineering'),
            ('CBE', 'Chemical and Biomolecular Engineering'),
            ('CV', 'Civil Engineering'),
            ('CE', 'Computer Engineering'),
            ('EE', 'Electrical Engineering'),
            ('EV', 'Environmental Engineering'),
            ('IE', 'Industrial Engineering'),
            ('MSE', 'Materials Science and Engineering'),
            ('ME', 'Mechanical Engineering'),
            ('NRE', 'Nuclear and Radiological Engineering')
        )
    ),
    ('Ivan Allen College of Liberal Arts', (
            ('AL', 'Applied Language and Intercultural Studies'),
            ('EC', 'Economics'),
            ('EIA', 'Economics and International Affairs'),
            ('GE', 'Global Economics and Modern Languages'),
            ('HTS', 'History, Technology, and Society'),
            ('IA', 'International Affairs'),
            ('IL', 'International Affairs and Modern Language'),
            ('PP', 'Public Policy'),
            ('ST', 'Science, Technology, and Culture')
        )
    ),
    ('College of Management', (
            ('BA', 'Business Administration'),
        )
    ),
    ('College of Sciences', (
            ('AM', 'Applied Mathematics'),
            ('AP', 'Applied Physics'),
            ('BIC', 'Biochemistry'),
            ('BIO', 'Biology'),
            ('CH', 'Chemistry'),
            ('DM', 'Discrete Mathematics'),
            ('EAS', 'Earth and Atmospheric Science'),
            ('PH', 'Physics'),
            ('PS', 'Psychology')
        )
    )
)


class VisibilitySettings(models.Model):
    full_name = models.BooleanField(blank=True)
    big_brother = models.BooleanField(blank=True)
    major = models.BooleanField(blank=True)
    hometown = models.BooleanField(blank=True)
    current_city = models.BooleanField(blank=True)
    initiation = models.BooleanField(blank=True)
    graduation = models.BooleanField(blank=True)
    dob = models.BooleanField(blank=True)
    phone = models.BooleanField(blank=True)
    email = models.BooleanField(blank=True)


class PublicVisibilityForm(forms.ModelForm):
    dob = forms.BooleanField(required=False, label='Date of birth')

    class Meta:
        model = VisibilitySettings


class ChapterVisibilityForm(forms.ModelForm):
    dob = forms.BooleanField(required=False, label='Date of birth')

    class Meta:
        model = VisibilitySettings
        exclude = ('full_name', 'big_brother', 'major', 'hometown', 'email')


class UserProfile(models.Model):
    user = models.OneToOneField(User) # need this to connect a user to his profile

    middle_name = models.CharField(max_length=30, blank=True)
    suffix = models.CharField(choices=SUFFIX_CHOICES, max_length=5, default='')
    nickname = models.CharField(max_length=30, blank=True, help_text='the name a brother prefers to be called')

    badge = models.PositiveIntegerField(unique=True, blank=False)
    status = models.CharField(choices=STATUS_CHOICES, max_length=15, blank=False, default='U')
    big_brother = models.ForeignKey(User, blank=True, null=True, related_name='little_brothers')

    major = models.CharField(choices=MAJOR_CHOICES, max_length=50, blank=True)
    hometown = models.CharField(max_length=50, blank=True)
    current_city = models.CharField(max_length=50, blank=True)
    initiation = models.DateField(blank=True, null=True)
    graduation = models.DateField(blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    phone = PhoneNumberField(blank=True)
    bits = models.IntegerField(blank=True, default=0) # (1 << 0): user is locked out

    public_visibility = models.ForeignKey(VisibilitySettings, blank=False, null=True, related_name='public_profiles')
    chapter_visibility = models.ForeignKey(VisibilitySettings, blank=False, null=True, related_name='chapter_profiles')

    def __unicode__(self):
        return self.common_name()

    def full_name(self):
        """Returns the brother's full name, in the format 'First[ Middle] Last[, Suffix]'."""
        suffix = self.suffix != ''
        values = (self.user.first_name,
                ' ' if self.middle_name else '',
                self.middle_name,
                self.user.last_name,
                ',' if suffix and (self.suffix in ['J', 'S']) else '',
                ' ' if suffix else '',
                self.get_suffix_display() if suffix else ''
        )
        return '%s%s%s %s%s%s%s' % values

    def preferred_name(self):
        """Returns the brother's nickname, if defined, or first name otherwise."""
        return '%s' % (self.nickname if self.nickname else self.user.first_name)

    def common_name(self):
        """Returns the brother's nickname (if defined; first name otherwise) and last name."""
        return '%s %s' % (self.preferred_name(), self.user.last_name)

    def is_undergrad(self):
        """Returns True if the brother is currently an active undergraduate."""
        return self.status == 'U'

    def is_admin(self):
        """Returns True if the brother is an administrator user (i.e., a member of the Administrators group)."""
        return self.user.groups.filter(name='Administrators').count() > 0

    def has_bit(self, bit):
        """Returns True if the brother has the specified bit set."""
        return self.bits & bit == bit

    class Meta:
        ordering = ['badge']
        # permissions = (('codename', 'description'),) ... add permissions as needed


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
        if secret is not None and secret != settings.SECRET_KEY:
            self._errors['secret_key'] = self.error_class(['Nope!'])
            del self.cleaned_data['secret_key']
        return self.cleaned_data['secret_key'] if 'secret_key' in self.cleaned_data else None

    def clean_admin_password(self):
        if not self.cleaned_data.get('make_admin'):
            return ''   # if admin box is unchecked, validate by default
        password = self.cleaned_data.get('admin_password')
        if password is not None and password != settings.ADMIN_KEY:
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
    old_pass = forms.CharField(widget=forms.PasswordInput)
    password = forms.CharField(min_length=6, widget=forms.PasswordInput, help_text='Must be at least six characters long')
    confirm = forms.CharField(min_length=6, widget=forms.PasswordInput, label='Confirm password')
    user = None

    def clean_old_pass(self):
        old_pass = self.cleaned_data.get('old_pass')
        if old_pass is not None and self.user is not None and old_pass != self.user.password:
            self._errors['old_pass'] = self.error_class(['That\'s not right!'])
            del self.cleaned_data['old_pass']
        return self.cleaned_data['old_pass'] if 'old_pass' in self.cleaned_data else None

    def clean_confirm(self):
        password = self.cleaned_data.get('password')
        confirm = self.cleaned_data.get('confirm')
        if password is not None and confirm is not None and password != confirm:
            self._errors['confirm'] = self.error_class(['The passwords you typed do not match.'])
            del self.cleaned_data['confirm']
        return self.cleaned_data['confirm'] if 'confirm' in self.cleaned_data else None


# The code below should be used here, but due to the fact that `badge` and `status` must be provided
# but are not known at the time the User instance is created, it is omitted. This should be fixed.
#def create_user_profile(sender, instance, created, **kwargs):
#    """Hook to create a user profile whenever a new user is created."""
#   if created:
#        UserProfile.objects.create(user=instance)
#post_save.connect(create_user_profile, sender=User)