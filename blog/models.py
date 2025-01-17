from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.db.models import Count, Prefetch
from django.db.models import OuterRef, Subquery


class PostQuerySet(models.QuerySet):

    def year(self, year):
        """return queryset with posts in 'year',
        sorted by 'published_at' field"""
        return self.filter(published_at__year=year).order_by('published_at')

    def popular(self):
        return self.annotate(num_likes=Count('likes')).order_by('-num_likes')

    def fresh(self):
        return self.annotate(num_likes=Count('likes')).order_by('-num_likes')

    def prefetch_tags(self):
        return self.prefetch_related(
                        Prefetch(
                            'tags',
                            queryset=Tag.objects.order_by('title') \
                                                .annotate(
                                                    posts_count=Count('posts')
                                                )
                        )
        )

    def fetch_with_comments_count(self):
        query_posts = self
        query_posts_ids = [post.id for post in query_posts]
        posts_with_comments = Post.objects.filter(
            id__in=query_posts_ids
            ).annotate(comments_count=Count('comments'))

        ids_and_comments = posts_with_comments.values_list(
                                                'id',
                                                'comments_count'
                                                )
        count_for_id = dict(ids_and_comments)

        for post in query_posts:
            post.comments_count = count_for_id[post.id]
        return self


class TagQuerySet(models.QuerySet):

    def popular(self):
        return self.annotate(num_posts=Count('posts')).order_by('-num_posts')


class Post(models.Model):
    title = models.CharField('Заголовок', max_length=200)
    text = models.TextField('Текст')
    slug = models.SlugField('Название в виде url', max_length=200)
    image = models.ImageField('Картинка')
    published_at = models.DateTimeField('Дата и время публикации')

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='posts',
        limit_choices_to={'is_staff': True})
    likes = models.ManyToManyField(
        User,
        related_name='liked_posts',
        verbose_name='Кто лайкнул',
        blank=True)
    tags = models.ManyToManyField(
        'Tag',
        related_name='posts',
        verbose_name='Теги')
    objects = PostQuerySet.as_manager()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('post_detail', args={'slug': self.slug})

    def get_likes_count(self):
        return self.likes.count()

    class Meta:
        ordering = ['-published_at']
        verbose_name = 'пост'
        verbose_name_plural = 'посты'


class Tag(models.Model):
    title = models.CharField('Тег', max_length=20, unique=True)
    objects = TagQuerySet.as_manager()

    def __str__(self):
        return self.title

    def clean(self):
        self.title = self.title.lower()

    def get_absolute_url(self):
        return reverse('tag_filter', args={'tag_title': self.slug})

    class Meta:
        ordering = ['title']
        verbose_name = 'тег'
        verbose_name_plural = 'теги'


class Comment(models.Model):
    post = models.ForeignKey(
        'Post',
        related_name='comments',
        on_delete=models.CASCADE,
        verbose_name='Пост, к которому написан')
    author = models.ForeignKey(
        User,
        related_name='comments',
        on_delete=models.CASCADE,
        verbose_name='Автор')

    text = models.TextField('Текст комментария')
    published_at = models.DateTimeField('Дата и время публикации')

    def __str__(self):
        return f'{self.author.username} under {self.post.title}'

    class Meta:
        ordering = ['published_at']
        verbose_name = 'комментарий'
        verbose_name_plural = 'комментарии'
