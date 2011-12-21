from chapter.models import Announcement

# Makes a list of the most recent announcements accessible to all requests.
def announcements_processor(request):
    return {'recent_news': Announcement.most_recent()}

def menu_item_processor(request):
    path = request.path
    menu_item = ''
    if path == '/':
        menu_item = 'home'
    elif request.user.is_authenticated():
        pass # TODO
    else:
        if path.startswith('/rush'):
            menu_item = 'rush'
        elif path.startswith('/chapter') or path.startswith('/brothers'):
            menu_item = 'chapter'
        elif path.startswith('/calendar'):
            menu_item = 'calendar'
        elif path.startswith('/contact'):
            menu_item = 'contact'
    return {'menu_item': menu_item}
