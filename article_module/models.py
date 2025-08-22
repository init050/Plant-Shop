from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.urls import reverse
from django.utils import timezone
from django.core.validators import MinLengthValidator
from account_module.models import User
from datetime import timedelta


class ArticleQuerySet(models.QuerySet):
    def published(self):
        return self.filter(status=Article.PUBLISHED, publish_date__lte=timezone.now())
    
    def pending(self):
        return self.filter(status=Article.PENDING)
    
    def draft(self):
        return self.filter(status=Article.DRAFT)


class ArticleManager(models.Manager):
    def get_queryset(self):
        return ArticleQuerySet(self.model, using=self._db)
    
    def published(self):
        return self.get_queryset().published()
    
    def pending(self):
        return self.get_queryset().pending()
    
    def draft(self):
        return self.get_queryset().draft()


class Article(models.Model):
    DRAFT = 'draft'
    PENDING = 'pending'
    PUBLISHED = 'published'
    REJECTED = 'rejected'
    
    STATUS_CHOICES = [
        (DRAFT, _('Draft')),
        (PENDING, _('Pending Review')),
        (PUBLISHED, _('Published')),
        (REJECTED, _('Rejected')),
    ]
    
    title = models.CharField(
        max_length=200,
        validators=[MinLengthValidator(5)],
        verbose_name=_('Title')
    )
    slug = models.SlugField(
        max_length=250,
        unique=True,
        blank=True,
        verbose_name=_('Slug')
    )
    summary = models.TextField(
        max_length=300,
        verbose_name=_('Summary'),
        help_text=_('Brief description of the article')
    )
    content = models.TextField(
        verbose_name=_('Content')
    )
    image = models.ImageField(
        upload_to='images/articles/',
        blank=True,
        null=True,
        verbose_name=_('Featured Image')
    )
    
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='articles',
        verbose_name=_('Author')
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=DRAFT,
        verbose_name=_('Status')
    )
    
    publish_date = models.DateTimeField(
        default=timezone.now,
        verbose_name=_('Publish Date')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    rejection_reason = models.TextField(
        blank=True,
        verbose_name=_('Rejection Reason')
    )
    
    view_count = models.PositiveIntegerField(default=0)
    
    objects = ArticleManager()
    
    class Meta:
        ordering = ['-publish_date', '-created_at']
        verbose_name = _('Article')
        verbose_name_plural = _('Articles')
        indexes = [
            models.Index(fields=['status', 'publish_date']),
            models.Index(fields=['author', 'status']),
            models.Index(fields=['slug']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Article.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('article_module:detail', kwargs={'slug': self.slug})
    
    @property
    def is_published(self):
        return self.status == self.PUBLISHED and self.publish_date <= timezone.now()
    
    @classmethod
    def can_user_create_article(cls, user):
        if not user.is_authenticated:
            return False
        
        if user.is_staff or user.is_superuser:
            return True
        
        last_24_hours = timezone.now() - timedelta(hours=24)
        recent_articles = cls.objects.filter(
            author=user,
            created_at__gte=last_24_hours
        ).exclude(status=cls.REJECTED)
        
        return not recent_articles.exists()


class Comment(models.Model):
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=_('Article')
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='article_comments',
        verbose_name=_('Author')
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name=_('Parent Comment')
    )
    content = models.TextField(
        validators=[MinLengthValidator(3)],
        verbose_name=_('Content')
    )
    
    is_approved = models.BooleanField(
        default=True,
        verbose_name=_('Approved')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Comment')
        verbose_name_plural = _('Comments')
        indexes = [
            models.Index(fields=['article', 'is_approved']),
            models.Index(fields=['author', 'is_approved']),
        ]
    
    def __str__(self):
        return f'Comment by {self.author.username or self.author.email} on {self.article.title}'
    
    @property
    def is_reply(self):
        return self.parent is not None


class ArticleView(models.Model):
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='article_views'
    )
    ip_address = models.GenericIPAddressField()
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['article', 'ip_address']
        indexes = [
            models.Index(fields=['article', 'viewed_at']),
        ]

        