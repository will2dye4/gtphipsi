"""View functions for the gtphipsi.brothers package.

This module exports the following view functions:
    - list (request)
    - show (request, badge)
    - change_email (request)
    - change_email_success (request)
    - my_profile (request)
    - manage (request)
    - add (request)
    - edit (request)
    - unlock (request, badge)
    - edit_account (request[, badge])
    - change_password (request)
    - change_password_success (request)
    - manage_groups (request)
    - add_group (request)
    - edit_group_perms (request, id)
    - edit_group_members (request, id)
    - delete_group (request, id)
    - show_group (request, id)
    - visibility (request)
    - edit_visibility (request[, public])
    - edit_public_visibility (request)
    - edit_chapter_visibility (request)
    - edit_notification_settings (request)

"""

import hashlib
import logging
from re import match

from django.db.models import Min
from django.conf import settings
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Group, Permission, User
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.template import RequestContext

from gtphipsi.brothers.bootstrap import INITIAL_BROTHER_LIST as IBL
from gtphipsi.brothers.forms import ChangePasswordForm, ChapterVisibilityForm, EditAccountForm, EditProfileForm,\
    NotificationSettingsForm, PublicVisibilityForm, UserForm
from gtphipsi.brothers.models import EmailChangeRequest, UserProfile, STATUS_BITS
from gtphipsi.common import create_user_and_profile, get_name_from_badge, log_page_view
from gtphipsi.messages import get_message


log = logging.getLogger('django')


## ============================================= ##
##                                               ##
##                 Public Views                  ##
##                                               ##
## ============================================= ##


def list(request):
    """Render a listing of all members of the chapter, separating undergraduates from alumni."""
    log_page_view(request, 'Brother List')
    columns = 3
    undergrad_rows, num_undergrads = _get_brother_listing(num_cols=columns)
    alumni_rows, num_alumni = _get_brother_listing(False, columns)
    return render(request, 'brothers/list.html',
                  {'undergrad_rows': undergrad_rows, 'num_undergrads': num_undergrads, 'alumni_rows': alumni_rows, 'col_width': 100/columns},
                  context_instance=RequestContext(request))


def show(request, badge):
    """Render a display of information about a specific member of the chapter.

    Required parameters:
        - badge =>  the badge number of the brother to view (as an integer)

    """
    log_page_view(request, 'View Profile')
    try:
        profile = UserProfile.objects.get(badge=badge)
        user = profile.user
    except UserProfile.DoesNotExist:
        name = get_name_from_badge(int(badge))
        if name is None:
            raise Http404
        min = _get_lowest_undergrad_badge()
        status = 'Undergraduate' if int(badge) > min else 'Alumnus'
        context = {'account': None, 'name': name, 'badge': badge, 'status': status}
    else:
        show_public = ('public' in request.GET and request.GET.get('public') == 'true') or request.user.is_anonymous()
        visibility = profile.public_visibility if show_public else profile.chapter_visibility
        fields = _get_fields_from_profile(profile, visibility)
        chapter_fields, personal_fields, contact_fields = _get_field_categories(fields)
        big_bro = None
        if 'Big brother' in fields:
            try:
                big_bro = '%s ... %d' % (UserProfile.objects.get(badge=profile.big_brother).common_name(), int(profile.big_brother))
            except UserProfile.DoesNotExist:    # if user's big brother doesn't have an account, look up name by badge
                big_bro = '%s ... %d' % (get_name_from_badge(profile.big_brother), int(profile.big_brother))
        context = {'own_account': (user == request.user), 'account': user, 'profile': profile, 'public': show_public,
                   'big': big_bro, 'fields': fields, 'chapter_fields': chapter_fields, 'personal_fields': personal_fields,
                   'contact_fields': contact_fields}
    return render(request, 'brothers/show.html', context, context_instance=RequestContext(request))


