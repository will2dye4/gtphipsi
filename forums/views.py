"""View functions for the gtphipsi.forums package.

This module exports the following view functions:
    - forums (request)
    - view_forum (request, slug)
    - add_forum (request)
    - edit_forum (request, slug)
    - view_thread (request, forum, id, thread[, page])
    - subscriptions (request)
    - my_threads (request)
    - add_thread (request, slug)
    - edit_thread (request, forum, id, thread)
    - add_post (request, forum, id, thread)
    - edit_post (request, id)

"""

from datetime import datetime
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import EmptyPage, InvalidPage, Paginator
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.template import RequestContext
from django.template.defaultfilters import slugify

from gtphipsi.common import log_page_view
from gtphipsi.forums.forms import ForumForm, PostForm, ThreadForm
from gtphipsi.forums.models import Forum, Post, Thread


log = logging.getLogger('django')


## ============================================= ##
##                                               ##
##              Authenticated Views              ##
##                                               ##
## ============================================= ##


@login_required
def forums(request):
    """Render a listing of all forums, including the most recent post of all threads within each forum."""
    log_page_view(request, 'Forum List')
    forum_list = Forum.objects.all()
    forums = []
    for forum in forum_list:
        if Post.objects.filter(thread__forum=forum).count():
            last_post = Post.objects.filter(thread__forum=forum).order_by('-updated')[0]
        else:
            last_post = None
        forums.append((forum, last_post))
    return render(request, 'forums/forums.html', {'forums': forums}, context_instance=RequestContext(request))


@login_required
def view_forum(request, slug):
    """Render a listing of threads in a forum, handling pagination if there are many such threads.

    Required arguments:
        - slug  =>  the slug of the forum to view (as a string)

    """
    log_page_view(request, 'View Forum')
    forum = get_object_or_404(Forum, slug=slug)
    is_mod = (request.user.get_profile() in forum.moderators.all())
    objects = Thread.objects.filter(forum=forum).order_by('-updated')
    paginator = Paginator(objects, settings.POSTS_PER_PAGE)
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1    # if 'page' parameter is not an integer, default to page 1
    try:
        threads = paginator.page(page)
    except (EmptyPage, InvalidPage):
        threads = paginator.page(paginator.num_pages)
    return render(request, 'forums/view_forum.html', {'threads': threads, 'forum': forum, 'is_mod': is_mod},
                  context_instance=RequestContext(request))


@login_required
@permission_required('forums.add_forum', login_url=settings.FORBIDDEN_URL)
def add_forum(request):
    """Render and process a form to create a new forum."""
    log_page_view(request, 'Add Forum')
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
                log.info('%s (%s) added new forum \'%s\'', request.user.username, request.user.get_full_name(), forum.name)
                return HttpResponseRedirect(reverse('forums'))
    else:
        form = ForumForm()
    return render(request, 'forums/add_forum.html', {'form': form, 'create': True},
                  context_instance=RequestContext(request))


@login_required
@permission_required('forums.change_forum', login_url=settings.FORBIDDEN_URL)
def edit_forum(request, slug):
    """Render and process a form to modify an existing forum.

    Required arguments:
        - slug  =>  the slug of the forum to edit (as a string)

    If 'delete=true' appears in the request's query string, the forum will be deleted, along with all of its threads.

    """
    log_page_view(request, 'Edit Forum')
    forum = get_object_or_404(Forum, slug=slug)
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
            log.info('%s (%s) deleted forum \'%s\'', request.user.username, request.user.get_full_name(), forum.name)
            forum.delete()
            return HttpResponseRedirect(reverse('forums'))
        form = ForumForm(instance=forum)
    return render(request, 'forums/add_forum.html', {'form': form, 'forum': forum, 'create': False},
                  context_instance=RequestContext(request))


@login_required
def view_thread(request, forum, id, thread, page=1):
    """Render a specific page of a thread.

    Required arguments:
        - forum     =>  the slug of the forum to which the thread belongs (as a string)
        - id        =>  the unique ID of the thread to view (as an integer)
        - thread    =>  the slug of the thread to view (as a string)

    Optional arguments:
        - page  =>  the number of the page to view (as an integer): defaults to 1

    """

    log_page_view(request, 'View Thread')
    forum = get_object_or_404(Forum, slug=forum)
    thread = get_object_or_404(Thread, id=id)
    objects = Post.objects.filter(thread=thread).order_by('number')
    paginator = Paginator(objects, settings.POSTS_PER_PAGE)

    try:
        posts = paginator.page(int(page))
    except (EmptyPage, InvalidPage):
        posts = paginator.page(paginator.num_pages)

    profile = request.user.get_profile()
    is_mod = (profile in forum.moderators.all())
    subscribed = (profile in thread.subscribers.all())

    if subscribed and 'unsubscribe' in request.GET:
        profile.subscriptions.remove(thread)
        profile.save()
        return HttpResponseRedirect(reverse('view_thread_page', kwargs={'forum': forum.slug, 'id': thread.id,
                                                                        'thread': thread.slug, 'page': page}))
    elif not subscribed and 'subscribe' in request.GET:
        profile.subscriptions.add(thread)
        profile.save()
        return HttpResponseRedirect(reverse('view_thread_page', kwargs={'forum': forum.slug, 'id': thread.id,
                                                                        'thread': thread.slug, 'page': page}))

    return render(request, 'forums/view_thread.html',
                  {'thread': thread, 'posts': posts, 'forum': forum, 'subscribed': subscribed, 'is_mod': is_mod},
                  context_instance=RequestContext(request))


