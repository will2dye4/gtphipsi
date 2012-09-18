# Functions used by multiple modules in the project.

from django.contrib.auth.models import Group, Permission
from django.conf import settings

from brothers.models import User, UserProfile, VisibilitySettings
from brothers.bootstrap import INITIAL_BROTHER_LIST


def get_name_from_badge(badge):
    """Function to return a brother's first and last name given his badge number, assuming he doesn't have an account."""

    return INITIAL_BROTHER_LIST[badge][1] if 0 < badge < len(INITIAL_BROTHER_LIST) else None


def get_all_big_bro_choices():
    """Function to return a list of tuples (badge, name) of all possible big brothers."""
    list = INITIAL_BROTHER_LIST
    for profile in UserProfile.objects.filter(badge__gte=len(INITIAL_BROTHER_LIST)).order_by('badge'):
        tup = (profile.badge, profile.common_name())
        list.append(tup)
    return list


def create_user_and_profile(form_data):
    """Function to create and persist a new User and UserProfile from the cleaned_data dictionary of a UserForm instance."""

    status = form_data['status']

    # create and save the User instance
    user = User.objects.create_user(form_data['username'], form_data['email'], form_data['password'])
    user.first_name = form_data['first_name']
    user.last_name = form_data['last_name']
    _create_user_permissions(user, status == 'U', form_data['make_admin'])
    user.save()

    # create and save the UserProfile instance
    middle, suffix, nickname = form_data['middle_name'], form_data['suffix'], form_data['nickname']
    major, hometown, city, phone = form_data['major'], form_data['hometown'], form_data['current_city'], form_data['phone']
    initiation, grad, dob, badge = form_data['initiation'], form_data['graduation'], form_data['dob'], form_data['badge']
    public, chapter = _create_visibility_settings()
    big_bro = int(form_data['big_brother'])
    profile = UserProfile(user=user, middle_name=middle, suffix=suffix, nickname=nickname, badge=badge, status=status,
                    big_brother=big_bro, major=major, hometown=hometown, current_city=city, phone=phone,
                    initiation=initiation, graduation=grad, dob=dob, public_visibility=public, chapter_visibility=chapter)
    profile.save()


# ============= Private Functions ============= #

def _create_user_permissions(user, undergrad, admin):
    """Helper function to add a new user to the appropriate permissions group(s)."""

    if undergrad:
        group, created = Group.objects.get_or_create(name='Undergraduates')
        if created:
            group.permissions = [Permission.objects.get(codename=code) for code in settings.UNDERGRADUATE_PERMISSIONS]
            group.save()
        user.groups.add(group)

    if admin:
        group, created = Group.objects.get_or_create(name='Administrators')
        if created:
            group.permissions = [Permission.objects.get(codename=code) for code in settings.ADMINISTRATOR_PERMISSIONS]
            group.save()
        user.groups.add(group)


def _create_visibility_settings():
    """Helper function to create default public and chapter VisibilitySettings objects for a new UserProfile."""

    public_visibility = VisibilitySettings(full_name=False, big_brother=False, major=False, hometown=False,
                                current_city=False, initiation=False, graduation=False, dob=False, phone=False, email=False)
    public_visibility.save()
    chapter_visibility = VisibilitySettings(full_name=True, big_brother=True, major=True, hometown=True,
                                current_city=True, initiation=True, graduation=True, dob=True, phone=True, email=True)
    chapter_visibility.save()
    return public_visibility, chapter_visibility