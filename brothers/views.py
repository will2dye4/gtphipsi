import hashlib
import logging
from re import match

from django.db.models import Min
from django.shortcuts import render
from django.template import RequestContext
from django.conf import settings
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User, Permission, Group
from django.http import Http404, HttpResponseRedirect

from gtphipsi.messages import get_message
from gtphipsi.common import get_name_from_badge, create_user_and_profile
from brothers.models import UserProfile, EmailChangeRequest, STATUS_BITS
from brothers.forms import UserForm, EditProfileForm, EditAccountForm, PublicVisibilityForm, ChapterVisibilityForm, ChangePasswordForm, NotificationSettingsForm
from brothers.bootstrap import INITIAL_BROTHER_LIST as IBL


log = logging.getLogger('django')


# visible to all users
def list(request):
    columns = 3
    undergrad_rows, num_undergrads = _get_brother_listing(num_cols=columns)
    alumni_rows, num_alumni = _get_brother_listing(False, columns)
    context = {'undergrad_rows': undergrad_rows, 'num_undergrads': num_undergrads, 'alumni_rows': alumni_rows, 'col_width': 100/columns}
    return render(request, 'brothers/list.html', context, context_instance=RequestContext(request))


# visible to all users
def show(request, badge=0):
    try:
        profile = UserProfile.objects.get(badge=badge)
        user = profile.user
    except (UserProfile.DoesNotExist, User.DoesNotExist):
        name = get_name_from_badge(int(badge))
        if name is None:
            raise Http404
        min = _get_lowest_undergrad_badge()
        status = 'Undergraduate' if int(badge) > min else 'Alumnus'
        context = {'account': None, 'name': name, 'badge': badge, 'status': status}
    else:
        show_public = ('public' in request.GET and request.GET['public'] == 'true') or request.user.is_anonymous()
        visibility = profile.public_visibility if show_public else profile.chapter_visibility
        fields = get_fields_from_profile(profile, visibility)
        chapter_fields, personal_fields, contact_fields = get_field_categories(fields)
        big_bro = None
        if 'Big brother' in fields:
            try:
                big_bro = '%s ... %d' % (UserProfile.objects.get(badge=profile.big_brother).common_name(), profile.big_brother)
            except UserProfile.DoesNotExist:
                big_bro = '%s ... %d' % (get_name_from_badge(profile.big_brother), profile.big_brother)
        context = {'own_account': (user.id == request.user.id), 'account': user, 'profile': profile, 'public': show_public,
                   'big': big_bro, 'fields': fields, 'chapter_fields': chapter_fields, 'personal_fields': personal_fields,
                   'contact_fields': contact_fields
        }
    return render(request, 'brothers/show.html', context, context_instance=RequestContext(request))


# visible to all users
def change_email(request):
    if 'hash' in request.GET:
        try:
            req = EmailChangeRequest.objects.get(hash=request.GET.get('hash'))
        except EmailChangeRequest.DoesNotExist:
            raise Http404
        user = req.user
        user.email = req.email
        user.save()
        req.delete()
        return HttpResponseRedirect(reverse('change_email_success'))
    return HttpResponseRedirect(reverse('home'))


# visible to all users
def change_email_success(request):
    return render(request, 'brothers/change_email_success.html', context_instance=RequestContext(request))


@login_required
def my_profile(request):
    return show(request, request.user.get_profile().badge)


@login_required
@permission_required('brothers.change_userprofile', login_url=settings.FORBIDDEN_URL)
def manage(request):
    undergrad_profiles = UserProfile.objects.filter(status='U')
    undergrads = User.objects.filter(pk__in=[profile.user.id for profile in undergrad_profiles])
    locked_out_undergrads = [profile.user for profile in undergrad_profiles if profile.has_bit(STATUS_BITS['LOCKED_OUT'])]
    alumni_profiles = UserProfile.objects.filter(status='A')
    alumni = User.objects.filter(pk__in=[profile.user.id for profile in alumni_profiles])
    locked_out_alumni = [profile.user for profile in alumni_profiles if profile.has_bit(STATUS_BITS['LOCKED_OUT'])]
    params = {
        'undergrads': undergrads,
        'alumni': alumni,
        'locked_out_undergrads': locked_out_undergrads,
        'locked_out_alumni': locked_out_alumni
    }
    return render(request, 'brothers/manage.html', params, context_instance=RequestContext(request))


