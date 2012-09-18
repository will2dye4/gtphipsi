import logging

from django.shortcuts import render
from django.http import HttpResponseRedirect, Http404
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.conf import settings

from gtphipsi.common import create_user_and_profile
from rush.views import REFERRER
from brothers.models import UserProfile, STATUS_BITS
from brothers.forms import UserForm


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
                    try:
                        profile = user.get_profile()
                    except UserProfile.DoesNotExist:
                        profile = None
                    redirect = get_redirect_destination(request.META[REFERRER], profile)
                    return HttpResponseRedirect(redirect)
                else:
                    error = 'disabled'
            else:
                error = 'invalid'
                request.session['login_attempts'] += 1
        elif not error:
            error = 'locked'
            try:
                profile = user.get_profile()
                profile.set_bit(locked_out_bit)
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
            create_user_and_profile(form.cleaned_data)
            return HttpResponseRedirect(reverse('register_success'))
    else:
        form = UserForm()
    return render(request, 'brothers/register.html', {'form': form}, context_instance=RequestContext(request))


def register_success(request):
    return render(request, 'brothers/register_success.html', context_instance=RequestContext(request))


def calendar(request):
    template_name = 'calendar.html' if request.user.is_anonymous() else 'calendar_bros_only.html'
    return render(request, template_name, context_instance=RequestContext(request))


def contact(request):
    from chapter.forms import ContactForm
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


def forgot_password(request):
    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '')
        try:
            user = User.objects.get(username=username)
            return reset_password(request, user.id) #HttpResponseRedirect(reverse('reset_password', args=[user.id]))
        except User.DoesNotExist:
            error = 'That username is invalid.'
    return render(request, 'forgot_password.html', {'error': error}, context_instance=RequestContext(request))


def reset_password(request, id=0):
    try:
        user = User.objects.get(pk=id)
    except User.DoesNotExist:
        raise Http404

    logged_in = request.user.is_authenticated()
    own_account = not logged_in or user == request.user

    if request.method == 'POST':
        password = User.objects.make_random_password(length=8, allowed_chars='abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789%#@&_?')
        user.set_password(password)
        user.save()

        profile = user.get_profile()
        profile.set_bit(STATUS_BITS['PASSWORD_RESET'])
        profile.save()

        message = 'Dear {0},\n\n' \
                    '{1}. The next time you sign in, please use the following temporary password.\n\n' \
                    'Password: {2}\n\n' \
                    'After signing in, you will be prompted to change your password to something more memorable.\n\n' \
                    'Cheers,\n' \
                    'gtphipsi Webmaster'.format(profile.preferred_name(),
                                  ('Your password for gtphipsi.org has been reset successfully' if own_account else 'An administrator has just reset your password for gtphipsi.org'),
                                  password)
        user.email_user('Your password has been reset', message)

        if own_account:
            log.info('User %s reset his password. Email sent successfully to %s', user.get_full_name(), user.email)
            redirect = reverse('reset_password_success')
        else:
            log.info('Admin %s (badge %d) reset password for user %s (%s). Email sent successfully to %s', request.user.get_full_name(), request.user.get_profile().badge, user.username, user.get_full_name(), user.email)
            redirect = reverse('manage_users')
        return HttpResponseRedirect(redirect)

    else:
        return render(request, 'reset_password.html', {'own_account': own_account, 'name': user.first_name, 'user_id': id}, context_instance=RequestContext(request))


def reset_password_success(request):
    return render(request, 'reset_password_success.html', context_instance=RequestContext(request))


def get_redirect_destination(referrer, profile):
    """Helper function to find and return the 'next' parameter from the HTTP Referrer header, if present."""
    redirect = reverse('home')
    if profile is not None and profile.has_bit(STATUS_BITS['PASSWORD_RESET']):
        redirect = reverse('change_password')
    elif referrer.find('?') > -1:
        uri, delim, querystr = referrer.partition('?')
        del uri, delim
        args = querystr.split('&')
        for arg in args:
            key_val = arg.split('=')
            if key_val[0] == 'next':
                redirect = key_val[1]
                break
    return redirect