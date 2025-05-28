from django.db import models
from uuid import uuid4
from django.utils import timezone
from mptt.models import MPTTModel, TreeForeignKey
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.utils.translation import gettext_lazy as _



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