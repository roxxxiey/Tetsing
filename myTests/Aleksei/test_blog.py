from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from blog.forms import PostForm, CommentForm
from blog.models import Post, Category, Location

User = get_user_model()

# Проверка корректности строковых представлений моделей

class BlogModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.category = Category.objects.create(
            title='Test Category',
            description='Test Description',
            slug='test-category',
            is_published=True
        )
        self.location = Location.objects.create(name='Test Location', is_published=True)
        self.post = Post.objects.create(
            title='Test Post',
            text='This is a test post',
            author=self.user,
            pub_date='2024-12-01 12:00',
            category=self.category,
            location=self.location,
            is_published=True
        )

    def test_post_str(self):
        self.assertEqual(str(self.post), 'Test Post')

    def test_category_str(self):
        self.assertEqual(str(self.category), 'Test Category')

    def test_location_str(self):
        self.assertEqual(str(self.location), 'Test Location')


# Проверка работы представлений и того, что страницы загружаются правильно и содержат нужную информацию.
class BlogViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.category = Category.objects.create(
            title='Test Category',
            description='Test Description',
            slug='test-category',
            is_published=True
        )
        self.post = Post.objects.create(
            title='Test Post',
            text='This is a test post',
            author=self.user,
            pub_date='2024-12-01 12:00',
            category=self.category,
            is_published=True
        )

    def test_index_view(self):
        response = self.client.get(reverse('blog:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Post')

    def test_post_detail_view(self):
        response = self.client.get(reverse('blog:post_detail', args=[self.post.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This is a test post')

    def test_category_posts_view(self):
        response = self.client.get(reverse('blog:category_posts', args=[self.category.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Post')

    def test_create_post_view(self):
        """Тестирование создания поста."""
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('blog:create_post'))
        self.assertEqual(response.status_code, 200)

        # Отправка данных формы
        form_data = {
            'title': 'New Test Post',
            'text': 'Test text for the new post',
            'pub_date': timezone.now(),
            'category': self.category.id
        }
        response = self.client.post(reverse('blog:create_post'), data=form_data)
        self.assertRedirects(response, reverse('blog:profile', args=[self.user.username]))
        self.assertEqual(Post.objects.count(), 2)  # Проверка, что пост добавлен

    def test_edit_post_view(self):
        """Тестирование редактирования поста."""
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('blog:edit_post', args=[self.post.id]))
        self.assertEqual(response.status_code, 200)

        form_data = {
            'title': 'Updated Test Post',
            'text': 'Updated text for the post',
            'category': self.category.id
        }
        response = self.client.post(reverse('blog:edit_post', args=[self.post.id]), data=form_data)
        self.assertRedirects(response, reverse('blog:post_detail', args=[self.post.id]))
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Updated Test Post')

    def test_delete_post_view(self):
        """Тестирование удаления поста."""
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('blog:delete_post', args=[self.post.id]))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('blog:delete_post', args=[self.post.id]))
        self.assertRedirects(response, reverse('blog:index'))
        self.assertEqual(Post.objects.count(), 0)  # Проверка, что пост удален

    def test_add_comment_view(self):
        """Тестирование добавления комментария к посту."""
        self.client.login(username='testuser', password='password123')
        comment_data = {'text': 'This is a test comment'}
        response = self.client.post(reverse('blog:add_comment', args=[self.post.id]), data=comment_data)
        self.assertRedirects(response, reverse('blog:post_detail', args=[self.post.id]))
        self.assertEqual(self.post.comments.count(), 1)  # Проверка, что комментарий добавлен

    def test_delete_comment_view(self):
        """Тестирование удаления комментария."""
        comment = self.post.comments.create(text='Comment to delete', author=self.user)
        self.client.login(username='testuser', password='password123')

        response = self.client.post(reverse('blog:delete_comment', args=[self.post.id, comment.id]))
        self.assertRedirects(response, reverse('blog:post_detail', args=[self.post.id]))
        self.assertEqual(self.post.comments.count(), 0)  # Проверка, что комментарий удален


# Проверка работы форм и их валидации

class BlogFormTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.category = Category.objects.create(
            title='Test Category',
            description='Test Description',
            slug='test-category',
            is_published=True
        )

    def test_post_form(self):
        form_data = {
            'title': 'New Test Post',
            'text': 'Test text for the new post',
            'pub_date': '2024-12-02 10:00',
            'category': self.category.id
        }
        form = PostForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_comment_form(self):
        form_data = {
            'text': 'This is a test comment'
        }
        form = CommentForm(data=form_data)
        self.assertTrue(form.is_valid())
