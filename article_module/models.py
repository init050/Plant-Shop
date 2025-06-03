from django.db import models
from uuid import uuid4
from django.utils import timezone
from mptt.models import MPTTModel, TreeForeignKey
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.urls import reverse
from django.core.cache import cache
from datetime import timedelta
from django.db.models import Q, Count
from ckeditor_uploader.fields import RichTextUploadingField
from account_module.models import User
from taggit.managers import TaggableManager
from django.utils.html import strip_tags
from pathlib import Path 
from PIL import Image
from django.conf import settings
from django.contrib.sitemaps import _SupportsCount, _SupportsLen, _SupportsOrdered, Sitemap





def upload_article_image(instance, filename):
    ext = filename.split('.')[-1]
    filename = f'{uuid4().hex}.{ext}'
    return f'articles/{instance.slug}/{filename}'

def upload_article_thumbnail(instance, filename):
    ext = filename.split('.')[-1]
    filename = f'thumb_{uuid4().hex}.{ext}'
    return f'article/{instance.slug}/thumbnails{filename}'

class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at =models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        abstract = True


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)
    
    def with_deleted(self):
        return super().get_queryset()
    
    def only_deleted(self):
        return super().get_queryset().filter(is_deleted=True)


class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True


    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(using=using)


    def hard_delete(self):
        super().delete()

    
    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save()


class Category(MPTTModel, TimestampedModel):
    name = models.CharField(
        max_length=70,
        unique=True,
        validators=[MinLengthValidator(2)],
        help_text=_('Category name')
    )

    slug = models.SlugField(
        max_length=120,
        unique=True,
        help_text=_('URL-friendly category identifier')
    )

    description = models.TextField(
        max_length=500,
        blank=True,
        help_text=_('Category description for SEO')
    )

    parents = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories'
    )
    
    is_active = models.BooleanField(default=True, db_index=True)
    meta_title = models.CharField(max_length=60, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)


    image = models.ImageField(
        upload_to='images/articles/',
        null=True,
        blank=True,
        help_text=_('Category image')
    )

    class MPTTMeta:
        order_insertion_by = ['name']

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['tree_id', 'lft']
        indexes = [
            models.indexes(fields=['slug', 'is_active']),
            models.indexes(fields=['parents', 'is_active'])
        ]

    def __str__(self) -> str:
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('article_module:category_detail', kewargs={'slug':self.slug})
    

    @property
    def article_count(self):
        cache_key = f'category_article_count_{self.pk}'
        count = cache.get(cache_key)

        if count is None:
            descendants = self.get_descendants(include=True)
            count = Article.objects.filter(
                categories__in=descendants,
                status=Article.PUBLISHED

            ).distinct().count()
            cache.set(cache_key, count, timedelta(hours=1))
        return count



class ArticleQueryset(models.QuerySet):


    def published(self):
        return self.filter(
            status=Article.PUBLISHED,
            publish_date__lte=timezone.now()
        )

    def draft(self):
        return self.filter(status=Article.DRAFT)

    def featured(self):
        return self.filter(is_featured=True)

    def author(self, author):
        return self.filter(author=author)

    def by_category(self, category):
        if isinstance(category, str):
            return self.filter(categories__slug=category)
        return self.filter(categories=category)
        

    def search(self, query):
        return self.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(excerpt__icontains=query) |
            Q(tag__name__icontains=query)
        ).distinct()
    


class ArticleManager(SoftDeleteManager):
    def get_queryset(self):
        return ArticleQueryset(self.model, using=self.db).filter(is_deleted=False)
    
    def published(self):
        return self.get_queryset().published()

    def featured(self):
        return self.get_queryset().featured()
    
    def popular(self, days=30):
        since = timezone.now() - timezone.timedelta(days=days)
        return self.get_queryset().published().filter(
            views__created__at__gte=since
        ).annotate(
            recent_view=Count('views', filter=Q(views__created__at__gte=since))
        ).order_by('-recent_views')



