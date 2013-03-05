"""View functions for the gtphipsi.rush package.

This module exports the following view functions:
    - rush (request)
    - rushphipsi (request)
    - schedule (request)
    - old_schedule (request)
    - info_card (request)
    - info_card_thanks (request)
    - list (request)
    - show (request[, name])
    - add (request)
    - edit (request, name)
    - add_event (request, name)
    - edit_event (request, id)
    - info_card_list (request)
    - info_card_show (request, id)
    - potentials (request[, name])
    - show_potential (request, id)
    - add_potential (request[, name])
    - edit_potential (request, id)
    - update_potentials (request[, name])
    - pledges (request[, name])
    - show_pledge (request, id)
    - add_pledge (request[, name])
    - edit_pledge (request, id)

"""

from datetime import datetime
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.core.mail import get_connection
from django.core.mail.message import EmailMessage
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.template import RequestContext

from gtphipsi.brothers.models import UserProfile, STATUS_BITS
from gtphipsi.chapter.forms import InformationForm
from gtphipsi.chapter.models import InformationCard
from gtphipsi.common import REFERRER
from gtphipsi.messages import get_message
from gtphipsi.rush.forms import PledgeForm, PotentialForm, RushEventForm, RushForm
from gtphipsi.rush.models import Potential, Rush, RushEvent


log = logging.getLogger('django')


## ============================================= ##
##                                               ##
##                 Public Views                  ##
##                                               ##
## ============================================= ##


def rush(request):
    """Render a page of text containing general information about fraternity rush."""
    return render(request, 'rush/rush.html', context_instance=RequestContext(request))


def rush_phi_psi(request):
    """Render a page of text containing information about rushing Phi Kappa Psi."""
    return render(request, 'rush/phipsi.html', context_instance=RequestContext(request))


def schedule(request):
    """Render a schedule of events for the current rush."""
    current_rush = Rush.current()
    if current_rush is None:
        raise Http404
    return render(request, 'rush/schedule.html', {'rush': current_rush}, context_instance=RequestContext(request))


def old_schedule(request):
    """Render a schedule of events for the current rush (exactly the same as the 'schedule' view).

    For backward compatibility, we need to support the URI '/rushschedule.php'. We also want there to be a distinct
    (and clean) URI for the rush schedule, i.e., reverse('rush_schedule') should resolve successfully. So, we use this
    view as a pass-through to convert the old URI to the new one.

    """
    return HttpResponseRedirect(reverse('rush_schedule'))


def info_card(request):
    """Render and process a form for potential members to provide information about themselves to the chapter."""
    if request.method == 'POST':
        form = InformationForm(request.POST)
        if form.is_valid():
            card = form.save()
            _send_info_card_emails(card)
            request.META[REFERRER] = reverse('info_card')   # set the HTTP_REFERER header, expected by the 'thanks' view
            return HttpResponseRedirect(reverse('info_card_thanks'))
    else:
        form = InformationForm()
    return render(request, 'rush/infocard.html', {'form': form}, context_instance=RequestContext(request))


def info_card_thanks(request):
    """Render a 'thanks' view after processing a new information card."""
    if REFERRER not in request.META or not request.META[REFERRER].endswith(reverse('info_card')):
        raise Http404
    return render(request, 'rush/infocard_thanks.html', context_instance=RequestContext(request))




## ============================================= ##
##                                               ##
##              Authenticated Views              ##
##                                               ##
## ============================================= ##


@login_required
def list(request):
    """Render a listing of rushes."""
    return render(request, 'rush/list.html', {'rushes': Rush.objects.all()}, context_instance=RequestContext(request))


@login_required
def show(request, name=None):
    """Render a display of information about a particular rush.

    Optional parameters:
        - name  =>  the unique name (abbreviation) of the rush to view (as a string): defaults to the current rush

    """
    if name is None:
        rush = Rush.current()       # use the most recent visible rush (if there is one)
        if rush is None:
            return HttpResponseRedirect(reverse('rush_list'))
    else:
        rush = _get_rush_or_404(name)  # look up by unique name
    num_pledges = Potential.objects.filter(rush=rush, pledged=True).count()
    num_potentials = Potential.objects.filter(rush=rush, pledged=False).count()
    return render(request, 'rush/show.html', {'rush': rush, 'pledges': num_pledges, 'potentials': num_potentials},
                  context_instance=RequestContext(request))