@login_required
@permission_required('brothers.add_userprofile', login_url=settings.FORBIDDEN_URL)
def add(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            create_user_and_profile(form.cleaned_data)
            log.info('Admin %s (badge %d) created new user %s (%s %s)', request.user.get_full_name(),
                    request.user.get_profile().badge, form.cleaned_data['username'], form.cleaned_data['first_name'],
                    form.cleaned_data['last_name'])
            return HttpResponseRedirect(reverse('manage_users'))
    else:
        form = UserForm()
    return render(request, 'brothers/add.html', {'form': form, 'secret_key': settings.BROTHER_KEY, 'admin_password': settings.ADMIN_KEY}, context_instance=RequestContext(request))


@login_required
def edit(request):
    try:
        user = User.objects.get(pk=request.user.id)
    except User.DoesNotExist:
        raise Http404

    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=user.get_profile())
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('my_profile'))
    else:
        form = EditProfileForm(instance=user.get_profile())
    return render(request, 'brothers/edit.html', {'form': form}, context_instance=RequestContext(request))


@login_required
@permission_required('brothers.change_userprofile', login_url=settings.FORBIDDEN_URL)
def unlock(request, badge):
    try:
        profile = UserProfile.objects.get(badge=badge)
    except UserProfile.DoesNotExist:
        raise Http404

    if profile.has_bit(STATUS_BITS['LOCKED_OUT']):
        profile.clear_bit(STATUS_BITS['LOCKED_OUT'])
        profile.save()
    return HttpResponseRedirect(reverse('manage_users'))


@login_required
def edit_account(request, badge=0):
    try:
        user = UserProfile.objects.get(badge=badge).user if badge else request.user
    except UserProfile.DoesNotExist:
        raise Http404
    own_account = (user == request.user)
    if not (own_account or request.user.get_profile().is_admin()):
        return HttpResponseRedirect(reverse('forbidden'))
    elif request.method == 'POST':
        profile = user.get_profile()
        form = EditAccountForm(request.POST)
        if form.is_valid():
            first, middle, last = form.cleaned_data['first_name'], form.cleaned_data['middle_name'], form.cleaned_data['last_name']
            nickname, suffix = form.cleaned_data['nickname'], form.cleaned_data['suffix']
            email, status = form.cleaned_data['email'], form.cleaned_data['status']
            save_user = False
            if first != user.first_name or last != user.last_name:
                user.first_name = first
                user.last_name = last
                save_user = True
            profile.middle_name = middle
            profile.nickname = nickname
            profile.suffix = suffix
            if status != profile.status:
                old_status = profile.status
                profile.status = status
                save_user = process_status_change(user, old_status, status) or save_user
            if email != user.email:
                digest = hashlib.sha224('%d-%s' % (profile.badge, email)).hexdigest()
                req = EmailChangeRequest(user=user, email=email, hash=digest)
                req.save()
                send_mail(get_message('email.change.subject'), get_message('email.change.body', args=(
                        user.first_name, settings.URI_PREFIX, digest
                    )), 'webmaster@gtphipsi.org', [email]
                )
                # TODO notify user to check his email
            profile.save()
            if save_user:
                user.save()
            if own_account:
                redirect = HttpResponseRedirect(reverse('my_profile'))
            else:
                log.info('Admin %s (badge %d) edited account details of %s (%s %s)', request.user.get_full_name(), request.user.get_profile().badge, user.username, first, last)
                redirect = HttpResponseRedirect(reverse('view_profile', args=[user.get_profile().badge]))
            return redirect
    else:
        profile = user.get_profile()
        form = EditAccountForm(initial={'first_name': user.first_name,
                                        'middle_name': profile.middle_name,
                                        'last_name': user.last_name,
                                        'nickname': profile.nickname,
                                        'suffix': profile.suffix,
                                        'email': user.email,
                                        'status': profile.status
        })
    params = {'form': form, 'name': user.get_full_name(), 'own_account': own_account, 'badge': user.get_profile().badge if (badge and not own_account) else None}
    return render(request, 'brothers/edit_account.html', params, context_instance=RequestContext(request))


@login_required
def change_password(request):
    user = request.user
    try:
        profile = user.get_profile()
    except UserProfile.DoesNotExist:
        profile = None
    reset = profile is not None and profile.has_bit(STATUS_BITS['PASSWORD_RESET'])

    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        form.user = user
        if form.is_valid():
            user.set_password(form.cleaned_data['password'])
            user.save()
            if reset:
                profile.clear_bit(STATUS_BITS['PASSWORD_RESET'])
                profile.save()
            # TODO email user about password change ??
            return HttpResponseRedirect(reverse('change_password_success'))
    else:
        form = ChangePasswordForm()
        form.user = user

    message = 'Your password was recently reset. ' \
              'Please use the form below to change your password to something more memorable. ' \
              'You will need the temporary password you were emailed.' if reset else None

    return render(request, 'brothers/change_password.html', {'form': form, 'message': message}, context_instance=RequestContext(request))


