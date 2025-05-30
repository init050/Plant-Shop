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

def upload_article_image(instance, filename):
    ext = filename.split('.')[-1]
    filename = f'{uuid4().hex}.{ext}'
    return f'articles/{instance.slug}/{filename}'


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
        help_text=_()
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
    title = models.CharField(max_length=100)


