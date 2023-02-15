
import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from posts.models import Post, Group, Comment, Follow, User
from posts.forms import PostForm, CommentForm
from posts.tests.constants import (INDEX_TEMPLATE,
                                   GROUP_LIST_TEMPLATE,
                                   CREATE_POST_TEMPLATE)

EXPECTED_POSTS_ON_FIRST_PAGE = 10
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        test_image = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        NAME_OF_IMAGE = 'test.gif'
        cls.uploaded = SimpleUploadedFile(
            name=NAME_OF_IMAGE,
            content=test_image,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='auth')
        cls.some_user = User.objects.create_user(username='follow')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug2',
            description='Тестовое описание2',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            text='Тестовый коммент',
            post=cls.post
        )

        cls.URL_INDEX = 'posts:index'
        cls.URL_GROUP_LIST = 'posts:group_list'
        cls.URL_POST_CREATE = 'posts:post_create'
        cls.URL_PROFILE = 'posts:profile'
        cls.URL_UPDATE_POST = 'posts:update_post'
        cls.URL_POST_DETAIL = 'posts:post_detail'
        cls.URL_FOLLOW_PAGE = 'posts:follow_index'
        cls.URL_PROFILE_FOLLOW = 'posts:profile_follow'
        cls.URL_PROFILE_UNFOLLOW = 'posts:profile_unfollow'

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)
        self.authorized_client1 = Client()
        self.authorized_client1.force_login(self.some_user)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        pages_templates_names = (
            (reverse(self.URL_INDEX),
             INDEX_TEMPLATE),
            (reverse(self.URL_GROUP_LIST, args=[self.group.slug]),
             GROUP_LIST_TEMPLATE),
            (reverse(self.URL_POST_CREATE),
             CREATE_POST_TEMPLATE),
        )

        for reverse_name, template in pages_templates_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        '''Шаблон index сформирован с правильным контекстом.'''
        expected_qs = Post.objects.all()
        response = self.client.get(reverse(self.URL_INDEX))
        context_qs = response.context.get('page_obj').object_list
        self.assertQuerysetEqual(expected_qs,
                                 context_qs,
                                 transform=lambda x: x
                                 )

    def test_group_list_page_show_correct_context(self):
        '''Шаблон group_list сформирован с правильным контекстом.'''
        expected_qs = Post.objects.filter(
            group=self.group2)
        response = self.client.get(reverse(self.URL_GROUP_LIST,
                                           args=[self.group2.slug]))
        context_qs = response.context.get('page_obj').object_list
        self.assertQuerysetEqual(expected_qs,
                                 context_qs,
                                 transform=lambda x: x
                                 )

    def test_create_post_page_show_correct_context(self):
        """Шаблон create_post сформирован с правильным
        контекстом для создания поста.
        """
        response = self.authorized_client.get(reverse(self.URL_POST_CREATE))
        form = response.context.get('form')
        self.assertIsInstance(form, PostForm)

    def test_create_post_page_show_correct_edit_context(self):
        """Шаблон create_post сформирован с правильным
        контекстом для редактирования поста.
        """
        response = self.authorized_client.get(reverse(
            self.URL_UPDATE_POST,
            args=[self.post.id]))
        form = response.context.get('form')
        is_edit = response.context.get('is_edit')
        self.assertIsInstance(form, PostForm)
        self.assertEqual(response.context.get('form').save(commit=False),
                         PostPagesTests.post)
        self.assertTrue(is_edit)

    def test_profile_page_show_correct_context(self):
        '''Шаблон profile сформирован с правильным контекстом.'''
        expected_qs = Post.objects.filter(
            author=self.user.id)
        response = self.client.get(reverse(self.URL_PROFILE,
                                           args=[self.user.username]))
        context_qs = response.context.get('page_obj').object_list
        self.assertQuerysetEqual(expected_qs,
                                 context_qs,
                                 transform=lambda x: x
                                 )

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            self.URL_POST_DETAIL,
            args=[self.post.id]))
        context_names = (
            ('post', Post),
            ('form', CommentForm),
        )
        for obj, obj_class in context_names:
            with self.subTest(obj=obj):
                context = response.context.get(obj)
                self.assertIsInstance(context, obj_class)
        expected_qs = Comment.objects.filter(
            post=self.post.id)
        context_qs = response.context.get('comments')
        self.assertQuerysetEqual(expected_qs,
                                 context_qs,
                                 transform=lambda x: x
                                 )

    def test_post_create_group_show_on_index_page(self):
        '''При создании поста при выборе группы,
        пост попадет на главную страницу и страницу указанной группы.
        '''
        urls_names = (reverse(self.URL_INDEX),
                      reverse(self.URL_GROUP_LIST, args=[self.group2.slug]))
        post = Post.objects.create(
            author=self.user,
            text='Тестовый post',
            group=self.group2
        )
        for url in urls_names:
            with self.subTest(url=url):
                response = self.client.get(url)
                first_object = response.context['page_obj'][0]
                self.assertEqual(first_object.text, post.text)
                self.assertEqual(first_object.group, post.group)
        response = self.client.get(reverse(self.URL_GROUP_LIST,
                                           args=[self.group.slug]))
        first_object = response.context['page_obj'][0]
        self.assertNotEqual(first_object.group, post.group)

    def test_first_page_ten_records_on_index_page(self):
        """В контекст главной страницы передается нужное количество постов.
        """
        posts = (
            Post(
                author=self.user,
                text='Тестовый пост' + str(i),
                group=self.group2
            ) for i in range(1, 13)
        )
        Post.objects.bulk_create(posts)
        response = self.client.get(reverse(self.URL_INDEX))
        self.assertEqual(len(response.context['page_obj']),
                         EXPECTED_POSTS_ON_FIRST_PAGE)

    def test_image_in_context(self):
        '''При выводе поста с картинкой изображение передается
        в словаре контекста.'''
        url_reverse_names = (
            ('page_obj', (reverse(self.URL_INDEX))),
            ('page_obj', (reverse(self.URL_PROFILE,
                                  args=[self.user.username]))),
            ('page_obj', (reverse(self.URL_GROUP_LIST,
                                  args=[self.group.slug]))),
            ('post', (reverse(self.URL_POST_DETAIL,
                              args=[self.post.id])))
        )
        for obj, url in url_reverse_names:
            with self.subTest(url=url):
                response = self.client.get(url)
                if obj == 'page_obj':
                    first_object_image = response.context[obj][0].image
                else:
                    first_object_image = response.context.get(obj).image
                self.assertEqual(self.post.image, first_object_image)

    def test_cache_index_page(self):
        '''Проверка кэширования главной страницы'''
        response = self.client.get(reverse(self.URL_INDEX))
        before_creation_content = response.content
        Post.objects.create(
            text='test_cache',
            author=self.user,
        )
        response = self.client.get(reverse(self.URL_INDEX))
        after_creation_content = response.content
        self.assertEqual(before_creation_content, after_creation_content)
        cache.clear()
        response = self.client.get(reverse(self.URL_INDEX))
        after_cache_clear_content = response.content
        self.assertNotEqual(after_creation_content, after_cache_clear_content)

    def test_authorised_user_following_authors(self):
        '''Авторизованный пользователь может подписываться на других
        пользователей и удалять их из подписок.'''
        follow_count = Follow.objects.count()
        self.authorized_client.get(reverse(self.URL_PROFILE_FOLLOW,
                                           args=[self.some_user.username]))
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.authorized_client.get(reverse(self.URL_PROFILE_UNFOLLOW,
                                           args=[self.some_user.username]))
        self.assertEqual(Follow.objects.count(), follow_count)

    def test_new_post_in_followers_page(self):
        '''Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех, кто не подписан.'''
        self.authorized_client.get(reverse(self.URL_PROFILE_FOLLOW,
                                           args=[self.some_user.username]))
        post = Post.objects.create(
            author=self.some_user,
            text='Following test',
            group=self.group2
        )
        response = self.authorized_client.get(reverse(self.URL_FOLLOW_PAGE))
        self.assertEqual(post, response.context['page_obj'].object_list[0])
        self.authorized_client1.get(reverse(self.URL_PROFILE_FOLLOW,
                                            args=[self.user.username]))
        response = self.authorized_client1.get(reverse(self.URL_FOLLOW_PAGE))
        self.assertNotEqual(post, response.context['page_obj'].object_list[0])
