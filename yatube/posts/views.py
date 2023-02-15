
from django.shortcuts import render, get_object_or_404
from django.shortcuts import redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page

from .models import Post, Group, Follow
from .forms import PostForm, CommentForm

User = get_user_model()

POSTS_ON_PAGE = 10


def page(request, post):
    paginator = Paginator(post, POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


@cache_page(20, key_prefix='index_page')
def index(request):
    posts = Post.objects.all()
    page_obj = page(request, posts)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


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
    author = User.objects.get(username=username)
    author_posts = author.posts.all()
    page_obj = page(request, author_posts)
    users = author.following.filter(user_id=request.user.id)
    if len(users) == 0:
        following = False
    else:
        following = True
    context = {
        'page_obj': page_obj,
        'author': author,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        'post': post,
        'form': form,
        'comments': comments
    }
    return render(request, 'posts/post_detail.html', context)


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
    comment = form.save(commit=False)
    comment.author = request.user
    comment.post = post
    comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    user = User.objects.get(username=request.user.username)
    authors = user.follower.all()
    id_authors = []
    for author in authors:
        id_authors.append(author.author_id)
    posts = Post.objects.filter(author__in=[*id_authors])
    page_obj = page(request, posts)
    context = {
        'page_obj': page_obj,
        'authors': authors,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = User.objects.get(username=username)
    data = {
        'user': request.user,
        'author': author
    }
    if request.user == author:
        return redirect('posts:index')
    if Follow.objects.filter(**data).exists():
        return redirect('posts:index')
    Follow.objects.create(**data)
    return redirect('posts:profile', author)


@login_required
def profile_unfollow(request, username):
    author = User.objects.get(username=username)
    authors = author.following.filter(user_id=request.user.id)
    authors.delete()
    return redirect('posts:profile', author)