@login_required
@permission_required('rush.add_rush', login_url=settings.FORBIDDEN_URL)
def add(request):
    """Render and process a form for users to create new rushes."""
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
    """Render and process a form for users to modify an existing rush.

    Required parameters:
        - name  =>  the unique name (abbreviation) of the rush to edit (as a string)

    """
    rush = _get_rush_or_404(name)
    if request.method == 'POST':
        form = RushForm(request.POST, instance=rush)
        if form.is_valid():
            form.save()
            return _get_redirect_from_rush(rush)
    else:
        if 'visible' in request.GET and request.GET.get('visible') == 'true':
            rush.visible = True
            rush.save()
            return _get_redirect_from_rush(rush)
        if 'delete' in request.GET and request.GET.get('delete') == 'true':
            name = rush.title()
            rush.delete()
            log.info('User %s (badge %d) deleted %s', request.user.get_full_name(), request.user.get_profile().badge, name)
            return HttpResponseRedirect(reverse('rush_list'))
        form = RushForm(instance=rush)
    return render(request, 'rush/edit.html', {'rush_name': name, 'form': form}, context_instance=RequestContext(request))


@login_required
@permission_required('rush.add_rushevent', login_url=settings.FORBIDDEN_URL)
def add_event(request, name):
    """Render and process a form for users to create new rush events.

    Required parameters:
        - name  =>  the unique name (abbreviation) of the rush to which the new event should belong (as a string)

    """
    rush = _get_rush_or_404(name)
    if request.method == 'POST':
        form = RushEventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.rush = rush
            event.save()
            rush.updated = datetime.now()
            rush.save()
            return _get_redirect_from_rush(rush)
    else:
        form = RushEventForm(initial={'rush': rush})
    return render(request, 'rush/add_event.html', {'rush': rush, 'form': form}, context_instance=RequestContext(request))


@login_required
@permission_required('rush.change_rushevent', login_url=settings.FORBIDDEN_URL)
def edit_event(request, id):
    """Render and process a form for users to modify an existing rush event.

    Required parameters:
        - id    =>  the unique ID of the rush event to edit (as an integer)

    """
    event = get_object_or_404(RushEvent, id=id)
    if request.method == 'POST':
        form = RushEventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            rush = event.rush
            rush.updated = datetime.now()
            rush.save()
            return _get_redirect_from_rush(rush)
    else:
        if 'delete' in request.GET and request.GET.get('delete') == 'true':
            event.delete()
            return _get_redirect_from_rush(event.rush)
        form = RushEventForm(instance=event)
    return render(request, 'rush/edit_event.html', {'event_id': event.id, 'form': form},
                  context_instance=RequestContext(request))


@login_required
def info_card_list(request):
    """Render a listing of all information cards that have been submitted to the chapter."""
    return render(request, 'rush/infocard_list.html', {'cards': InformationCard.objects.all()},
                  context_instance=RequestContext(request))


@login_required
def info_card_show(request, id):
    """Render a display of information about a particular information card.

    Required parameters:
        - id    =>  the unique ID of the information card to view (as an integer)

    """
    card = get_object_or_404(InformationCard, id=id)
    return render(request, 'rush/infocard_show.html', {'card': card}, context_instance=RequestContext(request))


@login_required
def potentials(request, name=None):
    """Render a listing of potential members, including all potentials or only those from a specific rush.

    Optional parameters:
        - name => the unique name (abbreviation) of the rush for which to show potentials (as a string): defaults to all

    """
    rush = _get_rush_or_404(name)
    if 'all' in request.GET and request.GET.get('all') == 'true':
        hidden = 0
    else:
        hidden = Potential.objects.filter(pledged=False, hidden=True).count()
    descending = (request.GET.get('order', '') == 'desc')     # ascending order by default
    potentials = _get_potential_queryset(hidden == 0, rush, False, request.GET.get('sort', 'name'), descending)
    current_rush = None if Rush.current() is None else Rush.current().get_unique_name()
    return render(request, 'rush/potentials.html',
                  {'potentials': potentials, 'rush': rush, 'hidden': hidden, 'current_rush': current_rush},
                  context_instance=RequestContext(request))


@login_required
def show_potential(request, id):
    """Render a display of information about a potential member.

    Required parameters:
        - id    =>  the unique ID of the potential to view (as an integer)

    """
    potential = get_object_or_404(Potential, id=id)
    return render(request, 'rush/potential_show.html', {'potential': potential}, context_instance=RequestContext(request))


