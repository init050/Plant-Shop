'''
URL configuration for Plant_Shop project.
'''
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home_module.urls')),
    path('user/', include('account_module.urls')),
    path('articles/', include('article_module.urls')),
    path('chat/', include('chat_module.urls')),
    path('products/', include('product_module.urls')),
]

# Critical: Serve static files in development mode
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)