from chapter.models import Announcement

# Makes a list of the most recent announcements accessible to all requests.
def announcements_processor(request):
    return {'recent_news': Announcement.most_recent(public=request.user.is_anonymous())}

def menu_item_processor(request):
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
            if path in ['/brothers/profile/', '/brothers/edit/', '/brothers/account/'] or path.startswith('/brothers/privacy') or path.startswith('/brothers/password'):
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
