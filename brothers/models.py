# Models related to brothers of the fraternity and permissions for administrative activity on the site.
# All administrator users will necessarily be brothers of the chapter.

from django.db import models
from django.contrib.auth.models import User
from django.contrib.localflavor.us.models import PhoneNumberField
#from django.db.models.signals import post_save -- see comment at the bottom of the file

STATUS_BITS = {
    'LOCKED_OUT': 0x1,
    'PASSWORD_RESET': 0x2,
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


#class SecurityQuestion(models.Model):
#    question = models.CharField(max_length=256)
#    answer = models.CharField(max_length=256)


#class SecurityQuestionForm(forms.Form):

#    class Meta:
#        model = SecurityQuestion


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


class UserProfile(models.Model):
    user = models.OneToOneField(User) # need this to connect a user to his profile

    middle_name = models.CharField(max_length=30, blank=True)
    suffix = models.CharField(choices=SUFFIX_CHOICES, max_length=5, default='')
    nickname = models.CharField(max_length=30, blank=True, help_text='the name a brother prefers to be called')

    badge = models.PositiveIntegerField(unique=True, blank=False)
    status = models.CharField(choices=STATUS_CHOICES, max_length=15, blank=False, default='U')
    big_brother = models.PositiveIntegerField(blank=True, default=0)

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

#    security_question = models.ForeignKey(SecurityQuestion, blank=True, null=True)

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

    def get_little_brothers(self):
        """Returns the set of UserProfile objects having this profile's badge as their big_brother."""
        return self.objects.filter(big_brother=self.badge)

    def has_bit(self, bit):
        """Returns True if the brother has the specified bit set."""
        return self.bits & bit == bit

    def set_bit(self, bit):
        """Sets the specified bit."""
        self.bits |= bit

    def clear_bit(self, bit):
        """Clears the specified bit."""
        self.bits &= ~bit

    class Meta:
        ordering = ['badge']
        # permissions = (('codename', 'description'),) ... add permissions as needed


# The code below should be used here, but due to the fact that `badge` and `status` must be provided
# but are not known at the time the User instance is created, it is omitted. This should be fixed.
#def create_user_profile(sender, instance, created, **kwargs):
#    """Hook to create a user profile whenever a new user is created."""
#   if created:
#        UserProfile.objects.create(user=instance)
#post_save.connect(create_user_profile, sender=User)