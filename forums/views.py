from datetime import datetime

from django.db import IntegrityError
from django.shortcuts import render
from django.template import RequestContext
from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.contrib.auth.decorators import login_required, permission_required
from django.http import Http404, HttpResponseRedirect
from django.template.defaultfilters import slugify

from gtphipsi.brothers.models import UserProfile
from gtphipsi.forums.models import Forum, Thread, Post
from gtphipsi.forums.forms import ForumForm, ThreadForm, PostForm


@login_required
def forums(request):
    list = Forum.objects.all()
    forums = []
    for forum in list:
        if Post.objects.filter(thread__forum=forum).count():
            last_post = Post.objects.filter(thread__forum=forum).order_by('-updated')[0]
        else:
            last_post = None
        forums.append((forum, last_post))
    can_add = request.user.has_perm('forums.add_forum')
    return render(request, 'forums/forums.html', {'forums': forums, 'can_add': can_add}, context_instance=RequestContext(request))


@login_required
def view_forum(request, slug):
    try:
        forum = Forum.objects.get(slug=slug)
    except Forum.DoesNotExist:
        raise Http404
    is_mod = (request.user.get_profile() in forum.moderators.all())
    objects = Thread.objects.filter(forum=forum).order_by('-updated')
    paginator = Paginator(objects, settings.POSTS_PER_PAGE)
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1
    try:
        threads = paginator.page(page)
    except (EmptyPage, InvalidPage):
        threads = paginator.page(paginator.num_pages)
    return render(request, 'forums/view_forum.html', {'threads': threads, 'forum': forum, 'is_mod': is_mod}, context_instance=RequestContext(request))


@login_required
@permission_required('forums.add_forum', login_url=settings.FORBIDDEN_URL)
def add_forum(request):
    if request.method == 'POST':
        form = ForumForm(request.POST)
        if form.is_valid():
            forum = form.save(commit=False)
            forum.slug = slugify(forum.name)
            try:
                forum.save()
            except IntegrityError:
                form._errors['name'] = form.error_class(['That name is too similar to an existing forum name.'])
            else:
                for mod in form.cleaned_data.get('moderators'):
                    forum.moderators.add(mod)
                forum.save()
                return HttpResponseRedirect(reverse('forums'))
    else:
        form = ForumForm()
    return render(request, 'forums/add_forum.html', {'form': form, 'create': True}, context_instance=RequestContext(request))


@login_required
def edit_forum(request, slug):
    try:
        forum = Forum.objects.get(slug=slug)
    except Forum.DoesNotExist:
        raise Http404
    profile = request.user.get_profile()
    if profile not in forum.moderators.all() and not profile.is_admin():
        return HttpResponseRedirect(reverse('forbidden'))
    if request.method == 'POST':
        form = ForumForm(request.POST, instance=forum)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('forums'))
    else:
        if 'delete' in request.GET and request.GET.get('delete') == 'true':
            forum.delete()
            return HttpResponseRedirect(reverse('forums'))
        form = ForumForm(instance=forum)
    return render(request, 'forums/add_forum.html', {'form': form, 'forum': forum, 'create': False})


@login_required
def view_thread(request, forum, id, thread, page=1):
    try:
        forum = Forum.objects.get(slug=forum)
        thread = Thread.objects.get(id=id)
    except (Forum.DoesNotExist, Thread.DoesNotExist):
        raise Http404
    
    page = int(page)
    objects = Post.objects.filter(thread=thread).order_by('number')
    paginator = Paginator(objects, settings.POSTS_PER_PAGE)
    try:
        posts = paginator.page(page)
    except (EmptyPage, InvalidPage):
        posts = paginator.page(paginator.num_pages)
    user = request.user.get_profile()
    subscribed = (UserProfile.objects.filter(badge=user.badge, subscriptions=id).count() > 0)
    is_mod = (user in forum.moderators.all())
    if subscribed and 'unsubscribe' in request.GET:
        user.subscriptions.remove(thread)
        user.save()
        return HttpResponseRedirect(reverse('view_thread', kwargs={'forum': forum.slug, 'id': thread.id, 'thread': thread.slug}))
    elif not subscribed and 'subscribe' in request.GET:
        user.subscriptions.add(thread)
        user.save()
        return HttpResponseRedirect(reverse('view_thread', kwargs={'forum': forum.slug, 'id': thread.id, 'thread': thread.slug}))

    return render(request, 'forums/view_thread.html', {'thread': thread, 'posts': posts, 'forum': forum, 'subscribed': subscribed, 'profile': user, 'is_mod': is_mod}, context_instance=RequestContext(request))


@login_required
def subscriptions(request):
    threads = request.user.get_profile().subscriptions.all().order_by('-updated')
    return render(request, 'forums/subscriptions.html', {'subscriptions': threads}, context_instance=RequestContext(request))


