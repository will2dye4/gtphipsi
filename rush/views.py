import logging

from django.shortcuts import render
from django.template import RequestContext
from django.http import HttpResponseRedirect, Http404
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required, permission_required

from rush.models import Rush, RushEvent
from rush.forms import RushForm, RushEventForm
from chapter.models import InformationCard


log = logging.getLogger('django')

REFERRER = 'HTTP_REFERER' # typo in 'referrer' intentional


# visible to anyone
def rush(request):
    return render(request, 'rush/rush.html', context_instance=RequestContext(request))


# visible to anyone
def rushphipsi(request):
    return render(request, 'rush/phipsi.html', context_instance=RequestContext(request))


# visible to anyone
def schedule(request):
    current_rush = Rush.current()
    if current_rush is None:
        raise Http404
    else:
        return render(request, 'rush/schedule.html', {'rush': current_rush}, context_instance=RequestContext(request))


# visible to anyone
# Hack - to continue to support the old rush schedule URI.
def old_schedule(request):
    return HttpResponseRedirect(reverse('rush_schedule'))


# visible to anyone
def info_card(request):
    from chapter.forms import InformationForm
    if request.method == 'POST':
        form = InformationForm(request.POST)
        if form.is_valid():
            form.save()
            request.META[REFERRER] = reverse('info_card')
            return HttpResponseRedirect(reverse('info_card_thanks'))
    else:
        form = InformationForm()
    return render(request, 'rush/infocard.html', {'form': form}, context_instance=RequestContext(request))


# visible to anyone
def info_card_thanks(request):
    from django.http import Http404
    if not (REFERRER in request.META and request.META[REFERRER].endswith(reverse('info_card'))):
        raise Http404
    else:
        return render(request, 'rush/infocard_thanks.html', context_instance=RequestContext(request))


@login_required
def list(request):
    queryset = Rush.objects.all()
    return render(request, 'rush/list.html', {'rushes': queryset if queryset.count() > 0 else Rush.objects.none()}, context_instance=RequestContext(request))


@login_required
def show(request, name=''):
    if name: # look up by unique name
        try:
            rush = Rush.objects.get(season=name[0], start_date__year=int(name[1:]))
        except Rush.DoesNotExist:
            raise Http404
    else:  # use the most recent visible rush
        rush = Rush.current()
        if rush is None:
            return HttpResponseRedirect(reverse('rush_list'))
    return render(request, 'rush/show.html', {'rush': rush}, context_instance=RequestContext(request))


@login_required
@permission_required('rush.add_rush', login_url=settings.FORBIDDEN_URL)
def add(request):
    if request.method == 'POST':
        form = RushForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('rush_list'))
    else:
        form = RushForm()
    return render(request, 'rush/create.html', {'form': form}, context_instance=RequestContext(request))



@login_required
@permission_required('rush.change_rush', login_url=settings.FORBIDDEN_URL)
def edit(request, name):
    try:
        rush = Rush.objects.get(season=name[0], start_date__year=int(name[1:]))
    except Rush.DoesNotExist:
        raise Http404
    if request.method == 'POST':
        form = RushForm(request.POST, instance=rush)
        if form.is_valid():
            form.save()
            return get_redirect_from_rush(rush)
    else:
        if 'visible' in request.GET and request.GET['visible'] == 'true':
            rush.visible = True
            rush.save()
            return get_redirect_from_rush(rush)
        elif 'new_pledges' in request.GET:
            rush.pledges += int(request.GET['new_pledges'])
            rush.save()
            return get_redirect_from_rush(rush)
        elif 'delete' in request.GET and request.GET['delete'] == 'true':
            name = rush.title()
            rush.delete()
            log.info('User %s (badge %d) deleted %s', request.user.get_full_name(), request.user.get_profile().badge, name)
            return HttpResponseRedirect(reverse('rush_list'))
        else:
            form = RushForm(instance=rush)
    return render(request, 'rush/edit.html', {'rush_name': name, 'form': form}, context_instance=RequestContext(request))


@login_required
@permission_required('rush.add_rushevent', login_url=settings.FORBIDDEN_URL)
def add_event(request, name):
    try:
        rush = Rush.objects.get(season=name[0], start_date__year=int(name[1:]))
    except Rush.DoesNotExist:
        raise Http404
    if request.method == 'POST':
        form = RushEventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.rush = rush
            event.save()
            return get_redirect_from_rush(rush)
    else:
        form = RushEventForm(initial={'rush': rush})
    return render(request, 'rush/add_event.html', {'rush': rush, 'form': form}, context_instance=RequestContext(request))


@login_required
@permission_required('rush.change_rushevent', login_url=settings.FORBIDDEN_URL)
def edit_event(request, id=0):
    try:
        event = RushEvent.objects.get(pk=id)
    except RushEvent.DoesNotExist:
        raise Http404
    if request.method == 'POST':
        form = RushEventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            return get_redirect_from_rush(event.rush)
    elif 'delete' in request.GET and request.GET['delete'] == 'true':
        event.delete()
        return get_redirect_from_rush(event.rush)
    else:
        form = RushEventForm(instance=event)
    return render(request, 'rush/edit_event.html', {'event_id': event.id, 'form': form}, context_instance=RequestContext(request))


@login_required
def info_card_list(request):
    queryset = InformationCard.objects.all()
    return render(request, 'rush/infocard_list.html', {'cards': queryset if queryset.count() > 0 else InformationCard.objects.none()}, context_instance=RequestContext(request))


@login_required
def info_card_show(request, id=0):
    card = InformationCard.objects.get(pk=id)
    if card is None:
        raise Http404
    else:
        return render(request, 'rush/infocard_show.html', {'card': card}, context_instance=RequestContext(request))


def get_redirect_from_rush(rush):
    return HttpResponseRedirect(reverse('current_rush')) if rush.is_current() else HttpResponseRedirect(reverse('view_rush', kwargs={'name': rush.get_unique_name()}))