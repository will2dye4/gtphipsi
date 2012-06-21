from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, AnonymousUser, Group, Permission
from django.conf import settings
from rush.views import REFERRER
from brothers.models import UserProfile, UserForm, VisibilitySettings, STATUS_BITS
import logging

log = logging.getLogger('django.request')

def home(request):
    log.info('Page viewed: Home')
    template = 'index.html' if request.user.is_anonymous() else 'index_bros_only.html'
    return render(request, template, context_instance=RequestContext(request))


def sign_in(request):
    error = ''
    locked_out_bit = STATUS_BITS['LOCKED_OUT']
    username = request.POST.get('username', '')
    
    try:
        test = request.session['login_attempts']
        del test
    except KeyError:
        request.session['login_attempts'] = 1
    
    if request.method == 'POST':
        try:
            user = User.objects.get(username=username)
            profile = user.get_profile()
            if profile.has_bit(locked_out_bit):
                error = 'locked'
        except User.DoesNotExist:
            error = 'invalid'
            request.session['login_attempts'] += 1
        except UserProfile.DoesNotExist:
            pass
        if request.session['login_attempts'] <= settings.MAX_LOGIN_ATTEMPTS and not error:
            user = authenticate(username=username, password=request.POST['password'])
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return HttpResponseRedirect(get_redirect_destination(request.META['HTTP_REFERER']))
                else:
                    error = 'disabled'
            else:
                error = 'invalid'
                request.session['login_attempts'] += 1
        elif not error:
            error = 'locked'
            try:
                profile = user.get_profile()
                profile.bits |= locked_out_bit
                profile.save()
                request.session['login_attempts'] = 1
            except UserProfile.DoesNotExist:
                pass
    return render(request, 'login.html', {'username': username, 'error': error}, context_instance=RequestContext(request))


def sign_out(request):
    logout(request)
    request.session['login_attempts'] = 1
    return HttpResponseRedirect(reverse('home'))


def register(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            first, last, username, password, email = form.cleaned_data['first_name'], form.cleaned_data['last_name'], form.cleaned_data['username'], form.cleaned_data['password'], form.cleaned_data['email']
            user = User.objects.create_user(username, email, password)
            user.first_name = first
            user.last_name = last
            create_user_permissions(user, form.cleaned_data['status'] == 'U', form.cleaned_data['make_admin'])
            user.save()
            middle, suffix, nickname = form.cleaned_data['middle_name'], form.cleaned_data['suffix'], form.cleaned_data['nickname']
            badge, status, big = form.cleaned_data['badge'], form.cleaned_data['status'], form.cleaned_data['big_brother']
            major, hometown, current_city, phone = form.cleaned_data['major'], form.cleaned_data['hometown'], form.cleaned_data['current_city'], form.cleaned_data['phone']
            initiation, graduation, dob = form.cleaned_data['initiation'], form.cleaned_data['graduation'], form.cleaned_data['dob']
            public, chapter = create_visibility_settings()
            profile = UserProfile(user=user, middle_name=middle, suffix=suffix, nickname=nickname, badge=badge, status=status, big_brother=big, major=major, hometown=hometown, current_city=current_city, phone=phone, initiation=initiation, graduation=graduation, dob=dob, public_visibility=public, chapter_visibility=chapter)
            profile.save()
            return HttpResponseRedirect(reverse('register_success'))
    else:
        form = UserForm()
    return render(request, 'brothers/register.html', {'form': form}, context_instance=RequestContext(request))


def register_success(request):
    return render(request, 'brothers/register_success.html', context_instance=RequestContext(request))


def calendar(request):
    return render(request, 'calendar.html', context_instance=RequestContext(request))


def contact(request):
    from chapter.models import ContactForm
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            request.META[REFERRER] = reverse('contact')
            return HttpResponseRedirect(reverse('contact_thanks'))
    else:
        form = ContactForm(initial={'message': ''})
    return render(request, 'contact.html', {'form': form}, context_instance=RequestContext(request))


def contact_thanks(request):
    from django.http import Http404
    if not (REFERRER in request.META and request.META[REFERRER].endswith(reverse('contact'))):
        raise Http404
    else:
        return render(request, 'contactthanks.html', context_instance=RequestContext(request))


def forbidden(request):
    return render(request, 'forbidden.html', context_instance=RequestContext(request))


def get_redirect_destination(referrer):
    """Helper function to find and return the 'next' parameter from the HTTP Referrer header, if present."""
    if referrer.find('?') > -1:
        uri, delim, querystr = referrer.partition('?')
        args = querystr.split('&')
        for arg in args:
            key_val = arg.split('=')
            if key_val[0] == 'next':
                return key_val[1]
    return reverse('home')


def create_user_permissions(user, undergrad, admin):
    """Helper function to add a new user to the appropriate permissions group(s)."""
    if undergrad or admin:
        group, created = Group.objects.get_or_create(name='Undergraduates')
        if created:
            create_permissions()
            group.permissions = [Permission.objects.get(codename=code) for code in settings.UNDERGRADUATE_PERMISSIONS]
            group.save()
        user.groups.add(group)
    if admin:
        group, created = Group.objects.get_or_create(name='Administrators')
        if created:
            group.permissions = [Permission.objects.get(codename=code) for code in settings.ADMINISTRATOR_PERMISSIONS]
            group.save()
        user.groups.add(group)


def create_permissions():
    """Helper function to create the necessary Permission objects the first time a user is created."""
    if not Permission.objects.all().count():
        permissions = settings.UNDERGRADUATE_PERMISSIONS + settings.ADMINISTRATOR_PERMISSIONS
        Permission.objects.bulk_create([Permission(codename=code) for code in permissions])


def create_visibility_settings():
    public_visibility = VisibilitySettings(full_name=False, big_brother=False, major=False, hometown=False, current_city=False, initiation=False, graduation=False, dob=False, phone=False, email=False)
    public_visibility.save()
    chapter_visibility = VisibilitySettings(full_name=True, big_brother=True, major=True, hometown=True, current_city=True, initiation=True, graduation=True, dob=True, phone=True, email=True)
    chapter_visibility.save()
    return public_visibility, chapter_visibility