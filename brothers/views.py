from django.shortcuts import render
from django.template import RequestContext
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Permission, Group
from django.http import Http404, HttpResponseRedirect
from brothers.models import UserProfile, UserForm, VisibilitySettings, PublicVisibilityForm, ChapterVisibilityForm, STATUS_BITS

def list(request):
    profile_list = UserProfile.objects.filter(status='U')
    brothers_list = User.objects.filter(pk__in=[profile.user.id for profile in profile_list])
    paginator = Paginator(brothers_list, 20)
    page = request.GET.get('page') if request.GET.get('page') else 1
    try:
        brothers = paginator.page(page)
    except PageNotAnInteger:
        brothers = paginator.page(1)
    except EmptyPage:
        brothers = paginator.page(paginator.num_pages)
    return render(request, 'brothers/list.html', {'brothers': brothers, 'num_brothers': brothers_list.count()}, context_instance=RequestContext(request))


@login_required
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
            admin = form.cleaned_data['make_admin']
            if admin or form.cleaned_data['status'] == 'U':
                group, created = Group.objects.get_or_create(name='Undergraduates')
                if created:
                    group.permissions = [Permission.objects.get(codename=code) for code in settings.UNDERGRADUATE_PERMISSIONS]
                    group.save()
                user.groups.add(group)
            if admin:
                group, created = Group.objects.get_or_create(name='Administrators')
                if created:
                    group.permissions = [Permission.objects.get(codename=code) for code in settings.ADMINISTRATOR_PERMISSIONS]
                    group.save()
                user.groups.add(group)
            user.save()
            middle, suffix, nickname = form.cleaned_data['middle_name'], form.cleaned_data['suffix'], form.cleaned_data['nickname']
            badge, status, big = form.cleaned_data['badge'], form.cleaned_data['status'], form.cleaned_data['big_brother']
            major, hometown, current_city, phone = form.cleaned_data['major'], form.cleaned_data['hometown'], form.cleaned_data['current_city'], form.cleaned_data['phone']
            initiation, graduation, dob = form.cleaned_data['initiation'], form.cleaned_data['graduation'], form.cleaned_data['dob']
            public_visibility = VisibilitySettings(full_name=False, big_brother=False, major=False, hometown=False, current_city=False, initiation=False, graduation=False, dob=False, phone=False, email=False)
            public_visibility.save()
            chapter_visibility = VisibilitySettings(full_name=True, big_brother=True, major=True, hometown=True, current_city=True, initiation=True, graduation=True, dob=True, phone=True, email=True)
            chapter_visibility.save()
            profile = UserProfile(user=user, middle_name=middle, suffix=suffix, nickname=nickname, badge=badge, status=status, big_brother=big, major=major, hometown=hometown, current_city=current_city, phone=phone, initiation=initiation, graduation=graduation, dob=dob, public_visibility=public_visibility, chapter_visibility=chapter_visibility)
            profile.save()
            return HttpResponseRedirect(reverse('manage_users'))
    else:
        form = UserForm()
    return render(request, 'brothers/add.html', {'form': form, 'secret_key': settings.SECRET_KEY, 'admin_password': settings.ADMIN_KEY}, context_instance=RequestContext(request))


@login_required
@user_passes_test(lambda u: u.get_profile().is_admin() if u else False, login_url='/forbidden/')
def edit(request, id=0):
    user = User.objects.get(pk=id)
    if user is None: # TODO need to catch User.DoesNotExist here instead of check for None?
        raise Http404
    else:
        if 'unlock' in request.GET and request.GET['unlock'] == 'true' and user.get_profile().has_bit(STATUS_BITS['LOCKED_OUT']):
            profile = user.get_profile()
            profile.bits &= ~STATUS_BITS['LOCKED_OUT']
            profile.save()
            return HttpResponseRedirect(reverse('manage_users'))
        else:
            pass # ... future functionality
    return render(request, 'brothers/edit.html', context_instance=RequestContext(request))


@login_required
@user_passes_test(lambda u: u.get_profile().is_admin() if u else False, login_url='/forbidden/')
def manage_groups(request):
    # TODO
    pass


@login_required
def visibility(request):
    fields = []
    profile = request.user.get_profile()
    public = profile.public_visibility
    chapter = profile.chapter_visibility
    if profile.middle_name or profile.nickname:
        fields.append('full_name')
    if profile.big_brother is not None:
        fields.append('big_brother')
    if profile.major:
        fields.append('major')
    if profile.hometown:
        fields.append('hometown')
    if profile.current_city:
        fields.append('current_city')
    if profile.initiation is not None:
        fields.append('initiation')
    if profile.graduation is not None:
        fields.append('graduation')
    if profile.dob is not None:
        fields.append('dob')
    if profile.phone:
        fields.append('phone')
    if request.user.email:
        fields.append('email')
    return render(request, 'brothers/visibility.html', {'fields': fields, 'public': public, 'chapter': chapter}, context_instance=RequestContext(request))


@login_required
def edit_visibility(request, public=True):
    visibility = request.user.get_profile().public_visibility if public else request.user.get_profile().chapter_visibility
    vis_type = 'public' if public else 'chapter'
    message = 'Remember that your public profile is visible to anyone.' if public else 'Your chapter profile is visible only to brothers with accounts.'
    if request.method == 'POST':
        form = PublicVisibilityForm(request.POST, instance=visibility) if public else ChapterVisibilityForm(request.POST, instance=visibility)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('visibility'))
    else:
        form = PublicVisibilityForm(instance=visibility) if public else ChapterVisibilityForm(instance=visibility)
    return render(request, 'brothers/edit_visibility.html', {'form': form, 'type': vis_type, 'message': message}, context_instance=RequestContext(request))


@login_required
def edit_public_visibility(request):
    return edit_visibility(request)


@login_required
def edit_chapter_visibility(request):
    return edit_visibility(request, False)