def change_email(request):
    """Process a request from a user to change his email address, verifying the validity of the new email address."""
    log_page_view(request, 'Change Email')
    if 'hash' in request.GET:
        req = get_object_or_404(EmailChangeRequest, hash=request.GET.get('hash'))
        user = req.user
        log.info('Email address for %s (%s) changed from %s to %s', user.username, user.get_full_name(), user.email, req.email)
        user.email = req.email
        user.save()
        req.delete()    # to keep the email change request table as small as possible, delete requests as they are processed
        return HttpResponseRedirect(reverse('change_email_success'))
    return HttpResponseRedirect(reverse('home'))    # if 'hash' parameter not in query string, redirect to home page


def change_email_success(request):
    """Render a 'success' page after a user's email address has been updated successfully."""
    return render(request, 'brothers/change_email_success.html', context_instance=RequestContext(request))




## ============================================= ##
##                                               ##
##              Authenticated Views              ##
##                                               ##
## ============================================= ##


@login_required
def my_profile(request):
    """Return a display of information about the currently authenticated user."""
    log_page_view(request, 'My Profile')
    return show(request, request.user.get_profile().badge)


@login_required
def manage(request):
    """Return a listing of user accounts along with some administrative data (which users are locked out)."""
    log_page_view(request, 'Manage Users')
    undergrads = UserProfile.objects.filter(status='U')
    alumni = UserProfile.objects.filter(status='A')
    if 'sort' in request.GET:
        sort = _get_sort_field(request.GET.get('sort'), request.GET.get('order', 'asc'))
        undergrads = undergrads.order_by(sort)
        alumni = alumni.order_by(sort)
    locked_out_undergrads = [profile for profile in undergrads if profile.has_bit(STATUS_BITS['LOCKED_OUT'])]
    locked_out_alumni = [profile for profile in alumni if profile.has_bit(STATUS_BITS['LOCKED_OUT'])]
    directory = (request.GET.get('view', 'admin') == 'directory')
    context = {'undergrads': undergrads, 'alumni': alumni, 'locked_out_undergrads': locked_out_undergrads,
               'locked_out_alumni': locked_out_alumni, 'directory': directory}
    return render(request, 'brothers/manage.html', context, context_instance=RequestContext(request))


@login_required
@permission_required('brothers.add_userprofile', login_url=settings.FORBIDDEN_URL)
def add(request):
    """Render and process a form for administrators to create new user accounts."""
    log_page_view(request, 'Add User')
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            create_user_and_profile(form.cleaned_data)
            log.info('Admin %s (#%d) created new user %s (badge = %d)', request.user.get_full_name(),
                    request.user.get_profile().badge, form.cleaned_data['username'], form.cleaned_data['badge'])
            return HttpResponseRedirect(reverse('manage_users'))
    else:
        form = UserForm()
    return render(request, 'brothers/add.html',
                  {'form': form, 'secret_key': settings.BROTHER_KEY, 'admin_password': settings.ADMIN_KEY},
                  context_instance=RequestContext(request))


@login_required
def edit(request):
    """Render a form for the currently authenticated user to modify his user profile."""
    log_page_view(request, 'Edit Profile')
    profile = get_object_or_404(UserProfile, user=request.user)
    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('my_profile'))
    else:
        form = EditProfileForm(instance=profile)
    return render(request, 'brothers/edit.html', {'form': form}, context_instance=RequestContext(request))


@login_required
@permission_required('brothers.change_userprofile', login_url=settings.FORBIDDEN_URL)
def unlock(request, badge):
    """Unlock the user account with the specified badge number.

    Required parameters:
        - badge =>  the badge number of the user to unlock (as an integer)

    """
    log_page_view(request, 'Unlock Account')
    profile = get_object_or_404(UserProfile, badge=badge)
    if profile.has_bit(STATUS_BITS['LOCKED_OUT']):
        profile.clear_bit(STATUS_BITS['LOCKED_OUT'])
        profile.save()
        log.info('User %s (%s) is now unlocked', profile.user.username, profile.user.get_full_name())
    return HttpResponseRedirect(reverse('manage_users'))