@login_required
def change_password_success(request):
    return render(request, 'brothers/change_password_success.html', context_instance=RequestContext(request))


@login_required
@permission_required('auth.change_group', login_url=settings.FORBIDDEN_URL)
def manage_groups(request):
    if request.GET.get('view', '') == 'members':
        groups = Group.objects.all()
        map = {}
        for group in groups:
            user_ids = [user.id for user in User.objects.filter(groups__id__exact=group.id)]
            names = ['%s ... %d' % (profile.common_name(), profile.badge) for profile in UserProfile.objects.filter(user__id__in=user_ids).order_by('badge')]
            map[group.name] = names
        context = {'map': map, 'show_perms': False}
    else:
        groups = Group.objects.all()
        context = {'groups': groups, 'show_perms': True}
    return render(request, 'brothers/manage_groups.html', context, context_instance=RequestContext(request))


@login_required
@permission_required('auth.add_group', login_url=settings.FORBIDDEN_URL)
def add_group(request):
    error = ''
    initial_name = ''
    if request.method == 'POST':
        ids = []
        group_name = None
        for name, value in request.POST.items():
            if name.find('perm_') > -1:
                ids.append(int(value))
            elif name == 'group_name':
                initial_name = value
                if match(r'^[a-zA-Z0-9_]+[a-zA-Z0-9_ ]*[a-zA-Z0-9]+$', value) is None:
                    error = 'The group name you entered is invalid. Please enter a different name.'
                elif Group.objects.filter(name=value).count() > 0:
                    error = 'A group with that name already exists. Please enter a different name.'
                else:
                    group_name = value
        if not len(ids) and not error:
            error = 'You must select at least one permission for this group.'
        if group_name is None and not error:
            error = 'You must enter a name for this group.'
        if not error:
            group = Group.objects.create(name=group_name)
            group.permissions = Permission.objects.filter(id__in=ids)
            group.save()
            return HttpResponseRedirect(reverse('view_group', kwargs={'name': group.name}))
    perms = get_available_permissions()
    choices = [[perm.id, perm.name] for perm in perms]
    return render(request, 'brothers/add_group.html', {'error': error, 'name': initial_name, 'perms': choices}, context_instance=RequestContext(request))



@login_required
@permission_required('auth.change_group', login_url=settings.FORBIDDEN_URL)
def edit_group_perms(request, name):
    try:
        group = Group.objects.get(name=name)
    except Group.DoesNotExist:
        raise Http404
    if request.method == 'POST':
        ids = []
        for name, value in request.POST.items():
            if name.find('perm_') > -1:
                ids.append(int(value))
        new_perms = Permission.objects.filter(id__in=ids)
        group.permissions = [perm for perm in new_perms]
        group.save()
        return HttpResponseRedirect(reverse('view_group', kwargs={'name': group.name}))
    else:
        perms = get_available_permissions()
        group_perms = group.permissions.all()
        choices = []
        initial = []
        for perm in perms:
            choices.append([perm.id, perm.name])
            if perm in group_perms:
                initial.append(perm.id)
    return render(request, 'brothers/edit_group_perms.html', {'group_name': group.name, 'perms': choices, 'initial': initial}, context_instance=RequestContext(request))


@login_required
@permission_required('auth.change_group', login_url=settings.FORBIDDEN_URL)
def edit_group_members(request, name):
    try:
        group = Group.objects.get(name=name)
    except Group.DoesNotExist:
        raise Http404

    users = User.objects.all()
    if request.method == 'POST':
        ids = []
        for name, value in request.POST.items():
            if name.find('user_') > -1:
                ids.append(int(value))
        new_users = User.objects.filter(id__in=ids)
        for user in users:
            if user in new_users and group not in user.groups.all():
                user.groups.add(group)
                user.save()
            elif user not in new_users and group in user.groups.all():
                user.groups.remove(group)
                user.save()
        return HttpResponseRedirect(reverse('view_group', kwargs={'name': group.name}))
    else:
        group_members = User.objects.filter(groups__id__exact=group.id)
        choices = []
        initial = []
        for user in users:
            choices.append([user.id, '%s ... %d' % (user.get_full_name(), user.get_profile().badge)])
            if user in group_members:
                initial.append(user.id)
    return render(request, 'brothers/edit_group_members.html', {'group_name': group.name, 'choices': choices, 'initial': initial}, context_instance=RequestContext(request))


