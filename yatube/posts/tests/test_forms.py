
import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Post, Group, Comment, User

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
        # cls.comment = Comment.objects.create()

        cls.URL_POST_CREATE = 'posts:post_create'
        cls.URL_PROFILE = 'posts:profile'
        cls.URL_UPDATE_POST = 'posts:update_post'
        cls.URL_POST_DETAIL = 'posts:post_detail'
        cls.URL_ADD_COMMENT = 'posts:add_comment'

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTest.user)

    def test_post_create(self):
        '''Валидная форма создает запись в Post.'''
        posts_count = Post.objects.count()
        test_image = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

        NAME_OF_IMAGE = 'test.gif'

        uploaded = SimpleUploadedFile(
            name=NAME_OF_IMAGE,
            content=test_image,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый пост 1',
            'group': self.post.group.id,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse(self.URL_POST_CREATE),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse(self.URL_PROFILE,
                                               args=[self.user.username]))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                author=self.user.id,
                text=form_data['text'],
                group=form_data['group'],
                image=f'posts/{NAME_OF_IMAGE}'
            ).exists()
        )

    def test_post_edit(self):
        '''Изменение поста с post_id в базе данных.'''
        post_edit_text = 'Тестовый пост 2 - отредактированный'
        form_data = {
            'text': post_edit_text,
            'group': self.post.group.id
        }
        response = self.authorized_client.post(
            reverse(self.URL_UPDATE_POST, args=[self.post.id]),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse(self.URL_POST_DETAIL,
                                               args=[self.post.id]))
        self.assertTrue(Post.objects.filter(**form_data).exists())

    def test_add_comment(self):
        '''Валидная форма создает запись в Comments.'''
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Текст комментария'
        }
        response = self.authorized_client.post(
            reverse(self.URL_ADD_COMMENT, args=[self.post.id]),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(self.URL_POST_DETAIL,
                                               args=[self.post.id]))
        self.assertEqual(Post.objects.count(), comments_count + 1)
        self.assertTrue(Comment.objects.filter(**form_data).exists())
