from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Article, Comment, ArticleView


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'author', 'status', 'get_image', 
        'view_count', 'publish_date', 'created_at'
    ]
    list_filter = ['status', 'publish_date', 'created_at', 'author']
    search_fields = ['title', 'content', 'author__email', 'author__username']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['view_count', 'created_at', 'updated_at']
    date_hierarchy = 'publish_date'
    
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'summary', 'content', 'image')
        }),
        (_('Publication'), {
            'fields': ('author', 'status', 'publish_date')
        }),
        (_('Moderation'), {
            'fields': ('rejection_reason',),
            'classes': ('collapse',)
        }),
        (_('Statistics'), {
            'fields': ('view_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['approve_articles', 'reject_articles', 'publish_articles']
    
    def get_image(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 4px;" />',
                obj.image.url
            )
        return '❌'
    get_image.short_description = _('Image')
    
    def approve_articles(self, request, queryset):
        updated = queryset.filter(status=Article.PENDING).update(status=Article.PUBLISHED)
        self.message_user(request, f'{updated} articles approved and published.')
    approve_articles.short_description = _('Approve and publish selected articles')
    
    def reject_articles(self, request, queryset):
        updated = queryset.filter(status=Article.PENDING).update(status=Article.REJECTED)
        self.message_user(request, f'{updated} articles rejected.')
    reject_articles.short_description = _('Reject selected articles')
    
    def publish_articles(self, request, queryset):
        updated = queryset.update(status=Article.PUBLISHED)
        self.message_user(request, f'{updated} articles published.')
    publish_articles.short_description = _('Publish selected articles')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['get_comment_preview', 'author', 'article', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'created_at', 'article']
    search_fields = ['content', 'author__email', 'author__username', 'article__title']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('article', 'author', 'parent', 'content')
        }),
        (_('Moderation'), {
            'fields': ('is_approved',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['approve_comments', 'disapprove_comments']
    
    def get_comment_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    get_comment_preview.short_description = _('Comment')
    
    def approve_comments(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} comments approved.')
    approve_comments.short_description = _('Approve selected comments')
    
    def disapprove_comments(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} comments disapproved.')
    disapprove_comments.short_description = _('Disapprove selected comments')


@admin.register(ArticleView)
class ArticleViewAdmin(admin.ModelAdmin):
    list_display = ['article', 'ip_address', 'user', 'viewed_at']
    list_filter = ['viewed_at', 'article']
    search_fields = ['article__title', 'ip_address', 'user__email']
    readonly_fields = ['article', 'ip_address', 'user', 'viewed_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False