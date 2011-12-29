from django.shortcuts import render
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404
from models import Announcement, AnnouncementForm

def about(request):
    return render(request, 'chapter/about.html', context_instance=RequestContext(request))

def history(request):
    return render(request, 'chapter/history.html', context_instance=RequestContext(request))

def creed(request):
    return render(request, 'chapter/creed.html', context_instance=RequestContext(request))

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
            return HttpResponseRedirect(reverse('announcements'))
    else:
        form = AnnouncementForm()
    return render(request, 'chapter/addannouncement.html', {'form': form}, context_instance=RequestContext(request))


@login_required
def edit_announcement(request, id=0):
    announcement = Announcement.objects.get(pk=id)
    if announcement is None:
        raise Http404
    else:
        if 'delete' in request.GET and request.GET['delete'] == 'true':
            announcement.delete()
            return HttpResponseRedirect(reverse('announcements'))
        elif request.method == 'POST':
            form = AnnouncementForm(request.POST, instance=announcement)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect(reverse('announcements'))
        else:
            form = AnnouncementForm(instance=announcement)
    return render(request, 'chapter/editannouncement.html', {'form': form, 'id': announcement.id}, context_instance=RequestContext(request))