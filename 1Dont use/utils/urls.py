from django.urls import path
from . import views

app_name = 'account'

urlpatterns = [
    # Authentication URLs
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    
    # Profile URLs
    path('profile/', views.ProfileView.as_view(), name='profile'),
    
    # Password Management URLs
    path('password/change/', views.PasswordChangeView.as_view(), name='password_change'),
    path('password/reset/', views.PasswordResetView.as_view(), name='password_reset'),
    path('password/reset/<str:token>/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    # Email Verification URL
    path('verify-email/<str:code>/', views.EmailVerificationView.as_view(), name='verify_email'),
    
    # Social Links API URLs
    path('api/social-links/', views.SocialLinksView.as_view(), name='social_links'),
]   