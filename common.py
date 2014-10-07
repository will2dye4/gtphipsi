"""Functions and constants used in several modules of the gtphipsi package.

This module exports the following functions:
    - get_name_from_badge (badge)
    - get_all_big_bro_choices ()
    - get_rush_or_404 (rush_name)
    - create_user_and_profile (form_data)
    - log_page_view (request, name)
    - bb_code_escape (text)
    - bb_code_unescape (text)

This module exports the following constant definitions:
    - REFERRER

"""

import logging
import re

from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.shortcuts import get_object_or_404

from gtphipsi.brothers.bootstrap import INITIAL_BROTHER_LIST
from gtphipsi.brothers.models import User, UserProfile, VisibilitySettings
from gtphipsi.rush.models import Rush


log = logging.getLogger('django.request')

# The literal name of the HTTP Referrer header. The typo below in 'referrer' is intentional.
REFERRER = 'HTTP_REFERER'
# The correct format for a rush "name" (as expected by URLs); Spring Rush 2013 would be 'S2013'.
RUSH_NAME_FORMAT = re.compile('^(?P<season>[FSU])(?P<year>\d{4})$')


def get_name_from_badge(badge):
    """Return a brother's first and last name given his badge number, assuming he doesn't have an account."""
    return INITIAL_BROTHER_LIST[badge][1] if 0 < badge < len(INITIAL_BROTHER_LIST) else None


def get_all_big_bro_choices():
    """Return a list of tuples (in the format (badge, name)) of all possible big brothers."""
    bro_list = INITIAL_BROTHER_LIST
    for profile in UserProfile.objects.filter(badge__gte=len(INITIAL_BROTHER_LIST)).order_by('badge'):
        tup = (profile.badge, profile.common_name())
        if tup not in bro_list:
            bro_list.append(tup)
    return bro_list


def get_rush_or_404(rush_name):
    """Return the rush instance having the provided unique name, if one exists.

    Required parameters:
        - rush_name  =>  the unique name (abbreviation) of the rush to find (as a string)

    If 'name' is None, the function returns None. Otherwise, the function looks for a rush with the provided unique
    name, in the format returned by the get_unique_name() method of the Rush model class. If a matching rush is found,
    it is returned; if not, Http404 is raised.

    """
    rush = None
    if rush_name is not None:
        matcher = RUSH_NAME_FORMAT.match(rush_name)
        if matcher is not None:
            rush = get_object_or_404(Rush, season=matcher.group('season'), start_date__year=int(matcher.group('year')))
    return rush


def create_user_and_profile(form_data):
    """Create and save a new User and UserProfile from the cleaned_data dictionary of a UserForm instance."""

    status = form_data['status']

    # create and save the User instance
    user = User.objects.create_user(form_data['username'], form_data['email'], form_data['password'])
    user.first_name = form_data['first_name']
    user.last_name = form_data['last_name']
    _create_user_permissions(user, status != 'A', form_data['make_admin'])
    user.save()

    # create and save the UserProfile instance
    public, chapter = _create_visibility_settings()
    profile = UserProfile.objects.create(user=user, middle_name=form_data['middle_name'], suffix=form_data['suffix'],
                                         nickname=form_data['nickname'], badge=form_data['badge'], status=status,
                                         big_brother=int(form_data['big_brother']), major=form_data['major'],
                                         hometown=form_data['hometown'], current_city=form_data['current_city'],
                                         phone=form_data['phone'], initiation=form_data['initiation'],
                                         graduation=form_data['graduation'], dob=form_data['dob'],
                                         public_visibility=public, chapter_visibility=chapter)
    profile.save()


def log_page_view(request, name):
    """Log a view to the specified page (view), including information about the client viewing the page."""
    method = request.method
    path = request.path
    if method == 'POST':
        post = ', POST Data: { '
        for key, value in request.POST.iteritems():
            if key not in ['csrfmiddlewaretoken', 'password', 'confirm', 'old_pass', 'secret_key', 'admin_password']:
                post += '%s: \'%s\', ' % (key, unicode(value))
        post += '}'
    else:
        post = ''
    if request.user.is_authenticated():
        profile = request.user.get_profile()
        client_string = ' User: %s (%s ... %d),' % (request.user.username, profile.common_name(), profile.badge)
    else:
        client_string = ''
    if 'HTTP_USER_AGENT' in request.META:
        user_agent = request.META['HTTP_USER_AGENT']
    else:
        user_agent = '<not supplied>'
    log.debug('[%s]%s Request: %s %s%s, User Agent: %s' % (name, client_string, method, path, post, user_agent))





