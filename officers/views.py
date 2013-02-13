from django.shortcuts import render
from django.template import RequestContext
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required, permission_required
from django.http import Http404, HttpResponseRedirect

from officers.models import *
from officers.forms import OfficerForm

#@login_required
def officers(request):
    officers = []
    incomplete = False
    for key, value in OFFICER_CHOICES:
        try:
            officer = ChapterOfficer.objects.get(office=key)
            officers.append(officer)
        except ChapterOfficer.DoesNotExist:
            #if key != 'HM':
            incomplete = True
    return render(request, 'officers/officers.html', {'officers': officers, 'add': incomplete}, context_instance=RequestContext(request))


@login_required
@permission_required('officers.change_chapterofficer', login_url=settings.FORBIDDEN_URL)
def edit_officer(request, office):
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
            except ChapterOfficer.DoesNotExist:
                prev = None
            if prev is None:
                officer = ChapterOfficer.objects.create(office=office, brother=brother)
                officer.save()
            elif prev.brother != brother:
                history = OfficerHistory.objects.create(office=prev.office, brother=prev.brother, start=prev.updated)
                history.save()
                prev.brother = brother
                prev.save()
            return HttpResponseRedirect(reverse('show_officers'))
    else:
        form = OfficerForm()
    return render(request, 'officers/edit_officer.html', {'form': form, 'title': title, 'office': office}, context_instance=RequestContext(request))


@login_required
@permission_required('officers.add_chapterofficer', login_url=settings.FORBIDDEN_URL)
def add_officer(request):
    error = ''
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
                error = 'Please select a brother from the list below.'
            else:
                officer = ChapterOfficer.objects.create(office=office, brother=brother)
                officer.save()
                return HttpResponseRedirect(reverse('show_officers'))
        else:
            error = 'Please select an office from the list below.'
    missing = []
    for key, value in OFFICER_CHOICES:
        if key != 'HM':
            try:
                ChapterOfficer.objects.get(office=key)
            except ChapterOfficer.DoesNotExist:
                missing.append((key, value))
    if not missing:
        return HttpResponseRedirect(reverse('forbidden'))
    brothers = []
    for brother in UserProfile.objects.filter(status='U'):
        brothers.append((brother.badge, brother.common_name()))
    return render(request, 'officers/add_officer.html', {'offices': missing, 'brothers': brothers, 'error': error}, context_instance=RequestContext(request))


@login_required
def officer_history(request):
    return render(request, 'officers/officer_history.html', context_instance=RequestContext(request))


@login_required
def office_history(request, office):
    title = None
    for key, value in OFFICER_CHOICES:
        if key == office:
            title = value
            break
    if title is None:
        raise Http404
    more = (OfficerHistory.objects.filter(office=office).count() > 9)
    full = (more and 'full' in request.GET and request.GET.get('full') == 'true')
    history = []
    try:
        current = ChapterOfficer.objects.get(office=office)
        history.append((current.brother, current.updated, None))
    except ChapterOfficer.DoesNotExist:
        pass
    if full and more:
        old_officers = OfficerHistory.objects.filter(office=office).order_by('-end')
        more = False
    else:
        old_officers = OfficerHistory.objects.filter(office=office).order_by('-end')[:9]
    for officer in old_officers:
        history.append((officer.brother, officer.start, officer.end))
    return render(request, 'officers/office_history.html', {'office': title, 'history': history, 'more': more, 'abbrev': office}, context_instance=RequestContext(request))
