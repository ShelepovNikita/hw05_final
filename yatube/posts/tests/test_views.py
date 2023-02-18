
import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from posts.models import Post, Group, Comment, Follow, User
from posts.forms import PostForm, CommentForm
from posts.tests.constants import (
    INDEX_TEMPLATE,
    GROUP_LIST_TEMPLATE,
    CREATE_POST_TEMPLATE
)
from posts.tests.constants import (
    NAME_OF_IMAGE,
    TEST_IMAGE,
)
from posts.tests.constants import (
    CREATE_POST_URL,
    INDEX_URL,
    FOLLOW_PAGE_URL,
    GROUP_LIST_URL,
    PROFILE_URL,
    PROFILE_FOLLOW_URL,
    PROFILE_UNFOLLOW_URL,
    POST_DETAIL_URL,
    UPDATE_POST_URL
)

EXPECTED_POSTS_ON_FIRST_PAGE = 10
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uploaded = SimpleUploadedFile(
            name=NAME_OF_IMAGE,
            content=TEST_IMAGE,
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
            (reverse(INDEX_URL),
             INDEX_TEMPLATE),
            (reverse(GROUP_LIST_URL, args=[self.group.slug]),
             GROUP_LIST_TEMPLATE),
            (reverse(CREATE_POST_URL),
             CREATE_POST_TEMPLATE),
        )

        for reverse_name, template in pages_templates_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        '''Шаблон index сформирован с правильным контекстом.'''
        expected_qs = Post.objects.all()
        response = self.client.get(reverse(INDEX_URL))
        context_qs = response.context.get('page_obj').object_list
        self.assertQuerysetEqual(expected_qs,
                                 context_qs,
                                 transform=lambda x: x
                                 )

    def test_group_list_page_show_correct_context(self):
        '''Шаблон group_list сформирован с правильным контекстом.'''
        response = self.client.get(reverse(GROUP_LIST_URL,
                                           args=[self.group2.slug]))
        group = response.context.get('group')
        self.assertEqual(self.group2.title, group.title)
        self.assertEqual(self.group2.slug, group.slug)
        self.assertEqual(self.group2.description, group.description)

    def test_create_post_page_show_correct_context(self):
        """Шаблон create_post сформирован с правильным
        контекстом для создания поста.
        """
        response = self.authorized_client.get(reverse(CREATE_POST_URL))
        form = response.context.get('form')
        self.assertIsInstance(form, PostForm)

    def test_create_post_page_show_correct_edit_context(self):
        """Шаблон create_post сформирован с правильным
        контекстом для редактирования поста.
        """
        response = self.authorized_client.get(reverse(
            UPDATE_POST_URL,
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
        response = self.client.get(reverse(PROFILE_URL,
                                           args=[self.user.username]))
        context_qs = response.context.get('page_obj').object_list
        self.assertQuerysetEqual(expected_qs,
                                 context_qs,
                                 transform=lambda x: x
                                 )

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            POST_DETAIL_URL,
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
        urls_names = (reverse(INDEX_URL),
                      reverse(GROUP_LIST_URL, args=[self.group2.slug]))
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
        response = self.client.get(reverse(GROUP_LIST_URL,
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
        response = self.client.get(reverse(INDEX_URL))
        self.assertEqual(len(response.context['page_obj']),
                         EXPECTED_POSTS_ON_FIRST_PAGE)

    def test_image_in_context(self):
        '''При выводе поста с картинкой изображение передается
        в словаре контекста.'''
        url_reverse_names = (
            ('page_obj', (reverse(INDEX_URL))),
            ('page_obj', (reverse(PROFILE_URL,
                                  args=[self.user.username]))),
            ('page_obj', (reverse(GROUP_LIST_URL,
                                  args=[self.group.slug]))),
            ('post', (reverse(POST_DETAIL_URL,
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
        response = self.client.get(reverse(INDEX_URL))
        Post.objects.all().delete()
        response = self.client.get(reverse(INDEX_URL))
        response_before_cache_clear = response.content
        self.assertEqual(response.content,
                         response_before_cache_clear)
        cache.clear()
        response = self.client.get(reverse(INDEX_URL))
        after_cache_clear_content = response.content
        self.assertNotEqual(response_before_cache_clear,
                            after_cache_clear_content)

    def test_authorised_user_following_authors(self):
        '''Авторизованный пользователь может подписываться на других
        пользователей и удалять их из подписок.'''
        follow_count = Follow.objects.count()
        self.authorized_client.get(reverse(PROFILE_FOLLOW_URL,
                                           args=[self.some_user.username]))
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.authorized_client.get(reverse(PROFILE_UNFOLLOW_URL,
                                           args=[self.some_user.username]))
        self.assertEqual(Follow.objects.count(), follow_count)

    def test_new_post_in_followers_page(self):
        '''Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех, кто не подписан.'''
        self.authorized_client.get(reverse(PROFILE_FOLLOW_URL,
                                           args=[self.some_user.username]))
        post = Post.objects.create(
            author=self.some_user,
            text='Following test',
            group=self.group2
        )
        response = self.authorized_client.get(reverse(FOLLOW_PAGE_URL))
        self.assertEqual(post, response.context['page_obj'].object_list[0])
        self.authorized_client1.get(reverse(PROFILE_FOLLOW_URL,
                                            args=[self.user.username]))
        response = self.authorized_client1.get(reverse(FOLLOW_PAGE_URL))
        self.assertNotEqual(post, response.context['page_obj'].object_list[0])
