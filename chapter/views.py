from django.shortcuts import render
from django.template import RequestContext

def about(request):
    return render(request, 'chapter/about.html', context_instance=RequestContext(request))

def history(request):
    return render(request, 'chapter/history.html', context_instance=RequestContext(request))

def creed(request):
    return render(request, 'chapter/creed.html', context_instance=RequestContext(request))
