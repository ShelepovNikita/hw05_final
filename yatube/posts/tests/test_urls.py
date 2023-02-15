
from http import HTTPStatus

from django.test import TestCase, Client

from posts.models import Post, Group, User
from posts.tests.constants import (INDEX_TEMPLATE,
                                   GROUP_LIST_TEMPLATE,
                                   PROFILE_TEMPLATE,
                                   CREATE_POST_TEMPLATE,
                                   POST_DETAIL_TEMPLATE,
                                   UNEXISTING_PAGE_TEMPLATE,
                                   FOLLOW_PAGE_TEMPLATE)


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user1 = User.objects.create_user(username='some_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )
        cls.URL_INDEX = '/'
        cls.URL_GROUP = f'/group/{PostURLTests.group.slug}/'
        cls.URL_PROFILE = f'/profile/{PostURLTests.user.username}/'
        cls.URL_POST_DETAIL = f'/posts/{PostURLTests.post.id}/'
        cls.URL_POST_CREATE = '/create/'
        cls.URL_UPDATE_POST = f'/posts/{PostURLTests.post.id}/edit/'
        cls.URL_UNEXISTING_PAGE = '/unexisting_page/'
        cls.URL_FOLLOW_PAGE = '/follow/'
        cls.URL_HTTP_STATUS_NAMES = (
            (cls.URL_INDEX, HTTPStatus.OK, INDEX_TEMPLATE),
            (cls.URL_GROUP, HTTPStatus.OK, GROUP_LIST_TEMPLATE),
            (cls.URL_PROFILE, HTTPStatus.OK, PROFILE_TEMPLATE),
            (cls.URL_POST_CREATE, HTTPStatus.FOUND, CREATE_POST_TEMPLATE),
            (cls.URL_POST_DETAIL, HTTPStatus.OK, POST_DETAIL_TEMPLATE),
            (cls.URL_UNEXISTING_PAGE, HTTPStatus.NOT_FOUND,
             UNEXISTING_PAGE_TEMPLATE),
            (cls.URL_FOLLOW_PAGE, HTTPStatus.FOUND, FOLLOW_PAGE_TEMPLATE)
        )

    def setUp(self):
        # Не авторизованный пользователь
        self.guest_client = Client()
        # Авторизованный пользователь - автор
        self.user = PostURLTests.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        # Авторизованный пользователь - не автор
        self.user1 = PostURLTests.user1
        self.authorized_client1 = Client()
        self.authorized_client1.force_login(self.user1)
        from django.core.cache import cache
        cache.clear()

    def test_urls_for_guest_users_at_desired_locations(self):
        """URL-адрес доступен любому пользователю."""
        for address, http_status, _ in self.URL_HTTP_STATUS_NAMES:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, http_status)

    def test_urls_for_auth_users_at_desired_locations(self):
        """URL-адрес доступен авторизованному пользователю."""
        response = self.authorized_client.get(self.URL_POST_CREATE)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for address, _, template in self.URL_HTTP_STATUS_NAMES:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_posts_posts_id_edit_working_right(self):
        """Страница редактирования поста работает корректно."""
        response = self.guest_client.get(self.URL_UPDATE_POST, follow=True)
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.id}/edit/'
        )
        response = self.authorized_client.get(self.URL_UPDATE_POST)
        self.assertTemplateUsed(response, CREATE_POST_TEMPLATE)
        response = self.authorized_client1.get(self.URL_UPDATE_POST)
        self.assertRedirects(
            response, f'/posts/{self.post.id}/'
        )

    def test_posts_create_url_redirect_anonymous_on_admin_login(self):
        """Страница по адресу /create/ перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.guest_client.get(self.URL_POST_CREATE, follow=True)
        self.assertRedirects(
            response, f'/auth/login/?next={self.URL_POST_CREATE}'
        )