@login_required
def subscriptions(request):
    """Render a listing of all threads to which the current user is subscribed."""
    log_page_view(request, 'Subscribed Threads')
    threads = request.user.get_profile().subscriptions.all().order_by('-updated')
    return render(request, 'forums/subscriptions.html', {'threads': threads, 'subscribe': True},
                  context_instance=RequestContext(request))


@login_required
def my_threads(request):
    """Render a listing of all threads belonging to the current user."""
    log_page_view(request, 'My Threads')
    threads = Thread.objects.filter(owner=request.user.get_profile()).order_by('-updated')
    return render(request, 'forums/subscriptions.html', {'threads': threads, 'subscribe': False},
                  context_instance=RequestContext(request))


@login_required
@permission_required('forums.add_thread', login_url=settings.FORBIDDEN_URL)
def add_thread(request, slug):
    """Render and process a form to create a new thread.

    Required arguments:
        - slug  =>  the slug of the forum to which the new thread should belong (as a string)

    """
    log_page_view(request, 'Add Thread')
    forum = get_object_or_404(Forum, slug=slug)
    if request.method == 'POST':
        form = ThreadForm(request.POST)
        if form.is_valid():
            profile = request.user.get_profile()
            thread = form.save(commit=False)
            thread.forum = forum
            thread.owner = profile
            thread.slug = slugify(thread.title)
            thread.save()
            thread.subscribers.add(profile)
            thread.save()
            body = _bb_code_escape(form.cleaned_data.get('post'))
            post = Post.objects.create(thread=thread, user=profile, updated_by=profile, number=1, deleted=False, body=body)
            post.save()     # create and save the first post belonging to the new thread
            return HttpResponseRedirect(thread.get_absolute_url())
    else:
        form = ThreadForm()
    return render(request, 'forums/add_thread.html', {'form': form, 'forum': forum, 'create': True},
                  context_instance=RequestContext(request))


@login_required
@permission_required('forums.change_thread', login_url=settings.FORBIDDEN_URL)
def edit_thread(request, forum, id, thread):
    """Render and process a form to modify an existing thread and its first post.

    Required arguments:
        - forum     =>  the slug of the forum to which the thread belongs (as a string)
        - id        =>  the unique ID of the thread to edit (as an integer)
        - thread    =>  the slug of the thread to edit (as a string)

    The 'thread' argument is not used by the function, but it is present for URL consistency.

    If 'delete=true' appears in the request's query string, the thread will be deleted, along with all of its posts.

    """
    log_page_view(request, 'Edit Thread')
    forum = get_object_or_404(Forum, slug=forum)
    thread = get_object_or_404(Thread, id=id)
    first_post = get_object_or_404(Post, thread=thread, number=1)
    profile = request.user.get_profile()
    if thread.owner != profile and profile not in thread.forum.moderators.all() and not profile.is_admin():
        return HttpResponseRedirect(reverse('forbidden'))
    if request.method == 'POST':
        form = ThreadForm(request.POST, instance=thread)
        if form.is_valid():
            form.save()
            first_post.body = _bb_code_escape(form.cleaned_data.get('post'))
            first_post.updated_by = profile
            first_post.save()   # update and save the thread's first post
            return HttpResponseRedirect(thread.get_absolute_url())
    else:
        if 'delete' in request.GET and request.GET.get('delete') == 'true':
            thread.delete()
            return HttpResponseRedirect(forum.get_absolute_url())
        form = ThreadForm(instance=thread, initial={'post': _bb_code_unescape(first_post.body)})
    return render(request, 'forums/add_thread.html',
                  {'form': form, 'forum': forum, 'thread': thread, 'create': False},
                  context_instance=RequestContext(request))


