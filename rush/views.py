from django.shortcuts import render
from django.template import RequestContext

def rush(request):
    return render(request, 'rush/rush.html', context_instance=RequestContext(request))

def rushphipsi(request):
    return render(request, 'rush/phipsi.html', context_instance=RequestContext(request))

def schedule(request):
    # TODO use the database for this!
    return render(request, 'rush/schedule.html', context_instance=RequestContext(request))
