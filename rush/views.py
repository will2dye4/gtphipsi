from django.shortcuts import render
from django.template import RequestContext
from django.http import HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from models import Rush, RushForm, RushEvent, RushEventForm
from chapter.models import InformationCard

REFERRER = 'HTTP_REFERER' # typo in 'referer' intentional

def rush(request):
    return render(request, 'rush/rush.html', context_instance=RequestContext(request))


def rushphipsi(request):
    return render(request, 'rush/phipsi.html', context_instance=RequestContext(request))


def schedule(request):
    current_rush = Rush.current()
    if current_rush is None:
        raise Http404
    else:
        return render(request, 'rush/schedule.html', {'rush': current_rush}, context_instance=RequestContext(request))


def info_card(request):
    from chapter.models import InformationForm, ContactRecord
    if request.method == 'POST':
        form = InformationForm(request.POST)
        if form.is_valid():
            form.save()
            request.META[REFERRER] = reverse('info_card')
            return HttpResponseRedirect(reverse('info_card_thanks'))
    else:
        form = InformationForm()
    return render(request, 'rush/infocard.html', {'form': form}, context_instance=RequestContext(request))


def info_card_thanks(request):
    from django.http import Http404
    if not (REFERRER in request.META and request.META[REFERRER].endswith(reverse('info_card'))):
        raise Http404
    else:
        return render(request, 'rush/infocardthanks.html', context_instance=RequestContext(request))


@login_required
def list(request):
    queryset = Rush.objects.all()
    return render(request, 'rush/list.html', {'rushes': queryset if queryset.count() > 0 else Rush.objects.none()}, context_instance=RequestContext(request))


@login_required
def show(request, id=0):
    if id: # look up by ID
        rush = Rush.objects.get(pk=id)
        if rush is None:
            raise Http404
    else:  # use the most recent visible rush
        rush = Rush.current()
        if rush is None:
            return HttpResponseRedirect(reverse('rush_list'))
    return render(request, 'rush/show.html', {'rush': rush}, context_instance=RequestContext(request))


@login_required
def current(request):
    return show(request, 0)


@login_required
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
def edit(request, id=0):
    rush = Rush.objects.get(pk=id)
    if rush is None:
        raise Http404
    else:
        if 'visible' in request.GET and request.GET['visible'] == 'true':
            rush.visible = True
            rush.save()
            return HttpResponseRedirect(reverse('view_rush', kwargs={'id': rush.id}))
        elif 'new_pledges' in request.GET:
            rush.pledges += int(request.GET['new_pledges'])
            rush.save()
            return HttpResponseRedirect(reverse('view_rush', kwargs={'id': rush.id}))
        elif 'delete' in request.GET and request.GET['delete'] == 'true':
            rush.delete()
            return HttpResponseRedirect(reverse('rush_list'))
        else:
            if request.method == 'POST':
                form = RushForm(request.POST, instance=rush)
                if form.is_valid():
                    form.save()
                    return HttpResponseRedirect(reverse('view_rush', kwargs={'id': rush.id}))
            else:
                form = RushForm(instance=rush)
    return render(request, 'rush/edit.html', {'rush_id': rush.id, 'form': form}, context_instance=RequestContext(request))


@login_required
def add_event(request, id=0):
    rush = Rush.objects.get(pk=id)
    if rush is None:
        raise Http404
    else:
        if request.method == 'POST':
            form = RushEventForm(request.POST)
            if form.is_valid():
                event = form.save(commit=False)
                event.rush = rush
                event.save()
                return HttpResponseRedirect(reverse('view_rush', kwargs={'id': rush.id}))
        else:
            form = RushEventForm(initial={'rush': rush})
    return render(request, 'rush/addevent.html', {'rush': rush, 'form': form}, context_instance=RequestContext(request))


@login_required
def edit_event(request, id=0):
    event = RushEvent.objects.get(pk=id)
    if event is None:
        raise Http404
    else:
        if 'delete' in request.GET and request.GET['delete'] == 'true':
            event.delete()
            return HttpResponseRedirect(reverse('view_rush', kwargs={'id': event.rush.id}))
        else:
            if request.method == 'POST':
                form = RushEventForm(request.POST, instance=event)
                if form.is_valid():
                    form.save()
                    return HttpResponseRedirect(reverse('view_rush', kwargs={'id': event.rush.id}))
            else:
                form = RushEventForm(instance=event)
    return render(request, 'rush/editevent.html', {'event_id': event.id, 'form': form}, context_instance=RequestContext(request))


@login_required
def info_card_list(request):
    queryset = InformationCard.objects.all()
    return render(request, 'rush/infocardlist.html', {'cards': queryset if queryset.count() > 0 else InformationCard.objects.none()}, context_instance=RequestContext(request))


@login_required
def info_card_show(request, id=0):
    card = InformationCard.objects.get(pk=id)
    if card is None:
        raise Http404
    else:
        return render(request, 'rush/infocardshow.html', {'card': card}, context_instance=RequestContext(request))
