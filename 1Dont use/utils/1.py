# models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.urls import reverse
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db.models import Q, Count, Avg
from PIL import Image
import os
from uuid import uuid4
from mptt.models import MPTTModel, TreeForeignKey
from ckeditor_uploader.fields import RichTextUploadingField
from taggit.managers import TaggableManager
from django.core.cache import cache
from django.utils.html import strip_tags
from django.contrib.sitemaps import Sitemap


def upload_article_image(instance, filename):
    """Upload path for article images with UUID"""
    ext = filename.split('.')[-1]
    filename = f"{uuid4().hex}.{ext}"
    return f"articles/{instance.slug}/{filename}"


def upload_article_thumbnail(instance, filename):
    """Upload path for article thumbnails"""
    ext = filename.split('.')[-1]
    filename = f"thumb_{uuid4().hex}.{ext}"
    return f"articles/{instance.slug}/thumbnails/{filename}"


class TimestampedModel(models.Model):
    """Abstract base model with timestamp fields"""
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    
    class Meta:
        abstract = True


class SoftDeleteManager(models.Manager):
    """Manager for soft delete functionality"""
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)
    
    def with_deleted(self):
        return super().get_queryset()
    
    def only_deleted(self):
        return super().get_queryset().filter(is_deleted=True)


class SoftDeleteModel(models.Model):
    """Abstract model for soft delete functionality"""
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    objects = SoftDeleteManager()
    all_objects = models.Manager()
    
    class Meta:
        abstract = True
    
    def delete(self, using=None, keep_parents=False):
        """Soft delete implementation"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(using=using)
    
    def hard_delete(self):
        """Permanent delete"""
        super().delete()
    
    def restore(self):
        """Restore soft deleted object"""
        self.is_deleted = False
        self.deleted_at = None
        self.save()


class Category(MPTTModel, TimestampedModel):
    """Hierarchical category model using MPTT"""
    name = models.CharField(
        max_length=100,
        unique=True,
        validators=[MinLengthValidator(2)],
        help_text="Category name"
    )
    slug = models.SlugField(
        max_length=120,
        unique=True,
        help_text="URL-friendly category identifier"
    )
    description = models.TextField(
        blank=True,
        max_length=500,
        help_text="Category description for SEO"
    )
    parent = TreeForeignKey(
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
        upload_to='categories/',
        null=True,
        blank=True,
        help_text="Category image"
    )
    
    class MPTTMeta:
        order_insertion_by = ['name']
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['tree_id', 'lft']
        indexes = [
            models.Index(fields=['slug', 'is_active']),
            models.Index(fields=['parent', 'is_active']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('article:category_detail', kwargs={'slug': self.slug})
    
    @property
    def article_count(self):
        """Get article count for this category and subcategories"""
        cache_key = f"category_article_count_{self.pk}"
        count = cache.get(cache_key)
        if count is None:
            descendants = self.get_descendants(include_self=True)
            count = Article.objects.filter(
                categories__in=descendants,
                status=Article.PUBLISHED
            ).distinct().count()
            cache.set(cache_key, count, 3600)  # Cache for 1 hour
        return count


class ArticleQuerySet(models.QuerySet):
    """Custom QuerySet for Article model"""
    
    def published(self):
        return self.filter(
            status=Article.PUBLISHED,
            publish_date__lte=timezone.now()
        )
    
    def draft(self):
        return self.filter(status=Article.DRAFT)
    
    def featured(self):
        return self.filter(is_featured=True)
    
    def by_author(self, author):
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
            Q(tags__name__icontains=query)
        ).distinct()
    
    def with_stats(self):
        """Annotate with statistics"""
        return self.annotate(
            comment_count=Count('comments', filter=Q(comments__is_approved=True)),
            avg_rating=Avg('ratings__score'),
            view_count_total=Count('views')
        )


class ArticleManager(SoftDeleteManager):
    """Custom manager for Article model"""
    
    def get_queryset(self):
        return ArticleQuerySet(self.model, using=self._db).filter(is_deleted=False)
    
    def published(self):
        return self.get_queryset().published()
    
    def featured(self):
        return self.get_queryset().featured()
    
    def popular(self, days=30):
        """Get popular articles based on views in last N days"""
        since = timezone.now() - timezone.timedelta(days=days)
        return self.get_queryset().published().filter(
            views__created_at__gte=since
        ).annotate(
            recent_views=Count('views', filter=Q(views__created_at__gte=since))
        ).order_by('-recent_views')


class Article(TimestampedModel, SoftDeleteModel):
    """Advanced Article model with all professional features"""
    
    # Status choices
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
    
    # Core fields
    title = models.CharField(
        max_length=200,
        validators=[MinLengthValidator(5)],
        help_text="Article title (5-200 characters)"
    )
    slug = models.SlugField(
        max_length=250,
        unique=True,
        help_text="URL-friendly identifier"
    )
    excerpt = models.TextField(
        max_length=300,
        help_text="Brief description for previews and SEO"
    )
    content = RichTextUploadingField(
        help_text="Main article content with rich text editor"
    )
    
    # Metadata
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
        help_text="Comma-separated tags"
    )
    
    # Status and publishing
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=DRAFT,
        db_index=True
    )
    publish_date = models.DateTimeField(
        default=timezone.now,
        help_text="When to publish this article",
        db_index=True
    )
    
    # Features
    is_featured = models.BooleanField(
        default=False,
        help_text="Featured articles appear prominently",
        db_index=True
    )
    is_premium = models.BooleanField(
        default=False,
        help_text="Premium content for subscribers only"
    )
    allow_comments = models.BooleanField(
        default=True,
        help_text="Allow users to comment on this article"
    )
    is_pinned = models.BooleanField(
        default=False,
        help_text="Pin article to top of category"
    )
    
    # Media
    featured_image = models.ImageField(
        upload_to=upload_article_image,
        null=True,
        blank=True,
        help_text="Main article image"
    )
    thumbnail = models.ImageField(
        upload_to=upload_article_thumbnail,
        null=True,
        blank=True,
        help_text="Auto-generated thumbnail"
    )
    featured_image_alt = models.CharField(
        max_length=200,
        blank=True,
        help_text="Alt text for featured image (SEO)"
    )
    
    # SEO fields
    meta_title = models.CharField(
        max_length=60,
        blank=True,
        help_text="SEO title (leave blank to use article title)"
    )
    meta_description = models.CharField(
        max_length=160,
        blank=True,
        help_text="SEO description (leave blank to use excerpt)"
    )
    canonical_url = models.URLField(
        blank=True,
        help_text="Canonical URL if content is republished"
    )
    
    # Reading statistics
    reading_time = models.PositiveIntegerField(
        default=0,
        help_text="Estimated reading time in minutes"
    )
    word_count = models.PositiveIntegerField(
        default=0,
        help_text="Article word count"
    )
    
    # Managers
    objects = ArticleManager()
    all_objects = models.Manager()
    
    class Meta:
        ordering = ['-publish_date', '-created_at']
        verbose_name = "Article"
        verbose_name_plural = "Articles"
        indexes = [
            models.Index(fields=['status', 'publish_date']),
            models.Index(fields=['author', 'status']),
            models.Index(fields=['is_featured', 'status']),
            models.Index(fields=['slug']),
            models.Index(fields=['-publish_date']),
        ]
        permissions = [
            ('can_publish_article', 'Can publish articles'),
            ('can_feature_article', 'Can feature articles'),
            ('can_edit_all_articles', 'Can edit all articles'),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Auto-generate slug
        if not self.slug:
            self.slug = slugify(self.title)
            
        # Ensure unique slug
        if not self.pk:
            original_slug = self.slug
            counter = 1
            while Article.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        
        # Auto-generate meta fields if empty
        if not self.meta_title:
            self.meta_title = self.title[:60]
        if not self.meta_description:
            self.meta_description = strip_tags(self.excerpt)[:160]
        
        # Calculate reading time and word count
        if self.content:
            content_text = strip_tags(self.content)
            self.word_count = len(content_text.split())
            self.reading_time = max(1, self.word_count // 200)  # ~200 words per minute
        
        super().save(*args, **kwargs)
        
        # Generate thumbnail after saving
        if self.featured_image and not self.thumbnail:
            self.generate_thumbnail()
    
    def get_absolute_url(self):
        return reverse('article:detail', kwargs={'slug': self.slug})
    
    def generate_thumbnail(self):
        """Generate thumbnail from featured image"""
        if not self.featured_image:
            return
        
        try:
            image = Image.open(self.featured_image.path)
            image.thumbnail((300, 200), Image.Resampling.LANCZOS)
            
            thumb_path = self.featured_image.path.replace(
                os.path.basename(self.featured_image.path),
                f"thumb_{os.path.basename(self.featured_image.path)}"
            )
            
            image.save(thumb_path, optimize=True, quality=85)
            
            # Update thumbnail field
            relative_path = os.path.relpath(thumb_path, settings.MEDIA_ROOT)
            self.thumbnail.name = relative_path
            Article.objects.filter(pk=self.pk).update(thumbnail=relative_path)
            
        except Exception as e:
            print(f"Error generating thumbnail: {e}")
    
    @property
    def is_published(self):
        return (
            self.status == self.PUBLISHED and
            self.publish_date <= timezone.now()
        )
    
    @property
    def comment_count(self):
        return self.comments.filter(is_approved=True).count()
    
    @property
    def view_count(self):
        return self.views.count()
    
    def get_related_articles(self, limit=5):
        """Get related articles based on categories and tags"""
        cache_key = f"related_articles_{self.pk}_{limit}"
        related = cache.get(cache_key)
        
        if related is None:
            # Get articles with same categories or tags
            related = Article.objects.published().exclude(pk=self.pk).filter(
                Q(categories__in=self.categories.all()) |
                Q(tags__in=self.tags.all())
            ).distinct().annotate(
                relevance=Count('categories', filter=Q(categories__in=self.categories.all())) +
                          Count('tags', filter=Q(tags__in=self.tags.all()))
            ).order_by('-relevance', '-publish_date')[:limit]
            
            cache.set(cache_key, list(related), 1800)  # Cache for 30 minutes
        
        return related
    
    def can_be_edited_by(self, user):
        """Check if user can edit this article"""
        if user.is_superuser:
            return True
        if user.has_perm('article.can_edit_all_articles'):
            return True
        return self.author == user
    
    def can_be_published_by(self, user):
        """Check if user can publish this article"""
        if user.is_superuser:
            return True
        if user.has_perm('article.can_publish_article'):
            return True
        return False


class Comment(MPTTModel, TimestampedModel, SoftDeleteModel):
    """Hierarchical comment system with moderation"""
    
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
        help_text="Reply to another comment"
    )
    content = models.TextField(
        validators=[
            MinLengthValidator(3),
            MaxLengthValidator(1000)
        ],
        help_text="Comment content (3-1000 characters)"
    )
    
    # Moderation
    is_approved = models.BooleanField(
        default=True,
        help_text="Approved comments are visible to public",
        db_index=True
    )
    is_flagged = models.BooleanField(
        default=False,
        help_text="Flagged comments need review"
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
        help_text="Reason for moderation action"
    )
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
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
    
    def __str__(self):
        return f"Comment by {self.author.username} on {self.article.title}"
    
    def get_absolute_url(self):
        return f"{self.article.get_absolute_url()}#comment-{self.pk}"
    
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
        return f"View of {self.article.title} from {self.ip_address}"


class ArticleRating(TimestampedModel):
    """Article rating system"""
    
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]  # 1-5 stars
    
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='ratings',
        db_index=True
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='article_ratings'
    )
    score = models.PositiveIntegerField(choices=RATING_CHOICES)
    review = models.TextField(blank=True, max_length=500)
    
    class Meta:
        unique_together = ['article', 'user']
        indexes = [
            models.Index(fields=['article', 'score']),
        ]
    
    def __str__(self):
        return f"{self.user.username} rated {self.article.title}: {self.score}/5"


# Sitemap for SEO
class ArticleSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8
    
    def items(self):
        return Article.objects.published()
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return obj.get_absolute_url()


# Signal handlers
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


@receiver(post_save, sender=Article)
def clear_article_cache(sender, instance, **kwargs):
    """Clear related caches when article is saved"""
    cache_keys = [
        f"related_articles_{instance.pk}_*",
        f"category_article_count_*",
    ]
    # Clear relevant cache keys
    cache.delete_many(cache_keys)


@receiver(post_delete, sender=Article)
def delete_article_files(sender, instance, **kwargs):
    """Delete associated files when article is deleted"""
    if instance.featured_image:
        if os.path.isfile(instance.featured_image.path):
            os.remove(instance.featured_image.path)
    
    if instance.thumbnail:
        if os.path.isfile(instance.thumbnail.path):
            os.remove(instance.thumbnail.path)