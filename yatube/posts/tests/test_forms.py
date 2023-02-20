
import shutil
import tempfile

from django.test import Client, override_settings, TestCase
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Comment, Group, Post, User
from posts.tests.constants import (
    ADD_COMMENT_URL,
    CREATE_POST_URL,
    PROFILE_URL,
    POST_DETAIL_URL,
    UPDATE_POST_URL
)
from posts.tests.constants import (
    IMAGE,
    NAME_OF_IMAGE,
    TEST_IMAGE,
)

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
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

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTest.user)

    def tearDown(self):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_post_create(self):
        '''Валидная форма создает запись в Post.'''
        posts_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name=NAME_OF_IMAGE,
            content=TEST_IMAGE,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый пост 1',
            'group': self.post.group.id,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse(CREATE_POST_URL),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse(PROFILE_URL,
                                               args=[self.user.username]))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        post = Post.objects.first()
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.image, IMAGE)

    def test_post_edit(self):
        '''Изменение поста с post_id в базе данных.'''
        uploaded = SimpleUploadedFile(
            name=NAME_OF_IMAGE,
            content=TEST_IMAGE,
            content_type='image/gif'
        )
        post_edit_text = 'Тестовый пост 2 - отредактированный'
        form_data = {
            'text': post_edit_text,
            'group': self.post.group.id,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse(UPDATE_POST_URL, args=[self.post.id]),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse(POST_DETAIL_URL,
                                               args=[self.post.id]))
        post = Post.objects.first()
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.image, IMAGE)

    def test_add_comment(self):
        '''Валидная форма создает запись в Comments.'''
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Текст комментария'
        }
        response = self.authorized_client.post(
            reverse(ADD_COMMENT_URL, args=[self.post.id]),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(POST_DETAIL_URL,
                                               args=[self.post.id]))
        self.assertEqual(Post.objects.count(), comments_count + 1)
        comment = Comment.objects.first()
        self.assertEqual(comment.text, form_data['text'])
