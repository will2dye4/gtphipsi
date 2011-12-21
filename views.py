from django.shortcuts import render
from django.http import HttpResponse
from django.template import RequestContext
import logging

log = logging.getLogger('django.request')

def home(request):
    log.info('Page viewed: Home')
    return render(request, 'index.html', context_instance=RequestContext(request))

# don't forget to use RequestContext for forms so you can use a CSRF token
def login(request):
    log.debug('Page viewed: Login')
    return render(request, 'login.html', context_instance=RequestContext(request))

def logout(request):
    log.warning('Page viewed: Logout')
    return HttpResponse('<p>This will be the logout page.</p>')

def calendar(request):
    return render(request, 'calendar.html', context_instance=RequestContext(request))