@login_required
def edit_account(request, badge=0):
    """Render and process a form to modify a user's account.

    Optional parameters:
        - badge =>  the badge number of the user to edit (as an integer): defaults to the currently authenticated user

    """

    log_page_view(request, 'Edit Account')

    if badge:
        profile = get_object_or_404(UserProfile, badge=badge)
        user = profile.user
    else:
        user = request.user
        profile = user.get_profile()

    own_account = (user == request.user)
    if not (own_account or request.user.get_profile().is_admin()):
        return HttpResponseRedirect(reverse('forbidden'))

    if request.method == 'POST':
        form = EditAccountForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data    # access cleaned form data (normalized to Python objects) through 'data'
            save_user = False           # we only want to save the user instance if one or more of its fields change
            if data['first_name'] != user.first_name or data['last_name'] != user.last_name:
                user.first_name = data['first_name']
                user.last_name = data['last_name']
                save_user = True
            profile.middle_name = data['middle_name']
            profile.nickname = data['nickname']
            profile.suffix = data['suffix']
            if data['status'] != profile.status:    # process change in chapter status (undergraduate/alumnus)
                old_status = profile.status
                profile.status = data['status']
                save_user = _process_status_change(user, old_status, data['status']) or save_user
            if data['email'] != user.email:         # process change in email address (verify new address)
                digest = hashlib.sha224('%d-%s' % (profile.badge, data['email'])).hexdigest()
                req = EmailChangeRequest(user=user, email=data['email'], hash=digest)
                req.save()
                send_mail(get_message('email.change.subject'),
                          get_message('email.change.body', args=(user.first_name, settings.URI_PREFIX, digest)),
                          settings.EMAIL_HOST_USER, [data['email']])
            profile.save()
            if save_user:
                user.save()
            if own_account:
                redirect = reverse('my_profile')
            else:
                log.info('Admin %s (badge %d) edited account details of %s (%s %s)', request.user.get_full_name(),
                         request.user.get_profile().badge, user.username, data['first_name'], data['last_name'])
                redirect = profile.get_absolute_url()
            return HttpResponseRedirect(redirect)

    else:
        form = EditAccountForm(initial={'first_name': user.first_name, 'middle_name': profile.middle_name,
                                        'last_name': user.last_name, 'nickname': profile.nickname,
                                        'suffix': profile.suffix, 'email': user.email, 'status': profile.status})

    badge = profile.badge if (badge and not own_account) else None  # pass badge if admin editing someone else's account
    return render(request, 'brothers/edit_account.html',
                  {'form': form, 'name': user.get_full_name(), 'own_account': own_account, 'badge': badge, 'alum': (profile.status == 'A')},
                  context_instance=RequestContext(request))


@login_required
def change_password(request):
    """Render and process a form for the currently authenticated user to change his password."""

    log_page_view(request, 'Change Password')
    user = request.user
    profile = user.get_profile()
    reset = profile.has_bit(STATUS_BITS['PASSWORD_RESET'])

    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        form.user = user
        if form.is_valid():
            user.set_password(form.cleaned_data['password'])
            user.save()
            if reset:
                profile.clear_bit(STATUS_BITS['PASSWORD_RESET'])
                profile.save()
            else:
                send_mail(get_message('email.new_password.subject'),
                          get_message('email.new_password.body', args=(user.first_name,)),
                          settings.EMAIL_HOST_USER, [user.email])
            log.info('User %s (%s) changed his password', user.username, user.get_full_name())
            return HttpResponseRedirect(reverse('change_password_success'))
    else:
        form = ChangePasswordForm()
        form.user = user

    return render(request, 'brothers/change_password.html',
                  {'form': form, 'message': (get_message('profile.password.reset') if reset else None)},
                  context_instance=RequestContext(request))


@login_required
def change_password_success(request):
    """Render a 'success' page after a user's password has been updated successfully."""
    return render(request, 'brothers/change_password_success.html', context_instance=RequestContext(request))


@login_required
@permission_required('auth.change_group', login_url=settings.FORBIDDEN_URL)
def manage_groups(request):
    """Render a listing of user groups and the brothers or permissions belonging to each group."""
    log_page_view(request, 'Manage User Groups')
    groups = Group.objects.all()
    if request.GET.get('view', '') == 'members':
        group_list = []
        for group in groups:
            profiles = UserProfile.objects.filter(user__id__in=group.user_set.values_list('id', flat=True)).order_by('badge')
            names = ['%s ... %d' % (profile.common_name(), profile.badge) for profile in profiles]
            group_list.append((group.id, group.name, names))
        context = {'group_list': group_list, 'show_perms': False}
    else:
        context = {'groups': groups, 'show_perms': True}
    return render(request, 'brothers/manage_groups.html', context, context_instance=RequestContext(request))


