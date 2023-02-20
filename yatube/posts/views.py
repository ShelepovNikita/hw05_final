
from django.views.decorators.cache import cache_page
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator

from .models import Follow, Group, Post, User
from .forms import CommentForm, PostForm


def page(request, post, posts_per_page=10):
    paginator = Paginator(post, posts_per_page)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


@cache_page(20, key_prefix='index_page')
def index(request):
    return render(
        request,
        'posts/index.html',
        {'page_obj': page(
            request,
            Post.objects.select_related('author', 'group').all())}
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_obj = page(request, posts)
    context = {
        'page_obj': page_obj,
        'group': group,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    return render(
        request,
        'posts/profile.html',
        {'page_obj': page(request, author.posts.all()),
         'author': author,
         'following': (user.is_authenticated
                       and user != author
                       and not author.following.filter(
                           user_id=request.user.id).exists())})


def post_detail(request, post_id):
    return render(
        request,
        'posts/post_detail.html',
        {'post': get_object_or_404(Post, pk=post_id),
         'form': CommentForm(request.POST or None)})


@login_required
def post_create(request):
    form = PostForm(request.POST or None,
                    files=request.FILES or None,)
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', request.user)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    if not form.is_valid():
        return render(request, 'posts/create_post.html',
                      {'form': form, 'is_edit': True})
    form.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    return render(
        request,
        'posts/follow.html',
        {'page_obj': page(
            request,
            Post.objects.filter(author__following__user=request.user))})


@login_required
def profile_follow(request, username):
    if request.user.username == username:
        return redirect('posts:index')
    data = {
        'user': request.user,
        'author': get_object_or_404(User, username=username)
    }
    Follow.objects.get_or_create(**data)
    return redirect('posts:profile', data['author'])


@login_required
def profile_unfollow(request, username):
    get_object_or_404(
        Follow,
        user=request.user,
        author__username=username
    ).delete()
    return redirect(
        'posts:profile',
        username
    )
