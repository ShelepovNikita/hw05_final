
from django.test import TestCase

from posts.models import Comment, Follow, Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user1 = User.objects.create_user(username='some user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='При относительном импорте вы только указываете...',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Дизлайк',
        )
        cls.follow = Follow.objects.create(
            user=cls.user1,
            author=cls.user
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        objects_names = (
            (self.group.title, str(self.group)),
            (self.post.text[:15], str(self.post)),
        )
        for expected_object_name, object_name in objects_names:
            with self.subTest(expected_object_name=expected_object_name):
                self.assertEqual(expected_object_name, object_name)

    def test_post_verbose_name(self):
        """verbose_name в полях модели Post совпадает с ожидаемым."""
        field_verboses = (
            ('text', 'Текст поста'),
            ('pub_date', 'Дата публикации поста'),
            ('author', 'Автор поста'),
            ('group', 'Группа'),
            ('image', 'Картинка'),
        )
        for field, expected_value in field_verboses:
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).verbose_name,
                    expected_value)

    def test_post_help_text(self):
        """help_text в полях модели Post совпадает с ожидаемым."""
        field_verboses = (
            ('text', 'Текст нового поста'),
            ('group', 'Группа, к которой будет относиться пост'),
        )
        for field, expected_value in field_verboses:
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).help_text,
                    expected_value)

    def test_comment_verbose_name(self):
        """verbose_name в полях модели Comment совпадает с ожидаемым."""
        field_verboses = (
            ('post', 'Пост'),
            ('author', 'Автор комментария'),
            ('text', 'Текст комментария'),
            ('created', 'Дата публикации комментария'),
        )
        for field, expected_value in field_verboses:
            with self.subTest(field=field):
                self.assertEqual(
                    self.comment._meta.get_field(field).verbose_name,
                    expected_value)

    def test_follow_verbose_name(self):
        """verbose_name в полях модели Follow совпадает с ожидаемым."""
        field_verboses = (
            ('user', 'Подписчик'),
            ('author', 'Автор'),
        )
        for field, expected_value in field_verboses:
            with self.subTest(field=field):
                self.assertEqual(
                    self.follow._meta.get_field(field).verbose_name,
                    expected_value)
