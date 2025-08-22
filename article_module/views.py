from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from account_module.utils.ip_retriever import get_client_ip
from .models import Article, Comment, ArticleView
from .forms import ArticleForm, CommentForm, ArticleSearchForm


class ArticleListView(ListView):
    model = Article
    template_name = 'article_module/article_list.html'
    context_object_name = 'articles'
    paginate_by = 9
    
    def get_queryset(self):
        queryset = Article.objects.published().select_related('author')
        
        query = self.request.GET.get('query')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(content__icontains=query) |
                Q(summary__icontains=query)
            )
        
        return queryset.order_by('-publish_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = ArticleSearchForm(self.request.GET)
        context['query'] = self.request.GET.get('query', '')
        return context


class ArticleDetailView(DetailView):
    model = Article
    template_name = 'article_module/article_detail.html'
    context_object_name = 'article'
    
    def get_queryset(self):
        return Article.objects.published().select_related('author')
    
    def get_object(self, queryset=None):
        article = super().get_object(queryset)
        
        # Track article view - unique per IP address
        ip_address = get_client_ip(self.request)
        view, created = ArticleView.objects.get_or_create(
            article=article,
            ip_address=ip_address,
            defaults={'user': self.request.user if self.request.user.is_authenticated else None}
        )
        
        if created:
            Article.objects.filter(pk=article.pk).update(view_count=article.view_count + 1)
        
        return article
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        article = self.get_object()
        
        # Get approved comments with replies
        comments = Comment.objects.filter(
            article=article,
            is_approved=True,
            parent=None
        ).select_related('author').prefetch_related('replies__author').order_by('-created_at')
        
        context['comments'] = comments
        context['comment_form'] = CommentForm()
        
        # Get related articles
        context['related_articles'] = Article.objects.published().exclude(
            pk=article.pk
        ).order_by('-publish_date')[:3]
        
        return context


class ArticleCreateView(LoginRequiredMixin, CreateView):
    model = Article
    form_class = ArticleForm
    template_name = 'article_module/article_create.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not Article.can_user_create_article(request.user):
            messages.error(
                request,
                _('You can only create one article per 24 hours. Please try again later.')
            )
            return redirect('article_module:my_articles')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_create'] = Article.can_user_create_article(self.request.user)
        return context
    
    def form_valid(self, form):
        article = form.save(commit=False)
        article.author = self.request.user
        
        # Auto-publish for staff/admin, otherwise set to pending
        if self.request.user.is_staff or self.request.user.is_superuser:
            article.status = Article.PUBLISHED
            success_message = _('Article published successfully!')
        else:
            article.status = Article.PENDING
            success_message = _('Article submitted for review. It will be published after admin approval.')
        
        article.save()
        messages.success(self.request, success_message)
        return redirect('article_module:my_articles')


class ArticleUpdateView(LoginRequiredMixin, UpdateView):
    model = Article
    form_class = ArticleForm
    template_name = 'article_module/article_update.html'
    
    def get_queryset(self):
        # Users can only edit their own articles
        return Article.objects.filter(author=self.request.user)
    
    def form_valid(self, form):
        article = form.save(commit=False)
        
        # Reset to pending if user is not staff and article was rejected
        if not (self.request.user.is_staff or self.request.user.is_superuser):
            if article.status == Article.REJECTED:
                article.status = Article.PENDING
                article.rejection_reason = ''
        
        article.save()
        messages.success(self.request, _('Article updated successfully!'))
        return redirect('article_module:my_articles')


class MyArticlesView(LoginRequiredMixin, ListView):
    model = Article
    template_name = 'article_module/my_articles.html'
    context_object_name = 'articles'
    paginate_by = 10
    
    def get_queryset(self):
        return Article.objects.filter(
            author=self.request.user
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_create'] = Article.can_user_create_article(self.request.user)
        return context


@login_required
def add_comment(request, article_slug):
    if request.method == 'POST':
        article = get_object_or_404(Article, slug=article_slug, status=Article.PUBLISHED)
        form = CommentForm(request.POST)
        
        if form.is_valid():
            comment = form.save(commit=False)
            comment.article = article
            comment.author = request.user
            
            # Handle reply to another comment
            parent_id = request.POST.get('parent_id')
            if parent_id:
                try:
                    parent_comment = Comment.objects.get(
                        id=parent_id,
                        article=article,
                        is_approved=True
                    )
                    comment.parent = parent_comment
                except Comment.DoesNotExist:
                    pass
            
            comment.save()
            messages.success(request, _('Comment added successfully!'))
        else:
            messages.error(request, _('Please check your comment and try again.'))
    
    return redirect('article_module:detail', slug=article_slug)


def article_search(request):
    form = ArticleSearchForm(request.GET)
    articles = []
    query = ''
    
    if form.is_valid():
        query = form.cleaned_data.get('query')
        if query:
            articles = Article.objects.published().filter(
                Q(title__icontains=query) |
                Q(content__icontains=query) |
                Q(summary__icontains=query)
            ).select_related('author').order_by('-publish_date')
    
    paginator = Paginator(articles, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'articles': page_obj,
        'search_form': form,
        'query': query,
        'page_obj': page_obj,
    }
    
    return render(request, 'article_module/article_search.html', context)