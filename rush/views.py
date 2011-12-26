from django.shortcuts import render
from django.template import RequestContext
from django.http import HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from chapter.models import InformationForm

REFERRER = 'HTTP_REFERER'

def rush(request):
    return render(request, 'rush/rush.html', context_instance=RequestContext(request))

def rushphipsi(request):
    return render(request, 'rush/phipsi.html', context_instance=RequestContext(request))

def schedule(request):
    # TODO use the database for this!
    return render(request, 'rush/schedule.html', context_instance=RequestContext(request))

def info_card(request):
    if request.method == 'POST':
        form = InformationForm(request.POST)
        if form.is_valid():
            form.save()
            request.META[REFERRER] = reverse('info_card')
            return HttpResponseRedirect(reverse('info_card_thanks'))
    else:
        form = InformationForm()
    return render(request, 'rush/infocard.html', {'form': form}, context_instance=RequestContext(request))

def info_card_thanks(request):
    if not (REFERRER in request.META and request.META[REFERRER].endswith(reverse('info_card'))):
        raise Http404
    else:
        return render(request, 'rush/infocardthanks.html', context_instance=RequestContext(request))
