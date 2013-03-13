"""View functions for the gtphipsi.officers package.

This module exports the following view functions:
    - officers (request)
    - edit_officer (request)
    - add_officer (request)
    - officer_history (request)
    - office_history (request, office)
    - add_office_history (request, office)

"""

from datetime import date
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.template import RequestContext

from gtphipsi.brothers.models import UserProfile
from gtphipsi.common import log_page_view
from gtphipsi.messages import get_message
from gtphipsi.officers.forms import OfficerForm, OfficerHistoryForm
from gtphipsi.officers.models import ChapterOfficer, OfficerHistory, OFFICER_CHOICES


log = logging.getLogger('django')


## ============================================= ##
##                                               ##
##                 Public Views                  ##
##                                               ##
## ============================================= ##


def officers(request):
    """Render a listing of the chapter's current officers."""
    log_page_view(request, 'Officer List')
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

    log_page_view(request, 'Edit Officer')
    title = _get_office_title_or_404(office)

    if request.method == 'POST':
        form = OfficerForm(request.POST)
        if form.is_valid():
            brother = form.cleaned_data.get('brother')
            try:
                prev = ChapterOfficer.objects.get(office=office)
            except ChapterOfficer.DoesNotExist:     # this shouldn't happen, but handle it just in case
                officer = ChapterOfficer.objects.create(office=office, brother=brother, updated=date.today())
                officer.save()
            else:
                if prev.brother != brother:
                    history = OfficerHistory.objects.create(office=prev.office, brother=prev.brother, start=prev.updated, end=date.today())
                    history.save()
                    prev.brother = brother  # just update the existing officer record instead of deleting and recreating
                    prev.updated = date.today()
                    prev.save()
                    log.info('%s (%s) changed %s from %s (#%d) to %s (#%d)', request.user.username, request.user.get_full_name(),
                             office, history.brother.common_name(), history.brother.badge, brother.common_name(), brother.badge)
            return HttpResponseRedirect(reverse('show_officers'))
    else:
        form = OfficerForm()

    return render(request, 'officers/edit_officer.html', {'form': form, 'title': title, 'office': office},
                  context_instance=RequestContext(request))


@login_required
@permission_required('officers.add_chapterofficer', login_url=settings.FORBIDDEN_URL)
def add_officer(request):
    """Render and process a form for administrators to add chapter officers (until all offices are added)."""

    log_page_view(request, 'Add Officer')
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
                officer = ChapterOfficer.objects.create(office=office, brother=brother, updated=date.today())
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
    log_page_view(request, 'Officer History')
    return render(request, 'officers/officer_history.html', context_instance=RequestContext(request))


@login_required
def office_history(request, office):
    """Render a listing of brothers who have held an officer position in the past, including the current officer.

    Required parameters:
        - office    =>  the abbreviation of the office whose history to view as a string (e.g., 'GP')

    """

    log_page_view(request, 'Office History')
    title = _get_office_title_or_404(office)

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


@login_required
@permission_required('officers.add_officerhistory', login_url=settings.FORBIDDEN_URL)
def add_office_history(request, office):
    """Render and process a form to create a new officer history record.

    Required parameters:
        - office    =>  the abbreviation of the office whose history to add as a string (e.g., 'GP')

    """
    log_page_view(request, 'Add Office History')
    title = _get_office_title_or_404(office)
    if request.method == 'POST':
        form = OfficerHistoryForm(request.POST)
        if form.is_valid():
            history = form.save(commit=False)
            history.office = office
            history.save()
            log.info('%s (%s) added history for %s: %s (#%d), %s - %s', request.user.username, request.user.get_full_name(),
                     office, history.brother.common_name(), history.brother.badge, history.start.strftime('%m/%d/%Y'),
                     history.end.strftime('%m/%d/%Y'))
            return HttpResponseRedirect(reverse('office_history', kwargs={'office': office}))
    else:
        form = OfficerHistoryForm()
    return render(request, 'officers/add_office_history.html', {'office': title, 'abbrev': office, 'form': form},
                  context_instance=RequestContext(request))






## ============================================= ##
##                                               ##
##               Private Functions               ##
##                                               ##
## ============================================= ##


def _get_office_title_or_404(abbrev):
    """Return the title of the office corresponding to the given abbreviation; raise Http404 if no such office exists."""
    for key, value in OFFICER_CHOICES:
        if key == abbrev:
            return value
    raise Http404