class Article(TimestampedModel, SoftDeleteModel):

    DRAFT = 'draft'
    PUBLISHED = 'published'
    ARCHIVED = 'archived'
    PENDING = 'pending'
    

    STATUS_CHOICES = [
        (DRAFT, 'Draft'),
        (PUBLISHED, 'Published'),
        (ARCHIVED, 'Archived'),
        (PENDING, 'Pending Review'),
    ]


    title = models.CharField(
        max_length=200,
        validators=[MinLengthValidator(5)],
        help_text=_('Article title (5-200 characters')
    )

    slug = models.SlugField(
        max_length=250,
        unique=True,
        help_text=_('URL-friendly identifier')
    )

    excerpt = models.TextField(
        max_length=300,
        help_text=_('Brief description for previews and SEO')
    )

    content = RichTextUploadingField(
        help_text=_('Main article content with rich text editor')
    )


    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='articles',
        db_index=True
    )
    categories = models.ManyToManyField(
        Category,
        related_name='articles',
        help_text="Select one or more categories"
    )

    tags = TaggableManager(
        blank=True,
        help_text=_('Comma-separated tags')
    )


    status = models.CharField(
        max_length=25,
        choices=STATUS_CHOICES,
        default=DRAFT,
        db_index=True
    )

    publish_date = models.DateTimeField(
        default=timezone.now(),
        db_index=True,
        help_text=_('When to publish this article')
    )
    
    is_featured = models.BooleanField(
        default=False,
        help_text=_('Featured articles appear prominently'),
        db_index=True
    )
    

    is_premium = models.BooleanField(
        default=False,
        help_text=_('Premium content for subscribers only')
    )

    is_pinned = models.BooleanField(
        default=False,
        help_text=_('Pin article to top of category')
    )

    allow_comments = models.BooleanField(
        default=True,
        help_text=_('Allow users to comment on this article')
    )

    featured_image = models.ImageField(
        upload_to=upload_article_image(),
        blank=True,
        null=True,
        help_text=_('Main article image')
    )

    featured_image_alt = models.CharField(
        max_length=200,
        blank=True,
        help_text=_('Alt text for featured image (SEO)')
    )

    thumbnail = models.ImageField(
        upload_to=upload_article_thumbnail,
        null=True,
        blank=True,
        help_text=_('Auto-generated thumbnail')
    )


    meta_title = models.CharField(
        max_length=60,
        blank=True,
        help_text=_('SEO title (leave blank to use article title)')
    )
    meta_description = models.CharField(
        max_length=160,
        blank=True,
        help_text=_('SEO description (leave blank to use excerpt)')
    )
    canonical_url = models.URLField(
        blank=True,
        help_text=_('Canonical URL if content is republished')
    )

    
    reading_time = models.PositiveIntegerField(
        default=0,
        help_text=_('Estimated reading time in minutes')
    )

    word_count = models.PositiveIntegerField(
        default=0,
        help_text=_('Article word count')
    )



    objects = ArticleManager()
    all_objects = models.Manager()


    class Meta:
        ordering = ['-publish_date', '-created_at']
        verbose_name = 'Article'
        verbose_name_plural = 'Articles'
        indexes = [
            models.indexes(fields=['status', 'publish_date']),
            models.indexes(fields=['author', 'status']),
            models.indexes(fields=['is_featured', 'status']),
            models.indexes(fields=['slug']),
            models.indexes(fields=['publish_date'])
        ]

        permissions = [
            ('can_publish_article', 'Can publish articles'),
            ('can_feature_article', 'Can feature articles'),
            ('can_edit_all_articles', 'Can edit all articles'),
        ]

    
    def __str__(self):
        return self.title
    

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)


        if not self.pk:
            original_slug = self.slug
            counter = 1
            while Article.objects.filter(slug=self.slug).exists():
                self.slug = f'{original_slug}-{counter}'
                counter += 1


        if not self.meta_title:
            self.meta_title = self.title[:60]
        if not self.meta_description:
            self.meta_description = strip_tags(self.excerpt)[:160]


        if self.content:
            content_text = strip_tags(self.content)
            self.word_count = len(content_text.split())
            self.reading_time = max(1, self.word_count // 200)


        super().save(*args, **kwargs)

        if self.featured_image and not self.thumbnail:
            self.generate_thumbnail()


    def get_absolute_url(self):
        return reverse('article_module:detail', kwargs={'slug': self.slug})


    def generate_thumbnail(self):
        if not self.featured_image:
            return
        try:
            image = Image.open(self.featured_image.path)
            image.thumbnail((300*200), Image.Resampling.LANCZOS)

            base_path = Path(self.featured_image.path)
            thumb_path = base_path.parent / f'thumb_{base_path.name}'

            image.save(thumb_path, optimize=True, quality=85)
            self.thumbnail.name = str(thumb_path.relative_to(settings.MEDIA_ROOT))
            self.save(update_fields=['thumbnail'])

        except Exception as e:
            print(f'Error generating thumbnail: {e}')
        
            
    @property
    def is_published(self):
        return (
            self.status == self.PUBLISHED and
            self.publish_date <= timezone.now()
        )

    @property
    def view_count(self):
        return self.views.count()
    

    @property
    def comment_count(self):
        return self.comments.count()
    
    
    def get_related_articles(self, limit=5):

        cache_key = f'related_articles_{self.pk}_{limit}'

        if not(related := cache.get(cache_key)):
            my_categories = self.categories.values_list('id', flat=True)
            my_tags = self.tags.values_list('id', flat=True)

            related = list(Article.objects.published()
                           .exclude(pk=self.pk)
                           .filter(Q(categories__in=my_categories) | Q(tag__in=my_tags))
                           .distinct()
                           .annonate(relevance=Count('categories', filter=Q(categories__in=my_categories))+
                                            Count('tags', filter=Q(tags__in=my_tags)))
                           .order_by('-relevance', '-publish_date')
                           .select_related() 
                           [:limit])
            cache.set(cache_key, related, 1800)

        return related


    def can_be_edited_by(self, user):
        if user.is_superuser:
            return True
        if user.has_perm('article.can_edit_all_articles'):
            return True
        return self.author == user
    

    def can_be_published_by(self, user):
        if user.is_superuser:
            return True
        if user.has_perm('article.can_publish_article'):
            return True
        return False
    

class Comment(MPTTModel, TimestampedModel, SoftDeleteModel):


    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='comments',
        db_index=True
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        help_text=_('Reply to another comment')
    )
    content = models.TextField(
        validators=[
            MinLengthValidator(3),
            MaxLengthValidator(1000)
        ],
        help_text=_('Comment content (3-1000 characters)')
    )


    is_aproved = models.BooleanField(
        default=False,
        help_text=_('Approved comments are visible to public'),
        db_index=True
    )

    is_flagged = models.BooleanField(
        default=False,
        help_text=_('Flagged comments need review')
    )
    moderator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderated_comments'
    )
    moderation_reason = models.CharField(
        max_length=200,
        blank=True,
        help_text=_('Reason for moderation action')
    )

    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)


    objects = SoftDeleteManager()

    class MPTTMeta:
        order_insertion_by = ['-created_at']


    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['article', 'is_approved']),
            models.Index(fields=['author', 'is_approved']),
            models.Index(fields=['parent', 'is_approved']),
            models.Index(fields=['-created_at']),
        ]
        permissions = [
            ('can_moderate_comments', 'Can moderate comments'),
            ('can_approve_comments', 'Can approve comments'),
        ]

    def __str__(self) -> str:
        return f'Comment on {self.author.username} on {self.article.title}'
    
    def get_absolute_url(self):
        return f'{self.article.get_absolute_url()}#comment-{self.pk}'
    
    @property
    def reply_count(self):
        return self.get_descendant_count()
    