@login_required
@permission_required('auth.add_group', login_url=settings.FORBIDDEN_URL)
def add_group(request):
    """Render and process a form to create a new user group."""
    log_page_view(request, 'Add User Group')
    error = None
    initial_name = ''   # empty string, not None (otherwise 'None' will appear in the form input)
    if request.method == 'POST':
        ids = []
        group_name = None
        for name, value in request.POST.items():
            if name.find('perm_') > -1:
                ids.append(int(value))
            elif name == 'group_name':      # validate group names for format and uniqueness
                initial_name = value
                if match(r'^[a-zA-Z0-9_]+[a-zA-Z0-9_ ]*[a-zA-Z0-9]+$', value) is None:
                    error = get_message('group.name.invalid')
                elif Group.objects.filter(name=value).count() > 0:
                    error = get_message('group.name.exists')
                else:
                    group_name = value
        if error is None:
            if group_name is None:
                error = get_message('group.name.nonempty')
            elif not len(ids):
                error = get_message('group.perms.nonempty')
            else:
                group = Group.objects.create(name=group_name)
                group.permissions = Permission.objects.filter(id__in=ids)
                group.save()
                log.info('%s (%s) created user group \'%s\'', request.user.username, request.user.get_full_name(), group_name)
                return HttpResponseRedirect(reverse('view_group', kwargs={'name': group.name}))
    perms = _get_available_permissions()
    choices = [[perm.id, perm.name] for perm in perms]
    return render(request, 'brothers/add_group.html', {'error': error, 'name': initial_name, 'perms': choices},
                  context_instance=RequestContext(request))



@login_required
@permission_required('auth.change_group', login_url=settings.FORBIDDEN_URL)
def edit_group_perms(request, id):
    """Render and process a form to modify the permissions associated with a user group.

    Required parameters:
        - id  =>  the unique ID of the group to edit (as an integer)

    """
    log_page_view(request, 'Edit Group Permissions')
    group = get_object_or_404(Group, id=id)
    if request.method == 'POST':
        ids = []
        for name, value in request.POST.items():
            if name.find('perm_') > -1:
                ids.append(int(value))
        group.permissions = Permission.objects.filter(id__in=ids)
        group.save()
        del request.session['group_perms']  # clear existing group permissions in case they just changed
        log.info('%s (%s) edited permissions for group \'%s\'', request.user.username, request.user.get_full_name(), group.name)
        return HttpResponseRedirect(reverse('view_group', kwargs={'id': group.id}))
    else:
        perms = _get_available_permissions()
        group_perms = group.permissions.all()
        choices = []
        initial = []
        for perm in perms:
            choices.append([perm.id, perm.name])
            if perm in group_perms:
                initial.append(perm.id)
    return render(request, 'brothers/edit_group_perms.html',
                  {'group': group, 'perms': choices, 'initial': initial},
                  context_instance=RequestContext(request))


@login_required
@permission_required('auth.change_group', login_url=settings.FORBIDDEN_URL)
def edit_group_members(request, id):
    """Render and process a form to modify the members of a user group.

    Required parameters:
        - id  =>  the unique ID of the group to edit (as an integer)

    """
    log_page_view(request, 'Edit Group Members')
    group = get_object_or_404(Group, id=id)
    if request.method == 'POST':
        user_ids = []
        for name, value in request.POST.items():
            if name.find('user_') > -1:
                user_ids.append(int(value))
        group.user_set = User.objects.filter(id__in=user_ids)
        group.save()
        del request.session['group_perms']  # clear existing group permissions in case they just changed
        log.info('%s (%s) edited members of group \'%s\'', request.user.username, request.user.get_full_name(), group.name)
        return HttpResponseRedirect(reverse('view_group', kwargs={'id': group.id}))
    else:
        users = User.objects.exclude(is_superuser=True) # only one superuser (root) should exist, so exclude that user
        group_members = group.user_set.all()
        choices = []
        initial = []
        for user in users:
            choices.append([user.id, '%s ... %d' % (user.get_full_name(), user.get_profile().badge)])
            if user in group_members:
                initial.append(user.id)
    return render(request, 'brothers/edit_group_members.html',
                  {'group': group, 'choices': choices, 'initial': initial},
                  context_instance=RequestContext(request))


