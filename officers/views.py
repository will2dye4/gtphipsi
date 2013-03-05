"""View functions for the gtphipsi.officers package.

This module exports the following view functions:
    - officers (request)
    - edit_officer (request)
    - add_officer (request)
    - officer_history (request)
    - office_history (request, office)

"""

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.template import RequestContext

from gtphipsi.brothers.models import UserProfile
from gtphipsi.messages import get_message
from gtphipsi.officers.forms import OfficerForm
from gtphipsi.officers.models import ChapterOfficer, OfficerHistory, OFFICER_CHOICES


## ============================================= ##
##                                               ##
##                 Public Views                  ##
##                                               ##
## ============================================= ##


def officers(request):
    """Render a listing of the chapter's current officers."""
    officers = []
    incomplete = False
    for key, value in OFFICER_CHOICES:  # retrieving records individually is inefficient, but it does sort by office
        try:
            officer = ChapterOfficer.objects.get(office=key)
        except ChapterOfficer.DoesNotExist:
            incomplete = True
        else:
            officers.append(officer)
    return render(request, 'officers/officers.html', {'officers': officers, 'add': incomplete},
                  context_instance=RequestContext(request))




## ============================================= ##
##                                               ##
##              Authenticated Views              ##
##                                               ##
## ============================================= ##


@login_required
@permission_required('officers.change_chapterofficer', login_url=settings.FORBIDDEN_URL)
def edit_officer(request, office):
    """Render and process a form to modify which brother currently holds an officer position.

    Required parameters:
        - office    =>  the abbreviation of the office to edit as a string (e.g., 'GP')

    """

    title = None
    for key, value in OFFICER_CHOICES:
        if key == office:
            title = value
            break
    if title is None:
        raise Http404

    if request.method == 'POST':
        form = OfficerForm(request.POST)
        if form.is_valid():
            brother = form.cleaned_data.get('brother')
            try:
                prev = ChapterOfficer.objects.get(office=office)
            except ChapterOfficer.DoesNotExist:     # this shouldn't happen, but handle it just in case
                officer = ChapterOfficer.objects.create(office=office, brother=brother)
                officer.save()
            else:
                if prev.brother != brother:
                    history = OfficerHistory.objects.create(office=prev.office, brother=prev.brother, start=prev.updated)
                    history.save()
                    prev.brother = brother  # just update the existing officer record instead of deleting and recreating
                    prev.save()
            return HttpResponseRedirect(reverse('show_officers'))
    else:
        form = OfficerForm()

    return render(request, 'officers/edit_officer.html', {'form': form, 'title': title, 'office': office},
                  context_instance=RequestContext(request))


@login_required
@permission_required('officers.add_chapterofficer', login_url=settings.FORBIDDEN_URL)
def add_officer(request):
    """Render and process a form for administrators to add chapter officers (until all offices are added)."""

    error = None
    if request.method == 'POST':
        office = request.POST.get('office')
        found = False
        for key, value in OFFICER_CHOICES:
            if key == office:
                found = True
                break
        if found and not ChapterOfficer.objects.filter(office=office).count():
            badge = int(request.POST.get('brother'))
            try:
                brother = UserProfile.objects.get(badge=badge)
            except UserProfile.DoesNotExist:
                error = get_message('officer.brother.invalid')
            else:
                officer = ChapterOfficer.objects.create(office=office, brother=brother)
                officer.save()
                return HttpResponseRedirect(reverse('show_officers'))
        else:
            error = get_message('officer.office.invalid')

    missing = []
    for key, value in OFFICER_CHOICES:
        try:
            ChapterOfficer.objects.get(office=key)
        except ChapterOfficer.DoesNotExist:
            missing.append((key, value))
    if not len(missing):
        return HttpResponseRedirect(reverse('forbidden'))   # all offices have already been added

    brothers = []
    for brother in UserProfile.objects.filter(status='U'):
        brothers.append((brother.badge, brother.common_name()))

    return render(request, 'officers/add_officer.html', {'offices': missing, 'brothers': brothers, 'error': error},
                  context_instance=RequestContext(request))


@login_required
def officer_history(request):
    """Render a listing of office names from which users may choose to see the history for an office."""
    return render(request, 'officers/officer_history.html', context_instance=RequestContext(request))


@login_required
def office_history(request, office):
    """Render a listing of brothers who have held an officer position in the past, including the current officer.

    Required parameters:
        - office    =>  the abbreviation of the office whose history to view as a string (e.g., 'GP')

    """

    title = None
    for key, value in OFFICER_CHOICES:
        if key == office:
            title = value
            break
    if title is None:
        raise Http404   # invalid officer position

    history = []
    try:
        current = ChapterOfficer.objects.get(office=office)
    except ChapterOfficer.DoesNotExist:
        pass
    else:
        history.append((current.brother, current.updated, None))

    has_more = (OfficerHistory.objects.filter(office=office).count() > 9)
    show_all = (has_more and 'full' in request.GET and request.GET.get('full') == 'true')
    if has_more and show_all:
        old_officers = OfficerHistory.objects.filter(office=office).order_by('-end')
        has_more = False
    else:
        old_officers = OfficerHistory.objects.filter(office=office).order_by('-end')[:9]
    for officer in old_officers:
        history.append((officer.brother, officer.start, officer.end))

    return render(request, 'officers/office_history.html',
                  {'office': title, 'history': history, 'more': has_more, 'abbrev': office},
                  context_instance=RequestContext(request))