@login_required
@permission_required('rush.add_potential', login_url=settings.FORBIDDEN_URL)
def add_potential(request, name=None):
    """Render and process a form for users to create records of new potential members.

    Optional parameters:
        - name  =>  the unique name (abbreviation) of the rush with which to associate the potential: defaults to none

    """
    rush = _get_rush_or_404(name)
    if request.method == 'POST':
        form = PotentialForm(request.POST)
        if form.is_valid():
            potential = form.save(commit=False)
            if rush is not None:
                potential.rush = rush
                rush.updated = datetime.now()
                rush.save()
            potential.save()
            redirect = reverse('all_potentials') if rush is None else rush.get_absolute_url()
            return HttpResponseRedirect(redirect)
    else:
        form = PotentialForm() if rush is None else PotentialForm(initial={'rush': rush})
    return render(request, 'rush/add_potential.html', {'form': form, 'rush': rush, 'pledge': False},
                  context_instance=RequestContext(request))


@login_required
@permission_required('rush.change_potential', login_url=settings.FORBIDDEN_URL)
def edit_potential(request, id):
    """Render and process a form for users to modify information about an existing potential.

    Required parameters:
        - id    =>  the unique ID of the potential to edit (as an integer)

    """
    potential = get_object_or_404(Potential, id=id)
    if request.method == 'POST':
        form = PotentialForm(request.POST, instance=potential)
        if form.is_valid():
            form.save()
            if form.cleaned_data['pledged']:
                redirect = reverse('show_pledge', kwargs={'id': id})
            else:
                redirect = reverse('show_potential', kwargs={'id': id})
            return HttpResponseRedirect(redirect)
    else:
        if 'delete' in request.GET and request.GET.get('delete') == 'true':
            if potential.rush:
                redirect = reverse('potentials', kwargs={'name': potential.rush.get_unique_name()})
            else:
                redirect = reverse('all_potentials')
            potential.delete()
            return HttpResponseRedirect(redirect)
        form = PotentialForm(instance=potential)
    return render(request, 'rush/edit_potential.html', {'form': form, 'potential': potential, 'pledge': False},
                  context_instance=RequestContext(request))


@login_required
def update_potentials(request, name=None):
    """Process a request to modify several potential members simultaneously.

    Optional parameters:
        - name  =>  the unique name of the rush with which the potentials are associated (as a string): defaults to none

    """
    if request.method != 'POST':
        return HttpResponseRedirect(reverse('forbidden'))
    rush = _get_rush_or_404(name)
    action = request.POST.get('action', 'NULL')
    potentials = [int(potential) for potential in request.POST.getlist('potential')]
    if action == 'hide':
        Potential.objects.filter(id__in=potentials).update(hidden=True)
        redirect = reverse('all_potentials') if rush is None else reverse('potentials', kwargs={'name': name})
        return HttpResponseRedirect(redirect)
    # TODO - complete this function!!
    return HttpResponse('%s %s' % (action, str(potentials)))



@login_required
def pledges(request, name=None):
    """Render a listing of pledges, either all pledges or only those from a specific rush (semester).

    Optional parameters:
        - name => the unique name (abbreviation) of the rush to which to restrict the listing; defaults to all rushes

    """
    rush = _get_rush_or_404(name)
    if rush is not None or ('all' in request.GET and request.GET.get('all') == 'true'):
        hidden = 0
    else:
        hidden = Potential.objects.filter(hidden=True).count()
    descending = (request.GET.get('order', '') == 'desc')     # ascending order by default
    pledges = _get_potential_queryset(hidden == 0, rush, True, request.GET.get('sort', 'name'), descending)
    current_rush = None if Rush.current() is None else Rush.current().get_unique_name()
    return render(request, 'rush/pledges.html',
                  {'pledges': pledges, 'hidden': hidden, 'rush': rush, 'current_rush': current_rush},
                  context_instance=RequestContext(request))


@login_required
def show_pledge(request, id):
    """Render a display of information about a particular pledge.

    Required parameter:
        - id    => the unique ID of the pledge to view (as an integer)

    """
    pledge = get_object_or_404(Potential, id=id)
    return render(request, 'rush/potential_show.html', {'potential': pledge}, context_instance=RequestContext(request))


@login_required
@permission_required('rush.add_potential', login_url=settings.FORBIDDEN_URL)
def add_pledge(request, name=None):
    """Render and process a form for users to create records of new pledges.

    Optional parameters:
        - name  =>  the unique name (abbreviation) of the rush with which to associate the pledge: defaults to none

    """
    rush = _get_rush_or_404(name)
    if request.method == 'POST':
        form = PledgeForm(request.POST)
        if form.is_valid():
            pledge = form.save(commit=False)
            pledge.pledged = True
            pledge.save()
            if rush is None:
                redirect = reverse('all_pledges')
            else:
                rush.updated = datetime.now()
                rush.save()
                redirect = reverse('pledges', kwargs={'name': name})
            return HttpResponseRedirect(redirect)
    else:
        form = PledgeForm() if rush is None else PledgeForm(initial={'rush': rush})
    return render(request, 'rush/add_potential.html', {'form': form, 'rush': rush, 'pledge': True},
                  context_instance=RequestContext(request))


