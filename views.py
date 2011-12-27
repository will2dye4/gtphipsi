from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.conf import settings
from rush.views import REFERRER
from brothers.models import UserProfile, STATUS_BITS
import logging

log = logging.getLogger('django.request')

def home(request):
    log.info('Page viewed: Home')
    return render(request, 'index.html', context_instance=RequestContext(request))


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
                    return HttpResponseRedirect(reverse('home'))
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