## ============================================= ##
##                                               ##
##               Private Functions               ##
##                                               ##
## ============================================= ##

def bb_code_escape(text):
    r"""Return an escaped version of the provided text, with BB markup converted to HTML.

    The text '<b>bold</b> & [B]bold[/B] [I]italic[/I] [U]underline[/U] \n [URL="/"]link[/URL]'
    becomes  '&lt;b&gt;bold&lt;/b&gt; &amp; <b>bold</b> <i>italic</i> <u>underline</u> <br /> <a href="/">link</a>'.

    Posts are rendered as-is (i.e., without HTML escaping) in the 'view_thread.html' template, so user input must be
    escaped before being stored in the database and rendered in the browser. Any HTML tags in the input will be
    converted to a safe representation (replacing '<', '>', and '&' with the HTML literals '&lt;', '&gt;', and '&amp;').
    Then any BB markup in the input ('[B]...[/B]', '[URL="..."]...[/URL]', etc.) is converted to HTML.

    """
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;') \
            .replace('[B]', '<b>').replace('[/B]', '</b>').replace('[I]', '<i>').replace('[/I]', '</i>') \
            .replace('[U]', '<u>').replace('[/U]', '</u>').replace('\n', '<br />') \
            .replace('[URL=\"', '<a href=\"').replace('\"]', '\">').replace('[/URL]', '</a>')


def bb_code_unescape(text):
    r"""Return an unescaped version of the provided text, with HTML converted to BB markup.

    The text '&lt;b&gt;bold&lt;/b&gt; &amp; <b>bold</b> <i>italic</i> <u>underline</u> <br /> <a href="/">link</a>'
    becomes  '<b>bold</b> & [B]bold[/B] [I]italic[/I] [U]underline[/U] \n [URL="/"]link[/URL]'.

    When users edit posts, they expect to see the BB markup they originally wrote and not the escaped text returned by
    _bb_code_escape(). Additionally, if previously-escaped text is re-escaped, the escaped HTML tags will be removed
    and the post will not be properly formatted in the browser. This function avoids these issues by restoring escaped
    text to its original (unescaped) form.

    """
    return text.replace('<b>', '[B]').replace('</b>', '[/B]').replace('<i>', '[I]').replace('</i>', '[/I]') \
            .replace('<u>', '[U]').replace('</u>', '[/U]').replace('<br />', '\n') \
            .replace('<a href=\"', '[URL=\"').replace('\">', '\"]').replace('</a>', '[/URL]') \
            .replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')


def _create_user_permissions(user, undergrad, admin):
    """Add a new user to the appropriate permissions group(s)."""

    if undergrad:
        group, created = Group.objects.get_or_create(name='Undergraduates')
        if created:
            group.permissions = Permission.objects.filter(codename__in=settings.UNDERGRADUATE_PERMISSIONS)
            group.save()
        user.groups.add(group)
    else:
        group, created = Group.objects.get_or_create(name='Alumni')
        if created:
            group.permissions = Permission.objects.filter(codename__in=settings.ALUMNI_PERMISSIONS)
            group.save()
        user.groups.add(group)

    if admin:
        group, created = Group.objects.get_or_create(name='Administrators')
        if created:
            group.permissions = Permission.objects.filter(codename__in=settings.ADMINISTRATOR_PERMISSIONS)
            group.save()
        user.groups.add(group)


def _create_visibility_settings():
    """Create default public and chapter visibility settings for a new user profile."""

    public_visibility = VisibilitySettings.objects.create(full_name=False, big_brother=False, major=False,
                                                          hometown=False, current_city=False, initiation=False,
                                                          graduation=False, dob=False, phone=False, email=False)
    public_visibility.save()
    chapter_visibility = VisibilitySettings.objects.create(full_name=True, big_brother=True, major=True, hometown=True,
                                                           current_city=True, initiation=True, graduation=True, dob=True,
                                                           phone=True, email=True)
    chapter_visibility.save()
    return public_visibility, chapter_visibility
