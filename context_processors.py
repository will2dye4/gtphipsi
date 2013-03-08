"""Context processors for the gtphipsi web application.

This module exports the following context processor functions:
    - announcements_processor (request)
    - user_profile_processor (request)
    - group_perms_processor (request)
    - menu_item_processor (request)

"""

from gtphipsi.chapter.models import Announcement


def announcements_processor(request):
    """Add an item 'recent_news', containing the most recently posted announcements, to all requests."""
    return {'recent_news': Announcement.most_recent(public=request.user.is_anonymous())}


def user_profile_processor(request):
    """Add an item 'user_profile', containing the profile of the currently authenticated user, to all requests."""
    return {'user_profile': request.user.get_profile() if request.user.is_authenticated() else None}


def group_perms_processor(request):
    """Add an item 'group_perms', containing the permissions associated with the user's groups, to all requests."""
    if 'group_perms' not in request.session:
        perms = []
        if request.user.is_authenticated():
            for group in request.user.groups.all():
                for perm in group.permissions.values_list('codename', flat=True):
                    if perm not in perms:
                        perms.append(perm)
        request.session['group_perms'] = perms
    return {'group_perms': request.session['group_perms']}



def menu_item_processor(request):
    """Add an item 'menu_item', indicating which menu category should be highlighted, to all requests."""
    path = request.path
    menu_item = ''
    if path == '/':
        menu_item = 'home'
    elif path.startswith('/rush'):
        menu_item = 'rush'
    elif path.startswith('/calendar'):
        menu_item = 'calendar'
    elif request.user.is_authenticated():
        if path.startswith('/chapter/announcements'):
            menu_item = 'announcements'
        elif path.startswith('/brothers'):
            if path in ['/brothers/profile/', '/brothers/edit/', '/brothers/account/'] \
                    or path.startswith('/brothers/privacy') or path.startswith('/brothers/password'):
                menu_item = 'account'
            else:
                menu_item = 'admin'
        elif path.startswith('/officers'):
            menu_item = 'officers'
        elif path.startswith('/forums'):
            menu_item = 'forums'
    else:
        if path.startswith('/chapter') or path.startswith('/brothers'):
            menu_item = 'chapter'
        elif path.startswith('/contact'):
            menu_item = 'contact'
    return {'menu_item': menu_item}
