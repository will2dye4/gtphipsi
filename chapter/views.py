"""View functions for the gtphipsi.chapter package.

This module exports the following view functions:
    - about (request)
    - history (request)
    - creed (request)
    - announcements (request)
    - add_announcement (request)
    - edit_announcement (request, id)

"""

import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.core.mail.message import EmailMessage
from django.core.paginator import EmptyPage, InvalidPage, Paginator
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.template import RequestContext

from gtphipsi.brothers.models import UserProfile, STATUS_BITS
from gtphipsi.chapter.models import Announcement, InformationCard
from gtphipsi.chapter.forms import AnnouncementForm
from gtphipsi.common import log_page_view
from gtphipsi.messages import get_message as _


log = logging.getLogger('django')


## ============================================= ##
##                                               ##
##                 Public Views                  ##
##                                               ##
## ============================================= ##


def about(request):
    """Render a page of text containing general information about the chapter."""
    log_page_view(request, 'Chapter Info')
    return render(request, 'chapter/about.html', context_instance=RequestContext(request))


def history(request):
    """Render a page of text describing the history of the national fraternity and the Georgia Beta chapter."""
    log_page_view(request, 'Chapter History')
    return render(request, 'chapter/history.html', context_instance=RequestContext(request))


def creed(request):
    """Render a page of text containing the Creed of Phi Kappa Psi."""
    log_page_view(request, 'Creed')
    return render(request, 'chapter/creed.html', context_instance=RequestContext(request))


def announcements(request):
    """Render a listing of announcements posted by members of the chapter."""

    log_page_view(request, 'Announcement List')
    private = False
    if request.user.is_authenticated():
        if 'bros_only' in request.GET and request.GET['bros_only'] == 'true':
            objects = Announcement.objects.filter(public=False)
            private = True
        else:
            objects = Announcement.objects.all()
        template = 'chapter/announcements_bros_only.html'
    else:
        objects = Announcement.objects.filter(public=True)
        template = 'chapter/announcements.html'

    paginator = Paginator(objects, settings.ANNOUNCEMENTS_PER_PAGE)
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1        # if 'page' parameter is not an integer, default to page 1
    try:
        announcements = paginator.page(page)
    except (EmptyPage, InvalidPage):
        announcements = paginator.page(paginator.num_pages)

    return render(request, template, {'announcements': announcements, 'private': private},
                  context_instance=RequestContext(request))




## ============================================= ##
##                                               ##
##              Authenticated Views              ##
##                                               ##
## ============================================= ##


@login_required
@permission_required('chapter.add_announcement', login_url=settings.FORBIDDEN_URL)
def add_announcement(request):
    """Render and process a form to create a new announcement.

    This function will email all users who have elected to be notified of new announcements and also all potentials
    who have submitted information cards and elected to subscribe to chapter updates.

    """
    log_page_view(request, 'Add Announcement')
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.user = request.user
            announcement.save()
            recipients = UserProfile.all_emails_with_bit(STATUS_BITS['EMAIL_NEW_ANNOUNCEMENT'])
            if announcement.public:
                recipients += InformationCard.all_subscriber_emails()
            date = ('' if announcement.date is None else '[%s] ' % announcement.date.strftime('%B %d, %Y'))
            message = EmailMessage(_('notify.announcement.subject'),
                                   _('notify.announcement.body', args=(announcement.user.get_profile().common_name(),
                                                                       date, announcement.text, settings.URI_PREFIX)),
                                   to=['messenger@gtphipsi.org'], bcc=recipients)
            message.send()
            log.info('%s (%s) added a new announcement: \'%s\'', request.user.username, request.user.get_full_name(),
                     announcement.text)
            return HttpResponseRedirect(reverse('announcements'))
    else:
        form = AnnouncementForm()
    return render(request, 'chapter/add_announcement.html', {'form': form}, context_instance=RequestContext(request))


@login_required
@permission_required('chapter.change_announcement', login_url=settings.FORBIDDEN_URL)
def edit_announcement(request, id):
    """Render and process a form to modify an existing announcement.

    Required parameters:
        - id    =>  the unique ID of the announcement to edit (as an integer)

    If 'delete=true' appears in the request's query string, the announcement will be deleted.

    """
    log_page_view(request, 'Edit Announcement')
    announcement = get_object_or_404(Announcement, id=id)
    profile = request.user.get_profile()
    if announcement.user != request.user and not profile.is_admin():
        return HttpResponseRedirect(reverse('forbidden'))   # only admins may edit other people's announcements
    if request.method == 'POST':
        form = AnnouncementForm(request.POST, instance=announcement)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('announcements'))
    else:
        if 'delete' in request.GET and request.GET['delete'] == 'true':
            text = announcement.text
            announcement.delete()
            log.info('%s (%s) deleted announcement \'%s\'', request.user.username, request.user.get_full_name(), text)
            return HttpResponseRedirect(reverse('announcements'))
        form = AnnouncementForm(instance=announcement)
    return render(request, 'chapter/edit_announcement.html', {'form': form, 'id': announcement.id},
                  context_instance=RequestContext(request))