@login_required
@permission_required('auth.delete_group', login_url=settings.FORBIDDEN_URL)
def delete_group(request, id):
    """Delete a user group, first removing the group from each of its users' set of groups.

    Required parameters:
        - id  =>  the unique ID of the group to delete (as an integer)

    """
    log_page_view(request, 'Delete User Group')
    group = get_object_or_404(Group, id=id)
    group.user_set = User.objects.none()
    group.save()
    log.info('%s (%s) deleted user group \'%s\'', request.user.username, request.user.get_full_name(), group.name)
    group.delete()
    return HttpResponseRedirect(reverse('manage_groups'))


@login_required
@permission_required('auth.change_group', login_url=settings.FORBIDDEN_URL)
def show_group(request, id):
    """Render a display of users and permissions associated with a user group.

    Required parameters:
        - id  =>  the unique ID of the group to display (as an integer)

    """
    log_page_view(request, 'View User Group')
    group = get_object_or_404(Group, id=id)
    profiles = UserProfile.objects.filter(user__id__in=group.user_set.values_list('id', flat=True)).order_by('badge')
    names = ['%s ... %d' % (profile.common_name(), profile.badge) for profile in profiles]
    return render(request, 'brothers/show_group.html', {'group': group, 'users': names},
                  context_instance=RequestContext(request))


@login_required
def visibility(request):
    """Render a display of the currently authenticated user's visibility settings, both public and private."""
    log_page_view(request, 'Visibility Settings')
    profile = request.user.get_profile()
    public = profile.public_visibility
    chapter = profile.chapter_visibility
    fields = _get_fields_from_profile(profile)
    return render(request, 'brothers/visibility.html', {'fields': fields, 'public': public, 'chapter': chapter},
                  context_instance=RequestContext(request))


@login_required
def edit_visibility(request, public=True):
    """Render and process a form for the currently authenticated user to modify his visibility settings.

    Optional parameters:
        - public => whether to edit the user's public or chapter visibility settings (as a boolean): defaults to public

    """
    viz = request.user.get_profile().public_visibility if public else request.user.get_profile().chapter_visibility
    if request.method == 'POST':
        if public:
            form = PublicVisibilityForm(request.POST, instance=viz)
        else:
            form = ChapterVisibilityForm(request.POST, instance=viz)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('visibility'))
    else:
        if public:
            form = PublicVisibilityForm(instance=viz)
        else:
            form = ChapterVisibilityForm(instance=viz)
    fields = _get_fields_from_profile(request.user.get_profile())
    vis_type = 'public' if public else 'chapter'
    message = get_message('visibility.edit.public') if public else get_message('visibility.edit.chapter')
    full_name_msg = get_message('visibility.fullname')
    return render(request, 'brothers/edit_visibility.html',
                  {'form': form, 'fields': fields, 'type': vis_type, 'message': message, 'name_msg': full_name_msg},
                  context_instance=RequestContext(request))


@login_required
def edit_public_visibility(request):
    """Render a form for the currently authenticated user to modify his public visibility settings."""
    log_page_view(request, 'Edit Public Visibility')
    return edit_visibility(request)


@login_required
def edit_chapter_visibility(request):
    """Render a form for the currently authenticated user to modify his chapter visibility settings."""
    log_page_view(request, 'Edit Chapter Visibility')
    return edit_visibility(request, False)


@login_required
def edit_notification_settings(request):
    """Render and process a form for the currently authenticated user to modify his notification settings."""

    log_page_view(request, 'Edit Notification Settings')
    profile = request.user.get_profile()
    initial = {'infocard': profile.has_bit(STATUS_BITS['EMAIL_NEW_INFOCARD']),
               'contact': profile.has_bit(STATUS_BITS['EMAIL_NEW_CONTACT']),
               'announcement': profile.has_bit(STATUS_BITS['EMAIL_NEW_ANNOUNCEMENT'])}

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

    return render(request, 'brothers/notification_settings.html',
                  {'form': form, 'email': request.user.email, 'from_email': settings.EMAIL_HOST_USER},
                  context_instance=RequestContext(request))






