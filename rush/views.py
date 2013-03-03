import logging
from datetime import datetime

from django.shortcuts import render
from django.template import RequestContext
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.conf import settings
from django.core.mail import get_connection
from django.core.mail.message import EmailMessage
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required, permission_required

from rush.models import Rush, RushEvent, Potential
from rush.forms import RushForm, RushEventForm, PotentialForm, PledgeForm
from chapter.models import InformationCard
from brothers.models import UserProfile, STATUS_BITS
from gtphipsi.messages import get_message as _


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
            card = form.save()      # save the new record to the database
            conn = get_connection() # open a connection to the SMTP backend
            conn.open()
            message = EmailMessage(_('email.infocard.subject'), _('email.infocard.body', args=(
                    card.name, card.created.strftime('%B %d, %Y at %I:%M %p'), card.to_string()
                )), to=[card.email]
            )       # message to the person who submitted the information card
            notification = EmailMessage(_('notify.infocard.subject'), _('notify.infocard.body', args=(
                    card.created.strftime('%B %d, %Y at %I:%M %p'), card.to_string(), settings.URI_PREFIX
                )), to=['membership@gtphipsi.org'], bcc=UserProfile.all_emails_with_bit(STATUS_BITS['EMAIL_NEW_INFOCARD'])
            )       # message to the Membership Chair and everyone who has selected to be notified about new info cards
            conn.send_messages([message, notification])
            conn.close()
            request.META[REFERRER] = reverse('info_card')   # set the HTTP_REFERER header, expected by the 'thanks' view
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
    num_pledges = Potential.objects.filter(rush=rush, pledged=True).count()
    num_potentials = Potential.objects.filter(rush=rush, pledged=False).count()
    return render(request, 'rush/show.html', {'rush': rush, 'pledges': num_pledges, 'potentials': num_potentials}, context_instance=RequestContext(request))


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
            return _get_redirect_from_rush(rush)
    else:
        if 'visible' in request.GET and request.GET['visible'] == 'true':
            rush.visible = True
            rush.save()
            return _get_redirect_from_rush(rush)
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
            rush.updated = datetime.now()
            rush.save()
            return _get_redirect_from_rush(rush)
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
            rush = event.rush
            rush.updated = datetime.now()
            rush.save()
            return _get_redirect_from_rush(event.rush)
    elif 'delete' in request.GET and request.GET['delete'] == 'true':
        event.delete()
        return _get_redirect_from_rush(event.rush)
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


@login_required
def potentials(request, name=None):
    if name is None:
        rush = None
    else:
        try:
            rush = Rush.objects.get(season=name[0], start_date__year=int(name[1:]))
        except Rush.DoesNotExist:
            raise Http404
    if 'all' in request.GET and request.GET.get('all') == 'true':
        hidden = 0
    else:
        hidden = Potential.objects.filter(pledged=False, hidden=True).count()
    if 'order' in request.GET:
        desc = (request.GET.get('order') == 'desc')
    else:
        desc = False
    potentials = _get_potential_queryset(hidden == 0, rush, False, request.GET.get('sort', 'first_name'), desc)
    return render(request, 'rush/potentials.html', {'potentials': potentials, 'rush': rush, 'hidden': hidden, 'current_rush': Rush.current().get_unique_name()}, context_instance=RequestContext(request))


@login_required
def show_potential(request, id):
    try:
        potential = Potential.objects.get(id=id)
    except Potential.DoesNotExist:
        raise Http404
    return render(request, 'rush/potential_show.html', {'potential': potential}, context_instance=RequestContext(request))


@login_required
@permission_required('rush.add_potential', login_url=settings.FORBIDDEN_URL)
def add_potential(request, name=None):
    if name is None:
        rush = None
    else:
        try:
            rush = Rush.objects.get(season=name[0], start_date__year=int(name[1:]))
        except Rush.DoesNotExist:
            raise Http404
    if request.method == 'POST':
        form = PotentialForm(request.POST)
        if form.is_valid():
            potential = form.save(commit=False)
            if rush is not None:
                potential.rush = rush
                rush.updated = datetime.now()
                rush.save()
            potential.save()
            redirect = reverse('all_potentials') if rush is None else reverse('view_rush', kwargs={'name': name})
            return HttpResponseRedirect(redirect)
    else:
        form = PotentialForm() if rush is None else PotentialForm(initial={'rush': rush})
    return render(request, 'rush/add_potential.html', {'form': form, 'rush': rush, 'pledge': False}, context_instance=RequestContext(request))


