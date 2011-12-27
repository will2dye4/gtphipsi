from django.shortcuts import render
from django.template import RequestContext
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.models import User
from brothers.models import UserProfile

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