@login_required
@permission_required('auth.delete_group', login_url=settings.FORBIDDEN_URL)
def delete_group(request, name):
    try:
        group = Group.objects.get(name=name)
    except Group.DoesNotExist:
        raise Http404
    for user in group.user_set.all():
        user.groups.remove(group)
        user.save()
    group.delete()
    return HttpResponseRedirect(reverse('manage_groups'))


@login_required
@permission_required('auth.change_group', login_url=settings.FORBIDDEN_URL)
def show_group(request, name):
    try:
        group = Group.objects.get(name=name)
    except Group.DoesNotExist:
        raise Http404
    user_ids = [user.id for user in User.objects.filter(groups__id__exact=group.id)]
    names = ['%s ... %d' % (profile.common_name(), profile.badge) for profile in UserProfile.objects.filter(user__id__in=user_ids).order_by('badge')]
    return render(request, 'brothers/show_group.html', {'group': group, 'users': names}, context_instance=RequestContext(request))


@login_required
def visibility(request):
    profile = request.user.get_profile()
    public = profile.public_visibility
    chapter = profile.chapter_visibility
    fields = get_fields_from_profile(profile)
    return render(request, 'brothers/visibility.html', {'fields': fields, 'public': public, 'chapter': chapter}, context_instance=RequestContext(request))


@login_required
def edit_visibility(request, public=True):
    visibility = request.user.get_profile().public_visibility if public else request.user.get_profile().chapter_visibility
    fields = get_fields_from_profile(request.user.get_profile())
    vis_type = 'public' if public else 'chapter'
    message = get_message('visibility.edit.public') if public else get_message('visibility.edit.chapter')
    full_name_msg = get_message('visibility.fullname')
    if request.method == 'POST':
        form = PublicVisibilityForm(request.POST, instance=visibility) if public else ChapterVisibilityForm(request.POST, instance=visibility)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('visibility'))
    else:
        form = PublicVisibilityForm(instance=visibility) if public else ChapterVisibilityForm(instance=visibility)
    return render(request, 'brothers/edit_visibility.html', {'form': form, 'fields': fields, 'type': vis_type, 'message': message, 'name_msg': full_name_msg}, context_instance=RequestContext(request))


@login_required
def edit_public_visibility(request):
    return edit_visibility(request)


@login_required
def edit_chapter_visibility(request):
    return edit_visibility(request, False)


@login_required
def edit_notification_settings(request):
    try:
        profile = UserProfile.objects.get(user__id=request.user.id)
    except UserProfile.DoesNotExist:
        raise Http404
    initial = {
        'infocard': profile.has_bit(STATUS_BITS['EMAIL_NEW_INFOCARD']),
        'contact': profile.has_bit(STATUS_BITS['EMAIL_NEW_CONTACT']),
        'announcement': profile.has_bit(STATUS_BITS['EMAIL_NEW_ANNOUNCEMENT'])
    }
    if request.method == 'POST':
        form = NotificationSettingsForm(request.POST, initial=initial)
        if form.is_valid():
            old_bits = profile.bits
            if form.cleaned_data['infocard'] and not initial['infocard']:
                profile.set_bit(STATUS_BITS['EMAIL_NEW_INFOCARD'])
            elif not form.cleaned_data['infocard'] and initial['infocard']:
                profile.clear_bit(STATUS_BITS['EMAIL_NEW_INFOCARD'])

            if form.cleaned_data['contact'] and not initial['contact']:
                profile.set_bit(STATUS_BITS['EMAIL_NEW_CONTACT'])
            elif not form.cleaned_data['contact'] and initial['contact']:
                profile.clear_bit(STATUS_BITS['EMAIL_NEW_CONTACT'])

            if form.cleaned_data['announcement'] and not initial['announcement']:
                profile.set_bit(STATUS_BITS['EMAIL_NEW_ANNOUNCEMENT'])
            elif not form.cleaned_data['announcement'] and initial['announcement']:
                profile.clear_bit(STATUS_BITS['EMAIL_NEW_ANNOUNCEMENT'])

            if profile.bits != old_bits:
                profile.save()
            return HttpResponseRedirect(reverse('my_profile'))
    else:
        form = NotificationSettingsForm(initial=initial)
    return render(request, 'brothers/notification_settings.html', {'form': form, 'email': request.user.email}, context_instance=RequestContext(request))