class ArticleView(TimestampedModel):
    """Track article views for analytics"""
    
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='views',
        db_index=True
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='article_views'
    )
    ip_address = models.GenericIPAddressField()
    session_key = models.CharField(max_length=40, blank=True)
    user_agent = models.TextField(blank=True)
    referrer = models.URLField(blank=True)
    
    class Meta:
        unique_together = ['article', 'ip_address', 'session_key']
        indexes = [
            models.Index(fields=['article', 'created_at']),
            models.Index(fields=['ip_address']),
        ]
    
    def __str__(self):
        return f'View of {self.article.title} from {self.ip_address}'


class ArticleRating(TimestampedModel):
    
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    article = models.ForeignKey(
        Article,
        db_index=True,
        on_delete=models.CASCADE,
        related_name='rating'
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='article_rating'
    )

    score = models.PositiveIntegerField(choices=RATING_CHOICES)
    review = models.TextField(max_length=200, blank=True)


    class Meta:
        unique_together = ['article', 'user']
        indexes = [
            models.indexes(fields=['article', 'score'])
        ]

    def __str__(self):
        return f"{self.user.username} rated {self.article.title}: {self.score}/5"
    


class ArticleSitemap(Sitemap):
    changedreq = 'weekly'
    priority = 0.8

    def items(self):
        return Article.objects.published()
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return obj.get_absolute_url()