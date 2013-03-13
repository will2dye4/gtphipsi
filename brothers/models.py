"""Models for the gtphipsi.brothers package.

This module exports the following model classes:
    - VisibilitySettings
    - UserProfile
    - EmailChangeRequest

This module exports the following tuples of field choices:
    - SUFFIX_CHOICES
    - STATUS_CHOICES
    - MAJOR_CHOICES

This module exports the following dictionary, mapping 'status' strings to unique bits:
    - STATUS_BITS

"""

from django.contrib.auth.models import User
from django.contrib.localflavor.us.models import PhoneNumberField
from django.core.urlresolvers import reverse
from django.db import models


# Maps 'status' strings to unique bits. A user may have multiple 'status' bits set in the 'bits' field of his profile.
STATUS_BITS = {
    'LOCKED_OUT':               0x1,
    'PASSWORD_RESET':           0x2,
    'EMAIL_NEW_INFOCARD':       0x4,
    'EMAIL_NEW_CONTACT':        0x8,
    'EMAIL_NEW_ANNOUNCEMENT':   0x10
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


# Choices for current status in the chapter.
STATUS_CHOICES = (
    ('U', 'Undergraduate'),
    ('O', 'Out of Town'),
    ('A', 'Alumnus')
)


# Possible majors at Georgia Tech.
# This list was last updated on 12/3/2011.
MAJOR_CHOICES = (
    ('', '---------'),
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
    """A user's visibility settings, determining which users should be allowed to see what information."""
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


class UserProfile(models.Model):
    """A user's profile, storing supplemental data about users not provided by Django's built-in User class."""

    user = models.OneToOneField(User)   # need this to connect a user to his profile

    middle_name = models.CharField(max_length=30, blank=True)
    suffix = models.CharField(choices=SUFFIX_CHOICES, max_length=5, default='')
    nickname = models.CharField(max_length=30, blank=True, help_text='the name a brother prefers to be called')

    badge = models.PositiveIntegerField(unique=True)
    status = models.CharField(choices=STATUS_CHOICES, max_length=15, blank=False, default='U')
    big_brother = models.PositiveIntegerField(blank=True, default=0)

    major = models.CharField(choices=MAJOR_CHOICES, max_length=50, blank=True)
    hometown = models.CharField(max_length=50, blank=True)
    current_city = models.CharField(max_length=50, blank=True)
    initiation = models.DateField(blank=True, null=True)
    graduation = models.DateField(blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    phone = PhoneNumberField(blank=True)
    bits = models.IntegerField(blank=True, default=0)

    public_visibility = models.ForeignKey(VisibilitySettings, blank=False, null=True, related_name='public_profiles')
    chapter_visibility = models.ForeignKey(VisibilitySettings, blank=False, null=True, related_name='chapter_profiles')

    @classmethod
    def all_profiles_with_bit(cls, bit=0):
        """Return a list of all user profiles having the specified status bit."""
        return cls.objects.raw('SELECT * FROM brothers_userprofile WHERE (bits & %s) > 0', [bit])

    @classmethod
    def all_emails_with_bit(cls, bit=0):
        """Return a list of the email addresses of all user profiles having the specified status bit."""
        query = 'SELECT u.id, u.email FROM auth_user u JOIN brothers_userprofile b ON (b.user_id = u.id) WHERE (b.bits & %s) > 0'
        queryset = cls.objects.raw(query, [bit])
        return [user.email for user in queryset]

    def __unicode__(self):
        """Return a Unicode string representation of the user profile."""
        return unicode(self.common_name())

    def get_absolute_url(self):
        """Return the absolute URL path for the user profile."""
        return reverse('view_profile', kwargs={'badge': self.badge})

    def full_name(self):
        """Return the brother's full name, in the format 'First[ Middle] Last[, Suffix]'."""
        suffix = (self.suffix != '')
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
        """Return the brother's nickname, if defined, or first name otherwise."""
        return '%s' % (self.nickname if self.nickname else self.user.first_name)

    def common_name(self):
        """Return the brother's nickname (if defined; first name otherwise) and last name."""
        return '%s %s' % (self.preferred_name(), self.user.last_name)

    def is_undergrad(self):
        """Return True if the brother is currently an active undergraduate, False otherwise."""
        return self.status == 'U'

    def is_admin(self):
        """Return True if the brother is an administrator (i.e., a member of the Administrators group), False otherwise."""
        return self.user.groups.filter(name='Administrators').count() > 0

    def get_little_brothers(self):
        """Return the set of UserProfile objects having the user as their big brother."""
        return self.objects.filter(big_brother=self.badge)

    def has_bit(self, bit):
        """Return True if the brother has the specified bit set, False otherwise."""
        return self.bits & bit == bit

    def set_bit(self, bit):
        """Set the specified bit."""
        self.bits |= bit

    def clear_bit(self, bit):
        """Clear the specified bit."""
        self.bits &= ~bit

    class Meta:
        """Define a default sort by badge number ascending."""
        ordering = ['badge']


class EmailChangeRequest(models.Model):
    """A request from a user to change his email address."""
    user = models.ForeignKey(User)
    email = models.EmailField()
    hash = models.CharField(max_length=64)