# ============= Private Functions ============= #

def _get_lowest_undergrad_badge():
    return UserProfile.objects.filter(status='U').aggregate(Min('badge'))['badge__min']


def _get_brother_listing(undergrad=True, num_cols=2):
    """Returns a list of lists, each sublist having num_cols elements, of data about undergraduates or alumni."""

    # first, look up brothers with accounts and add them to a dictionary keyed by badge
    map = {}
    for profile in UserProfile.objects.filter(status=('U' if undergrad else 'A')):
        map[int(profile.badge)] = (profile.common_name(), True)

    # next, add brothers without accounts to the dictionary as necessary
    no_profile_list = IBL[_get_lowest_undergrad_badge():] if undergrad else IBL[1:_get_lowest_undergrad_badge()]
    ignore_list = UserProfile.objects.filter(status='A').values_list('badge', flat=True) if undergrad else []
    for badge, name in no_profile_list:
        if badge not in ignore_list and not map.has_key(badge):
            map[badge] = (name, False)

    # sort the dictionary by badge and use the sorted values to generate the final list
    sorted_list = sorted(map.iteritems())
    num_bros = len(sorted_list)
    num_rows = num_bros/num_cols
    if num_bros % num_cols:
        num_rows += 1
    result = []
    for i in range(num_cols):
        for j in range(num_rows):
            if len(result) == j:
                result.append([])
            index = i * num_rows + j
            if index < num_bros:
                data = sorted_list[index]   # data is a tuple in the format (badge, (name, has_account))
                result[j].append((data[0], data[1][0], data[1][1]))
            else:
                result[j].append(tuple())

    return result, num_bros


def get_fields_from_profile(profile, vis=None):
    fields = []
    if (profile.middle_name or profile.nickname) and (vis is None or vis.full_name):
        fields.append('Full name')

    # chapter information
    if profile.big_brother > 0 and (vis is None or vis.big_brother):
        fields.append('Big brother')
    if profile.major and (vis is None or vis.major):
        fields.append('Major')
    if profile.initiation is not None and (vis is None or vis.initiation):
        fields.append('Initiation')
    if profile.graduation is not None and (vis is None or vis.graduation):
        fields.append('Graduation')

    # personal information
    if profile.hometown and (vis is None or vis.hometown):
        fields.append('Hometown')
    if profile.current_city and (vis is None or vis.current_city):
        fields.append('Current city')
    if profile.dob is not None and (vis is None or vis.dob):
        fields.append('Date of birth')

    # contact information
    if profile.phone and (vis is None or vis.phone):
        fields.append('Phone')
    if vis is None or vis.email:
        fields.append('Email') # email is required

    return fields


def get_field_categories(fields):
    field_set = frozenset(fields)
    chapter_set = frozenset(['Big brother', 'Major', 'Initiation', 'Graduation'])
    personal_set = frozenset(['Hometown', 'Current city', 'Date of birth'])
    contact_set = frozenset(['Phone', 'Email'])
    return len(field_set.intersection(chapter_set)), len(field_set.intersection(personal_set)), len(field_set.intersection(contact_set))


def get_available_permissions():
    """Returns a query set containing all available permissions. Excluded permissions are those relating to unused Django admin model objects
       (site, session, message, content type), those which are implicitly granted to all users (visibility settings), and those which are
       implicitly granted to all visitors of the site (contact record, information card)."""
    return Permission.objects.exclude(codename__contains='site').exclude(codename__contains='session').exclude(codename__contains='message') \
            .exclude(codename__contains='contenttype').exclude(codename__contains='visibilitysettings').exclude(codename__contains='contactrecord') \
            .exclude(codename__contains='informationcard').order_by('id')


def process_status_change(user, old_status, new_status):
    """Handles adding a user to or removing a user from the 'Undergraduates' group when his chapter status changes.
       Returns True if a change was made, False otherwise."""
    result = False
    try:
        undergrads = Group.objects.get(name='Undergraduates')
    except Group.DoesNotExist:
        # this should never happen
        log.warn("Failed to find user group 'Undergraduates' while processing status change for user '%s' (badge %d)" % (user.get_full_name(), user.get_profile().badge))
    else:
        if old_status != 'U' and new_status == 'U':
            user.groups.add(undergrads)
            result = True
        elif old_status == 'U':
            user.groups.remove(undergrads)
            result = True
    return result