@login_required
@permission_required('forums.add_post', login_url=settings.FORBIDDEN_URL)
def add_post(request, forum, id, thread):
    """Render and process a form to create a new post.

    Required arguments:
        - forum     =>  the slug of the forum to which the new post's thread belongs (as a string)
        - id        =>  the unique ID of the thread to which the new post should belong (as an integer)
        - thread    =>  the slug of the thread to which the new post should belong (as a string)

    """

    log_page_view(request, 'Reply to Thread')
    forum = get_object_or_404(Forum, slug=forum)
    thread = get_object_or_404(Thread, id=id)

    if request.method == 'POST':
        quote = None
        if 'quote' in request.POST:
            try:
                quote = Post.objects.get(thread=thread, number=int(request.POST.get('quote')))
            except Post.DoesNotExist:
                pass
        form = PostForm(request.POST)
        if form.is_valid():
            profile = request.user.get_profile()
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
            thread.save()   # set the thread's updated time to now, since the thread has a new post
            return HttpResponseRedirect(post.get_absolute_url())
    else:
        quote = None
        if 'quote' in request.GET:
            try:
                quote = Post.objects.get(thread=thread, number=int(request.GET.get('quote')))
            except Post.DoesNotExist:
                pass
        form = PostForm()

    return render(request, 'forums/add_post.html',
                  {'form': form, 'forum': forum, 'thread': thread, 'quote': quote, 'create': True},
                  context_instance=RequestContext(request))


@login_required
@permission_required('forums.change_post', login_url=settings.FORBIDDEN_URL)
def edit_post(request, id):
    """Render and process a form to modify an existing post.

    Required arguments:
        - id    =>  the unique ID of the post to edit (as an integer)

    If 'delete=true' appears in the request's query string, the post will be marked as deleted (i.e., post.deleted will
    be set to True), but the post instance will not actually deleted from the database.

    """
    log_page_view(request, 'Edit Post')
    post = get_object_or_404(Post, id=id)
    profile = request.user.get_profile()
    if post.user != profile and profile not in post.thread.forum.moderators.all() and not profile.is_admin():
        return HttpResponseRedirect(reverse('forbidden'))
    if request.method == 'POST':
        post.body = _bb_code_unescape(post.body)
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
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
    return render(request, 'forums/add_post.html',
                  {'form': form, 'forum': post.thread.forum, 'thread': post.thread, 'quote': post.quote, 'create': False, 'post': post},
                  context_instance=RequestContext(request))






## ============================================= ##
##                                               ##
##               Private Functions               ##
##                                               ##
## ============================================= ##


def _bb_code_escape(text):
    r"""Return an escaped version of the provided text, with BB markup converted to HTML.

    The text '<b>bold</b> & [B]bold[/B] [I]italic[/I] [U]underline[/U] \n [URL="/"]link[/URL]'
    becomes  '&lt;b&gt;bold&lt;/b&gt; &amp; <b>bold</b> <i>italic</i> <u>underline</u> <br /> <a href="/">link</a>'.

    Posts are rendered as-is (i.e., without HTML escaping) in the 'view_thread.html' template, so user input must be
    escaped before being stored in the database and rendered in the browser. Any HTML tags in the input will be
    converted to a safe representation (replacing '<', '>', and '&' with the HTML literals '&lt;', '&gt;', and '&amp;').
    Then any BB markup in the input ('[B]...[/B]', '[URL="..."]...[/URL]', etc.) is converted to HTML.

    """
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;') \
            .replace('[B]', '<b>').replace('[/B]', '</b>').replace('[I]', '<i>').replace('[/I]', '</i>') \
            .replace('[U]', '<u>').replace('[/U]', '</u>').replace('\n', '<br />') \
            .replace('[URL=\"', '<a href=\"').replace('\"]', '\">').replace('[/URL]', '</a>')


def _bb_code_unescape(text):
    r"""Return an unescaped version of the provided text, with HTML converted to BB markup.

    The text '&lt;b&gt;bold&lt;/b&gt; &amp; <b>bold</b> <i>italic</i> <u>underline</u> <br /> <a href="/">link</a>'
    becomes  '<b>bold</b> & [B]bold[/B] [I]italic[/I] [U]underline[/U] \n [URL="/"]link[/URL]'.

    When users edit posts, they expect to see the BB markup they originally wrote and not the escaped text returned by
    _bb_code_escape(). Additionally, if previously-escaped text is re-escaped, the escaped HTML tags will be removed
    and the post will not be properly formatted in the browser. This function avoids these issues by restoring escaped
    text to its original (unescaped) form.

    """
    return text.replace('<b>', '[B]').replace('</b>', '[/B]').replace('<i>', '[I]').replace('</i>', '[/I]') \
            .replace('<u>', '[U]').replace('</u>', '[/U]').replace('<br />', '\n') \
            .replace('<a href=\"', '[URL=\"').replace('\">', '\"]').replace('</a>', '[/URL]') \
            .replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