## ============================================= ##
##                                               ##
##               Private Functions               ##
##                                               ##
## ============================================= ##


def _get_lowest_undergrad_badge():
    """Return the lowest badge number of all undergraduates with user accounts."""
    return UserProfile.objects.filter(status='U').aggregate(Min('badge'))['badge__min']


def _get_brother_listing(undergrad=True, num_cols=2):
    """Return a list of lists (each sub-list containing the specified number of elements) of data about users.

    Optional parameters:
        - undergrad =>  whether to return a listing of undergraduates or alumni (as a boolean): defaults to undergrads
        - num_cols  =>  the number of elements to put in each inner list

    The function returns a list of lists in the following format (in this case, num_cols = 2):
        [ [ (badge, 'First Last', has_account), (badge, 'First Last', has_account) ], [ (...), (...) ], ... ]

    In addition, the function returns the total number of users in all the inner lists.

    """

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
                result[j].append(tuple())   # append empty tuples at the end if needed

    return result, num_bros


def _get_fields_from_profile(profile, vis=None):
    """Return a list of field names (as strings) that a user has provided and, optionally, made visible.

    Required parameters:
        - profile   =>  the profile whose fields to inspect

    Optional parameters:
        - vis   =>  the visibility settings to use for restricting which fields are returned: defaults to None

    If 'vis' is None, the function returns all nonempty fields in the user's profile. Otherwise, the function returns
    all nonempty fields in the profile that are marked as visible by the provided visibility settings.

    """

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


def _get_field_categories(fields):
    """Return the number of nonempty fields for each of three categories (chapter, personal, and contact info)."""
    field_set = frozenset(fields)
    chapter_set = frozenset(['Big brother', 'Major', 'Initiation', 'Graduation'])
    personal_set = frozenset(['Hometown', 'Current city', 'Date of birth'])
    contact_set = frozenset(['Phone', 'Email'])
    return len(field_set.intersection(chapter_set)),\
           len(field_set.intersection(personal_set)),\
           len(field_set.intersection(contact_set))


def _get_available_permissions():
    """Return a QuerySet containing all available permissions.

    Excluded permissions are those relating to unused Django admin model objects (site, session, message, content type),
    those which are implicitly granted to all users (visibility settings), and those which are implicitly granted to all
    visitors of the site (contact record, information card).

    """
    return Permission.objects.exclude(codename__contains='site').exclude(codename__contains='session') \
            .exclude(codename__contains='message').exclude(codename__contains='contenttype') \
            .exclude(codename__contains='visibilitysettings').exclude(codename__contains='contactrecord') \
            .exclude(codename__contains='informationcard').order_by('id')


def _process_status_change(user, old_status, new_status):
    """Add a user to and remove a user from the appropriate user groups when his chapter status changes.

    Return True if a change was made, False otherwise.

    """
    result = False
    try:
        undergrads = Group.objects.get(name='Undergraduates')
        alumni = Group.objects.get(name='Alumni')
    except Group.DoesNotExist:
        # this should never happen
        log.warn("Failed to find default user group while processing status change for user '%s' (badge %d)",
                 user.get_full_name(), user.get_profile().badge)
    else:
        if old_status == 'A' and new_status != 'A':
            user.groups.remove(alumni)
            user.groups.add(undergrads)
            result = True
        elif old_status != 'A' and new_status == 'A':
            user.groups.remove(undergrads)
            user.groups.add(alumni)
            result = True
    return result


def _get_sort_field(sort, order):
    """Return the name of the field by which to sort, based on the content of the request's query string."""

    if sort not in ['name', 'email', 'phone', 'city', 'login']:
        sort = 'name'
    if sort == 'name':
        sort = 'user__first_name'
    elif sort == 'city':
        sort = 'current_city'
    elif sort == 'email':
        sort = 'user__email'
    elif sort == 'login':
        sort = 'user__last_login'

    if order == 'desc':
        sort = '-%s' % sort
    return sort
