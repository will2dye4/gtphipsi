from chapter.models import Announcement

# Makes a list of the most recent announcements accessible to all requests.
def announcements_processor(request):
    return {'recent_news': Announcement.most_recent()}
