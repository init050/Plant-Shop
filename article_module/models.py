from django.db import models
from uuid import uuid4
from django.utils import timezone
from mptt.models import MPTTModel, TreeForeignKey



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
    pass