from django.urls import path
from . import views

app_name = 'article_module'

urlpatterns = [
    path('', views.ArticleListView.as_view(), name='list'),
    path('search/', views.article_search, name='search'),
    path('create/', views.ArticleCreateView.as_view(), name='create'),
    path('my-articles/', views.MyArticlesView.as_view(), name='my_articles'),
    path('<slug:slug>/', views.ArticleDetailView.as_view(), name='detail'),
    path('<slug:slug>/edit/', views.ArticleUpdateView.as_view(), name='update'),
    path('<slug:article_slug>/comment/', views.add_comment, name='add_comment'),
]