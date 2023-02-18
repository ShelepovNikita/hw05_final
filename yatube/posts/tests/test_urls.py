
from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User
from posts.tests.constants import (
    CREATE_POST_TEMPLATE,
    INDEX_TEMPLATE,
    FOLLOW_PAGE_TEMPLATE,
    GROUP_LIST_TEMPLATE,
    PROFILE_TEMPLATE,
    POST_DETAIL_TEMPLATE,
    UNEXISTING_PAGE_TEMPLATE,
)
from posts.tests.constants import (
    CREATE_POST_URL,
    INDEX_URL,
    FOLLOW_PAGE_URL,
    GROUP_LIST_URL,
    PROFILE_URL,
    POST_DETAIL_URL,
    UNEXISTING_PAGE_URL,
    UPDATE_POST_URL
)


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
        cls.URL_HTTP_STATUS_NAMES = (
            (reverse(CREATE_POST_URL), HTTPStatus.FOUND,
             CREATE_POST_TEMPLATE),
            (reverse(INDEX_URL), HTTPStatus.OK,
             INDEX_TEMPLATE),
            (reverse(FOLLOW_PAGE_URL), HTTPStatus.FOUND,
             FOLLOW_PAGE_TEMPLATE),
            (reverse(GROUP_LIST_URL, args=[cls.group.slug]), HTTPStatus.OK,
             GROUP_LIST_TEMPLATE),
            (reverse(PROFILE_URL, args=[cls.user.username]), HTTPStatus.OK,
             PROFILE_TEMPLATE),
            (reverse(POST_DETAIL_URL, args=[cls.post.id]), HTTPStatus.OK,
             POST_DETAIL_TEMPLATE),
            (UNEXISTING_PAGE_URL, HTTPStatus.NOT_FOUND,
             UNEXISTING_PAGE_TEMPLATE),)

    def setUp(self):
        # Не авторизованный пользователь
        self.guest_client = Client()
        # Авторизованный пользователь - автор
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.user)
        # Авторизованный пользователь - не автор
        self.authorized_client1 = Client()
        self.authorized_client1.force_login(PostURLTests.user1)
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
        response = self.authorized_client.get(reverse(CREATE_POST_URL))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for address, _, template in self.URL_HTTP_STATUS_NAMES:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_posts_posts_id_edit_working_right(self):
        """Страница редактирования поста работает корректно."""
        response = self.guest_client.get(
            reverse(UPDATE_POST_URL, args=[self.post.id]), follow=True)
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.id}/edit/'
        )
        response = self.authorized_client.get(
            reverse(UPDATE_POST_URL, args=[self.post.id]))
        self.assertTemplateUsed(response, CREATE_POST_TEMPLATE)
        response = self.authorized_client1.get(
            reverse(UPDATE_POST_URL, args=[self.post.id]))
        self.assertRedirects(
            response, f'/posts/{self.post.id}/'
        )

    def test_posts_create_url_redirect_anonymous_on_admin_login(self):
        """Страница по адресу /create/ перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.guest_client.get(reverse(CREATE_POST_URL), follow=True)
        self.assertRedirects(
            response, f'/auth/login/?next={reverse(CREATE_POST_URL)}'
        )
