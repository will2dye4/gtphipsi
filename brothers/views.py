from django.shortcuts import render
from django.template import RequestContext
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Permission, Group
from django.http import Http404, HttpResponseRedirect
from gtphipsi.messages import get_message
from brothers.models import UserProfile, UserForm, EditProfileForm, EditAccountForm, VisibilitySettings, PublicVisibilityForm, ChapterVisibilityForm, ChangePasswordForm, STATUS_BITS
import logging


log = logging.getLogger('django')


# visible to all users
def list(request):
    profile_list = UserProfile.objects.filter(status='U')
    brothers_list = User.objects.filter(pk__in=[profile.user.id for profile in profile_list])   # TODO why not just `[profile.user for profile in profile_list]` ??
    paginator = Paginator(brothers_list, 20)
    page = request.GET.get('page') if request.GET.get('page') else 1
    try:
        brothers = paginator.page(page)
    except PageNotAnInteger:
        brothers = paginator.page(1)
    except EmptyPage:
        brothers = paginator.page(paginator.num_pages)
    return render(request, 'brothers/list.html', {'brothers': brothers, 'num_brothers': brothers_list.count()}, context_instance=RequestContext(request))


# visible to all users
def show(request, badge=0):
    try:
        profile = UserProfile.objects.get(badge=badge)
        user = profile.user
    except (UserProfile.DoesNotExist, User.DoesNotExist):
        raise Http404
    own_account = (user.id == request.user.id)
    show_public = ('public' in request.GET and request.GET['public'] == 'true') or request.user.is_anonymous()
    visibility = profile.public_visibility if show_public else profile.chapter_visibility
    fields = get_fields_from_profile(profile, visibility)
    chapter_fields, personal_fields, contact_fields = get_field_categories(fields)
    return render(request, 'brothers/show.html', {'fields': fields,
                                                  'account': user,
                                                  'profile': profile,
                                                  'public': show_public,
                                                  'own_account': own_account,
                                                  'chapter_fields': chapter_fields,
                                                  'personal_fields': personal_fields,
                                                  'contact_fields': contact_fields
    }, context_instance=RequestContext(request))


@login_required(login_url='/login/')
def my_profile(request):
    return show(request, request.user.get_profile().badge)


@login_required
@user_passes_test(lambda u: u.get_profile().is_admin() if u else False, login_url='/forbidden/')
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
@user_passes_test(lambda u: u.get_profile().is_admin() if u else False, login_url='/forbidden/')
def add(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            first, last, username, password, email = form.cleaned_data['first_name'], form.cleaned_data['last_name'], form.cleaned_data['username'], form.cleaned_data['password'], form.cleaned_data['email']
            user = User.objects.create_user(username, email, password)
            user.first_name = first
            user.last_name = last
            add_user_to_groups(user, (form.cleaned_data['status'] == 'U'), form.cleaned_data['make_admin'])
            user.save()
            middle, suffix, nickname = form.cleaned_data['middle_name'], form.cleaned_data['suffix'], form.cleaned_data['nickname']
            badge, status, big = form.cleaned_data['badge'], form.cleaned_data['status'], form.cleaned_data['big_brother']
            major, hometown, current_city, phone = form.cleaned_data['major'], form.cleaned_data['hometown'], form.cleaned_data['current_city'], form.cleaned_data['phone']
            initiation, graduation, dob = form.cleaned_data['initiation'], form.cleaned_data['graduation'], form.cleaned_data['dob']
            public, chapter = create_visibility_settings()
            profile = UserProfile(user=user, middle_name=middle, suffix=suffix, nickname=nickname, badge=badge, status=status, big_brother=big, major=major, hometown=hometown, current_city=current_city, phone=phone, initiation=initiation, graduation=graduation, dob=dob, public_visibility=public, chapter_visibility=chapter)
            profile.save()
            log.info('Admin %s (badge %d) created new user %s (%s %s)', request.user.get_full_name(), request.user.get_profile().badge, username, first, last)
            return HttpResponseRedirect(reverse('manage_users'))
    else:
        form = UserForm()
    return render(request, 'brothers/add.html', {'form': form, 'secret_key': settings.SECRET_KEY, 'admin_password': settings.ADMIN_KEY}, context_instance=RequestContext(request))


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
@user_passes_test(lambda u: u.get_profile().is_admin() if u else False, login_url='/forbidden/')
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
                # TODO verify name change?
                user.first_name = first
                user.last_name = last
                save_user = True
            profile.middle_name = middle
            profile.nickname = nickname
            profile.suffix = suffix
            if status != profile.status:
                # TODO process status update (permissions)
                profile.status = status
            if email != user.email:
                # TODO process email change
                user.email = email
                save_user = True
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
@user_passes_test(lambda u: u.get_profile().is_admin() if u else False, login_url='/forbidden/')
def manage_groups(request):
    # TODO
    pass


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


# ============= Private Functions ============= #

def add_user_to_groups(user, undergrad, admin):
    if undergrad or admin:
        group, created = Group.objects.get_or_create(name='Undergraduates')
        if created:
            if not Permission.objects.count():
                Permission.objects.bulk_create([Permission(codename=code) for code in (settings.UNDERGRADUATE_PERMISSIONS + settings.ADMINISTRATOR_PERMISSIONS)])
            group.permissions = [Permission.objects.get(codename=code) for code in settings.UNDERGRADUATE_PERMISSIONS]
            group.save()
        user.groups.add(group)
    if admin:
        group, created = Group.objects.get_or_create(name='Administrators')
        if created:
            group.permissions = [Permission.objects.get(codename=code) for code in settings.ADMINISTRATOR_PERMISSIONS]
            group.save()
        user.groups.add(group)


def create_visibility_settings():
    public_visibility = VisibilitySettings(full_name=False, big_brother=False, major=False, hometown=False, current_city=False, initiation=False, graduation=False, dob=False, phone=False, email=False)
    public_visibility.save()
    chapter_visibility = VisibilitySettings(full_name=True, big_brother=True, major=True, hometown=True, current_city=True, initiation=True, graduation=True, dob=True, phone=True, email=True)
    chapter_visibility.save()
    return public_visibility, chapter_visibility


def get_fields_from_profile(profile, vis=None):
    fields = []
    if (profile.middle_name or profile.nickname) and (vis is None or vis.full_name):
        fields.append('Full name')

    # chapter information
    if profile.big_brother is not None and (vis is None or vis.big_brother):
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