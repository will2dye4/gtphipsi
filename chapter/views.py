import logging

from django.shortcuts import render
from django.template import RequestContext
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.mail.message import EmailMessage
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404

from chapter.models import Announcement, InformationCard
from chapter.forms import AnnouncementForm
from brothers.models import STATUS_BITS, UserProfile
from gtphipsi.messages import get_message as _


log = logging.getLogger('django')


# visible to all users
def about(request):
    return render(request, 'chapter/about.html', context_instance=RequestContext(request))


# visible to all users
def history(request):
    return render(request, 'chapter/history.html', context_instance=RequestContext(request))


# visible to all users
def creed(request):
    return render(request, 'chapter/creed.html', context_instance=RequestContext(request))


# visible to all users
def announcements(request):
    private = False
    if request.user.is_authenticated():
        if 'bros_only' in request.GET and request.GET['bros_only'] == 'true':
            announcement_list = Announcement.objects.filter(public=False)
            private = True
        else:
            announcement_list = Announcement.objects.all()
        template = 'chapter/announcements_bros_only.html'
    else:
        announcement_list = Announcement.objects.filter(public=True)
        template = 'chapter/announcements.html'

    paginator = Paginator(announcement_list, 20)
    page = request.GET.get('page', 1)
    try:
        list = paginator.page(page)
    except PageNotAnInteger:
        list = paginator.page(1)
    except EmptyPage:
        list = paginator.page(paginator.num_pages)

    return render(request, template, {'announcements': list, 'private': private}, context_instance=RequestContext(request))


@login_required
def add_announcement(request):
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.user = request.user
            announcement.save()
            recipients = UserProfile.all_emails_with_bit(STATUS_BITS['EMAIL_NEW_ANNOUNCEMENT'])
            if announcement.public:
                recipients += InformationCard.all_subscriber_emails()
            message = EmailMessage(_('notify.announcement.subject'), _('notify.announcement.body', args=(
                    announcement.user.get_profile().common_name(),
                    '' if announcement.date is None else '[%s] ' % announcement.date.strftime('%B %d, %Y'),
                    announcement.text,
                    settings.URI_PREFIX
                )), to=['messenger@gtphipsi.org'], bcc=recipients
            )
            message.send()
            return HttpResponseRedirect(reverse('announcements'))
    else:
        form = AnnouncementForm()
    return render(request, 'chapter/add_announcement.html', {'form': form}, context_instance=RequestContext(request))


@login_required
def edit_announcement(request, id=0):
    announcement = Announcement.objects.get(pk=id)
    if announcement is None:
        raise Http404
    else:
        if 'delete' in request.GET and request.GET['delete'] == 'true':
            text = announcement.text
            announcement.delete()
            log.info('User %s (badge %d) deleted announcement "%s"', request.user.get_full_name(), request.user.get_profile().badge, text)
            return HttpResponseRedirect(reverse('announcements'))
        elif request.method == 'POST':
            form = AnnouncementForm(request.POST, instance=announcement)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect(reverse('announcements'))
        else:
            form = AnnouncementForm(instance=announcement)
    return render(request, 'chapter/edit_announcement.html', {'form': form, 'id': announcement.id}, context_instance=RequestContext(request))