@login_required
@permission_required('rush.change_potential', login_url=settings.FORBIDDEN_URL)
def edit_potential(request, id):
    try:
        potential = Potential.objects.get(id=id)
    except Potential.DoesNotExist:
        raise Http404
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
    return render(request, 'rush/edit_potential.html', {'form': form, 'potential': potential, 'pledge': False}, context_instance=RequestContext(request))


@login_required
def update_potentials(request, name=None):
    if request.method != 'POST':
        return HttpResponseRedirect(reverse('forbidden'))
    rush = None
    if name is not None:
        try:
            rush = Rush.objects.get(season=name[0], start_date__year=int(name[1:]))
        except Rush.DoesNotExist:
            raise Http404
    action = request.POST.get('action', 'NULL')
    potentials = [int(potential) for potential in request.POST.getlist('potential')]
    if action == 'hide':
        Potential.objects.filter(id__in=potentials).update(hidden=True)
        redirect = reverse('all_potentials') if rush is None else reverse('potentials', kwargs={'name': name})
        return HttpResponseRedirect(redirect)
    return HttpResponse('%s %s' % (action, str(potentials)))



@login_required
def pledges(request, name=None):
    if name is None:
        rush = None
    else:
        try:
            rush = Rush.objects.get(season=name[0], start_date__year=int(name[1:]))
        except Rush.DoesNotExist:
            raise Http404
    if 'order' in request.GET:
        desc = (request.GET.get('order') == 'desc')
    else:
        desc = False
    if rush is None:
        if 'all' in request.GET and request.GET.get('all') == 'true':
            hidden = 0
            all = True
        else:
            hidden = Potential.objects.filter(hidden=True).count()
            all = False
    else:
        hidden = 0
        all = True
    pledges = _get_potential_queryset(all, rush, True, request.GET.get('sort', 'first_name'), desc)
    return render(request, 'rush/pledges.html', {'pledges': pledges, 'hidden': hidden, 'rush': rush, 'current_rush': Rush.current().get_unique_name()}, context_instance=RequestContext(request))


@login_required
def show_pledge(request, id):
    try:
        pledge = Potential.objects.get(id=id)
    except Potential.DoesNotExist:
        raise Http404
    return render(request, 'rush/potential_show.html', {'potential': pledge}, context_instance=RequestContext(request))


@login_required
@permission_required('rush.add_potential', login_url=settings.FORBIDDEN_URL)
def add_pledge(request, name=None):
    if name is None:
        rush = None
    else:
        try:
            rush = Rush.objects.get(season=name[0], start_date__year=int(name[1:]))
        except Rush.DoesNotExist:
            raise Http404
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
                redirect = reverse('view_rush', kwargs={'name': name})
            return HttpResponseRedirect(redirect)
    else:
        form = PledgeForm() if rush is None else PotentialForm(initial={'rush': rush})
    return render(request, 'rush/add_potential.html', {'form': form, 'rush': rush, 'pledge': True}, context_instance=RequestContext(request))


@login_required
@permission_required('rush.change_potential', login_url=settings.FORBIDDEN_URL)
def edit_pledge(request, id):
    try:
        pledge = Potential.objects.get(id=id)
    except Potential.DoesNotExist:
        raise Http404
    if request.method == 'POST':
        form = PledgeForm(request.POST, instance=pledge)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('show_pledge', kwargs={'id': id}))
    else:
        if 'delete' in request.GET and request.GET.get('delete') == 'true':
            if pledge.rush:
                redirect = reverse('potentials', kwargs={'name': pledge.rush.get_unique_name()})
            else:
                redirect = reverse('all_potentials')
            pledge.delete()
            return HttpResponseRedirect(redirect)
        form = PledgeForm(instance=pledge)
    return render(request, 'rush/edit_potential.html', {'form': form, 'potential': pledge, 'pledge': True}, context_instance=RequestContext(request))






## ============================================= ##
##                                               ##
##               Private Functions               ##
##                                               ##
## ============================================= ##

def _get_potential_queryset(all, rush, pledge, sort_by='first_name', desc=False):
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
    if sort_by == 'name':
        sort_by = 'first_name'
    elif sort_by == 'date':
        sort_by = 'created'
    elif sort_by not in ['phone', 'rush']:
        sort_by = 'first_name'
    return queryset.order_by('-%s' % sort_by) if desc else queryset.order_by(sort_by)


def _get_redirect_from_rush(rush):
    return HttpResponseRedirect(reverse('current_rush')) if rush.is_current() else HttpResponseRedirect(reverse('view_rush', kwargs={'name': rush.get_unique_name()}))