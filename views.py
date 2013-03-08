"""'Global' view functions for the gtphipsi package.

This module exports the following view functions:
    - home (request)
    - sign_in (request)
    - sign_out (request)
    - forbidden (request)
    - register (request)
    - register_success (request)
    - calendar (request)
    - contact (request)
    - contact_thanks (request)
    - forgot_password (request)
    - reset_password (request, id)
    - reset_password_success (request)

"""

from datetime import datetime, timedelta
import logging

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.mail import get_connection
from django.core.mail.message import EmailMessage
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect, QueryDict
from django.shortcuts import get_object_or_404, render
from django.template import RequestContext

from gtphipsi.brothers.forms import UserForm
from gtphipsi.brothers.models import UserProfile, STATUS_BITS
from gtphipsi.chapter.forms import ContactForm
from gtphipsi.chapter.models import Announcement, InformationCard
from gtphipsi.common import create_user_and_profile, REFERRER
from gtphipsi.messages import get_message


log = logging.getLogger('django.request')


## ============================================= ##
##                                               ##
##                 Public Views                  ##
##                                               ##
## ============================================= ##


def home(request):
    """Render a home page - a page of text for visitors and a sort of 'dashboard' view for authenticated members."""
    if request.user.is_anonymous():
        template = 'index.html'
        context = {}    # main index doesn't require any context
    else:
        template = 'index_bros_only.html'
        user = request.user
        profile = user.get_profile()
        threads = profile.subscriptions.order_by('-updated')
        if len(threads) > 5:
            threads = threads[:5]
        announcements = Announcement.most_recent(False)
        two_months_ago = datetime.now() - timedelta(days=60)
        info_cards = InformationCard.objects.filter(created__gte=two_months_ago).order_by('-created')
        if len(info_cards) > 5:
            info_cards = info_cards[:5]
        accounts = UserProfile.objects.filter(user__date_joined__gte=two_months_ago).order_by('badge')
        context = {'subscriptions': threads, 'announcements': announcements, 'info_cards': info_cards, 'accounts': accounts}
    return render(request, template, context, context_instance=RequestContext(request))


def sign_in(request):
    """Render and process a form for users to sign into their accounts."""

    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse('home'))    # you can't sign in once you're signed in ...

    if 'login_attempts' not in request.session:
        request.session['login_attempts'] = 1
    if 'username' not in request.session:
        request.session['username'] = ''

    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '')
        if username != request.session['username']:
            request.session['username'] = username
            request.session['login_attempts'] = 1
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            error = get_message('login.account.invalid')
        else:
            profile = user.get_profile()
            if profile.has_bit(STATUS_BITS['LOCKED_OUT']):
                error = get_message('login.account.locked')
            elif request.session['login_attempts'] > settings.MAX_LOGIN_ATTEMPTS:
                error = get_message('login.account.locked')
                profile.set_bit(STATUS_BITS['LOCKED_OUT'])
                profile.save()
            else:
                user = authenticate(username=username, password=request.POST.get('password'))
                if user is None:
                    error = get_message('login.account.invalid')
                    request.session['login_attempts'] += 1      # invalid password; increment login attempts
                elif not user.is_active:
                    error = get_message('login.account.disabled')
                else:
                    login(request, user)
                    del request.session['login_attempts'], request.session['username'], request.session['group_perms']
                    return HttpResponseRedirect(_get_redirect_destination(request.META[REFERRER], user.get_profile()))
    else:
        username = ''

    return render(request, 'public/login.html', {'username': username, 'error': error},
                  context_instance=RequestContext(request))


def sign_out(request):
    """Sign out the currently authenticated user (if there is one), then redirect to the home page."""
    logout(request)
    if 'group_perms' in request.session:
        del request.session['group_perms']
    return HttpResponseRedirect(reverse('home'))


def forbidden(request):
    """Render a 'forbidden' page when a user tries to go to a page that he is not allowed to view."""
    return render(request, 'forbidden.html', context_instance=RequestContext(request))


def register(request):
    """Render and process a form for members to register with the site."""
    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse('home'))
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            create_user_and_profile(form.cleaned_data)
            return HttpResponseRedirect(reverse('register_success'))
    else:
        form = UserForm()
    return render(request, 'brothers/register.html', {'form': form}, context_instance=RequestContext(request))


def register_success(request):
    """Render a 'success' page after a member has registered successfully."""
    return render(request, 'brothers/register_success.html', context_instance=RequestContext(request))


def calendar(request):
    """Display the chapter's calendar of events (currently displays a Google calendar inline)."""
    return render(request, 'public/calendar.html', context_instance=RequestContext(request))