@login_required
@permission_required('rush.change_potential', login_url=settings.FORBIDDEN_URL)
def edit_pledge(request, id):
    """Render and process a form for users to modify information about an existing pledge.

    Required parameters:
        - id    =>  the unique ID of the pledge to edit (as an integer)

    """
    pledge = get_object_or_404(Potential, id=id)
    if request.method == 'POST':
        form = PledgeForm(request.POST, instance=pledge)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(pledge.get_absolute_url())
    else:
        if 'delete' in request.GET and request.GET.get('delete') == 'true':
            if pledge.rush:
                redirect = reverse('pledges', kwargs={'name': pledge.rush.get_unique_name()})
            else:
                redirect = reverse('all_pledges')
            pledge.delete()
            return HttpResponseRedirect(redirect)
        form = PledgeForm(instance=pledge)
    return render(request, 'rush/edit_potential.html', {'form': form, 'potential': pledge, 'pledge': True},
                  context_instance=RequestContext(request))






## ============================================= ##
##                                               ##
##               Private Functions               ##
##                                               ##
## ============================================= ##


def _get_rush_or_404(name):
    """Return the rush instance having the provided unique name, if one exists.

    Required parameters:
        - name  =>  the unique name (abbreviation) of the rush to find (as a string)

    If 'name' is None, the function returns None. Otherwise, the function looks for a rush with the provided unique
    name, in the format returned by the get_unique_name() method of the Rush model class. If a matching rush is found,
    it is returned; if not, Http404 is raised.

    """
    return None if name is None else get_object_or_404(Rush, season=name[0], start_date__year=int(name[1:]))


def _send_info_card_emails(card):
    """Send an email thanking a potential for submitting an information card; email brothers who want to be notified.

    Required parameters:
        - card  =>  the information card about which to email

    """
    date = card.created.strftime('%B %d, %Y at %I:%M %p')
    # message to the person who submitted the information card
    message = EmailMessage(get_message('email.infocard.subject'),
                           get_message('email.infocard.body', args=(card.name, date, card.to_string())), to=[card.email])
    # message to the Membership Chair and everyone who has selected to be notified about new info cards
    notification = EmailMessage(get_message('notify.infocard.subject'),
                                get_message('notify.infocard.body', args=(date, card.to_string(), settings.URI_PREFIX)),
                                to=['membership@gtphipsi.org'],
                                bcc=UserProfile.all_emails_with_bit(STATUS_BITS['EMAIL_NEW_INFOCARD']))
    # open a connection to the SMTP backend so we can send two messages over the same connection
    conn = get_connection()
    conn.open()
    conn.send_messages([message, notification])
    conn.close()


def _get_potential_queryset(all, rush, pledge, sort_by='name', desc=False):
    """Return a queryset of potentials or pledges filtered and sorted based on the provided parameters.

    Required parameters:
        - all       =>  whether to include all potentials or only those not marked as hidden (as a boolean)
        - rush      =>  the rush to which to limit results, or None to include results from all rushes
        - pledge    =>  whether to include pledges or potentials (as a boolean)

    Optional parameters:
        - sort_by   => the field by which to sort the results (one of 'name', 'date', 'phone', 'rush'): defaults to name
        - desc      => whether to sort the results in descending order (as a boolean): defaults to ascending order

    """
    if rush is None:
        if all:
            queryset = Potential.objects.filter(pledged=pledge)
        else:
            queryset = Potential.objects.filter(hidden=False, pledged=pledge)
    else:
        if all:
            queryset = Potential.objects.filter(pledged=pledge, rush=rush)
        else:
            queryset = Potential.objects.filter(hidden=False, rush=rush, pledged=pledge)
    map = {'name': 'first_name', 'date': 'created', 'phone': 'phone', 'rush': 'rush'}
    sort_by = map[sort_by] if map.has_key(sort_by) else 'first_name'
    return queryset.order_by('-%s' % sort_by) if desc else queryset.order_by(sort_by)


def _get_redirect_from_rush(rush):
    """Return an instance of HttpResponseRedirect based on whether the provided rush is the current rush or not.

    Required parameters:
        - rush  =>  the rush for which to obtain a redirection

    """
    if rush.is_current():
        redirect = HttpResponseRedirect(reverse('current_rush'))
    else:
        redirect = HttpResponseRedirect(rush.get_absolute_url())
    return redirect