@login_required
def add_thread(request, slug):
    try:
        forum = Forum.objects.get(slug=slug)
    except Forum.DoesNotExist:
        raise Http404
    if request.method == 'POST':
        form = ThreadForm(request.POST)
        if form.is_valid():
            profile = request.user.get_profile()
            thread = form.save(commit=False)
            thread.forum = forum
            thread.owner = profile
            thread.slug = slugify(thread.title)
            thread.save()
            body = _bb_code_escape(form.cleaned_data.get('post'))
            post = Post.objects.create(thread=thread, user=profile, updated_by=profile, number=1, deleted=False, body=body)
            post.save()
            return HttpResponseRedirect(thread.get_absolute_url())
    else:
        form = ThreadForm()
    return render(request, 'forums/add_thread.html', {'form': form, 'forum': forum, 'create': True}, context_instance=RequestContext(request))


@login_required
def edit_thread(request, forum, id, thread):
    try:
        forum = Forum.objects.get(slug=forum)
        thread = Thread.objects.get(id=id)
        first_post = Post.objects.get(thread=thread, number=1)
    except (Forum.DoesNotExist, Thread.DoesNotExist, Post.DoesNotExist):
        raise Http404
    profile = request.user.get_profile()
    if thread.owner != profile and profile not in thread.forum.moderators.all() and not profile.is_admin():
        return HttpResponseRedirect(reverse('forbidden'))
    if request.method == 'POST':
        form = ThreadForm(request.POST, instance=thread)
        if form.is_valid():
            form.save()
            first_post.body = _bb_code_escape(form.cleaned_data.get('post'))
            first_post.updated_by = profile
            first_post.save()
            return HttpResponseRedirect(thread.get_absolute_url())
    else:
        if 'delete' in request.GET and request.GET.get('delete') == 'true':
            thread.delete()
            return HttpResponseRedirect(forum.get_absolute_url())
        form = ThreadForm(instance=thread, initial={'post': _bb_code_unescape(first_post.body)})
    return render(request, 'forums/add_thread.html', {'form': form, 'forum': forum, 'thread': thread, 'create': False})


@login_required
def add_post(request, forum, id, thread):
    try:
        forum = Forum.objects.get(slug=forum)
        thread = Thread.objects.get(id=id)
    except (Forum.DoesNotExist, Thread.DoesNotExist):
        raise Http404
    if request.method == 'POST':
        profile = request.user.get_profile()
        quote = None
        if 'quote' in request.POST:
            try:
                quote = Post.objects.get(thread=thread, number=int(request.POST.get('quote')))
            except Post.DoesNotExist:
                pass
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.thread = thread
            post.user = profile
            post.updated_by = profile
            post.deleted = False
            post.number = Post.objects.filter(thread=thread).count() + 1
            if quote is not None:
                post.quote = quote
            post.body = _bb_code_escape(post.body)
            post.save()
            thread.updated = datetime.now()
            thread.save()
            return HttpResponseRedirect(post.get_absolute_url())
    else:
        quote = None
        if 'quote' in request.GET:
            try:
                quote = Post.objects.get(thread=thread, number=int(request.GET.get('quote')))
            except Post.DoesNotExist:
                pass
        form = PostForm()
    return render(request, 'forums/add_post.html', {'form': form, 'forum': forum, 'thread': thread, 'quote': quote, 'create': True}, context_instance=RequestContext(request))


@login_required
def edit_post(request, id):
    try:
        post = Post.objects.get(id=id)
    except Post.DoesNotExist:
        raise Http404
    profile = request.user.get_profile()
    if post.user != profile and profile not in post.thread.forum.moderators.all() and not profile.is_admin():
        return HttpResponseRedirect(reverse('forbidden'))
    if request.method == 'POST':
        post.body = _bb_code_unescape(post.body)
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save()
            post.body = _bb_code_escape(post.body)
            post.updated_by = profile
            post.save()
            return HttpResponseRedirect(post.get_absolute_url())
    else:
        if 'delete' in request.GET and request.GET.get('delete') == 'true':
            post.deleted = True
            post.updated_by = profile
            post.save()
            return HttpResponseRedirect(post.thread.get_absolute_url())
        post.body = _bb_code_unescape(post.body)
        form = PostForm(instance=post)
    return render(request, 'forums/add_post.html', {'form': form, 'forum': post.thread.forum, 'thread': post.thread, 'quote': post.quote, 'create': False, 'post': post}, context_instance=RequestContext(request))






## ============================================= ##
##                                               ##
##               Private Functions               ##
##                                               ##
## ============================================= ##


def _bb_code_escape(text):
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    text = text.replace('[B]', '<b>').replace('[/B]', '</b>').replace('[I]', '<i>').replace('[/I]', '</i>')
    text = text.replace('[U]', '<u>').replace('[/U]', '</u>').replace('\n', '<br />')
    return text.replace('[URL=\"', '<a href=\"').replace('\"]', '\">').replace('[/URL]', '</a>')

def _bb_code_unescape(text):
    text = text.replace('<b>', '[B]').replace('</b>', '[/B]').replace('<i>', '[I]').replace('</i>', '[/I]')
    text = text.replace('<u>', '[U]').replace('</u>', '[/U]').replace('<br />', '\n')
    text = text.replace('<a href=\"', '[URL=\"').replace('\">', '\"]').replace('</a>', '[/URL]')
    return text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