def contact(request):
    """Render and process a form for visitors to contact the chapter."""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save()
            _send_contact_emails(contact)
            request.META[REFERRER] = reverse('contact') # set the HTTP_REFERER header, expected by the 'thanks' view
            return HttpResponseRedirect(reverse('contact_thanks'))
    else:
        form = ContactForm(initial={'message': ''})
    return render(request, 'public/contact.html', {'form': form}, context_instance=RequestContext(request))


def contact_thanks(request):
    """Render a 'thanks' view after processing a new contact form."""
    if REFERRER not in request.META or not request.META[REFERRER].endswith(reverse('contact')):
        raise Http404
    return render(request, 'public/contact_thanks.html', context_instance=RequestContext(request))


def forgot_password(request):
    """Render and process a form to allow users to reset their passwords."""

    if request.user.is_authenticated() and not request.user.get_profile().is_admin():
        return HttpResponseRedirect(reverse('forbidden'))   # if you're logged in but not admin, you shouldn't be here

    username = None
    if request.method == 'POST':
        username = request.POST.get('username', '')
    elif 'username' in request.session and request.session['username'] != '':
        username = request.session['username']

    if username is None:
        error = None
    else:
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            error = 'That username is invalid.'
        else:
            return reset_password(request, user.id)

    return render(request, 'public/forgot_password.html', {'error': error}, context_instance=RequestContext(request))


def reset_password(request, id):
    """Reset a user's password to a random string and email the user the new password.

    Required parameters:
        - id    =>  the unique ID of the user whose password should be reset (as an integer)

    """

    if request.user.is_authenticated() and not request.user.get_profile().is_admin():
        return HttpResponseRedirect(reverse('forbidden'))   # non-admins should use the 'change password' form

    user = get_object_or_404(User, id=id)
    anonymous = request.user.is_anonymous()

    if request.method == 'POST':
        password = User.objects.make_random_password(length=8, allowed_chars=settings.PASSWORD_RESET_CHARS)
        user.set_password(password)
        user.save()
        profile = user.get_profile()
        profile.set_bit(STATUS_BITS['PASSWORD_RESET'])
        profile.save()

        reset_message = get_message('email.password.reset' if anonymous else 'email.password.admin.reset')
        message = get_message('email.password.body', args=(profile.preferred_name(), reset_message, password))
        user.email_user(get_message('email.password.subject'), message)

        if anonymous:
            log.info('Password reset for user %s. Email sent successfully to %s', user.get_full_name(), user.email)
            redirect = reverse('reset_password_success')
        else:
            log.info('Admin %s (badge %d) reset password for user %s (%s). Email sent successfully to %s',
                     request.user.get_full_name(), request.user.get_profile().badge, user.username,
                     user.get_full_name(), user.email)
            redirect = reverse('manage_users')
        return HttpResponseRedirect(redirect)

    return render(request, 'public/reset_password.html', {'anon': anonymous, 'username': user.username, 'user_id': id},
                  context_instance=RequestContext(request))


def reset_password_success(request):
    """Render a 'success' page after a user's password has been reset successfully."""
    return render(request, 'public/reset_password_success.html', context_instance=RequestContext(request))






## ============================================= ##
##                                               ##
##               Private Functions               ##
##                                               ##
## ============================================= ##


def _get_redirect_destination(referrer, profile):
    """Find and return the 'next' parameter from the HTTP Referrer header, if present.

    Required parameters:
        - referrer  =>  the content of the HTTP Referrer header, as a string
        - profile   =>  the profile of the user who just logged in

    """
    index = referrer.find('?')
    redirect = reverse('home')
    if profile is not None and profile.has_bit(STATUS_BITS['PASSWORD_RESET']):
        redirect = reverse('change_password')
    elif index > -1:
        params = QueryDict(referrer[index+1:])
        if 'next' in params:
            redirect = params['next']
    return redirect


def _send_contact_emails(contact):
    """Send an email to a visitor who submitted a contact form; email brothers who want to be notified.

    Required parameters:
        - contact   =>  the contact record for which to email

    """
    date = contact.created.strftime('%B %d, %Y at %I:%M %p')
    # message to the person who submitted the information card
    message = EmailMessage(get_message('email.contact.subject'),
                           get_message('email.contact.body', args=(contact.name, date, contact.to_string())),
                           to=[contact.email])
    # message to the webmaster and everyone who has selected to be notified about new contact forms
    notification = EmailMessage(get_message('notify.contact.subject'),
                                get_message('notify.contact.body', args=(date, contact.to_string())),
                                to=['webmaster@gtphipsi.org'],
                                bcc=UserProfile.all_emails_with_bit(STATUS_BITS['EMAIL_NEW_CONTACT']))
    # open a connection to the SMTP backend so we can send two messages over the same connection
    conn = get_connection()
    conn.open()
    conn.send_messages([message, notification])
    conn.close()
