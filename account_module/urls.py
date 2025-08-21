from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

app_name = 'account_module'

urlpatterns = [
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='account_module:login'), name='logout'),    
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('change-password/', views.PasswordChangeView.as_view(), name='change_password'),
    
    path('email-verification/', views.EmailVerificationView.as_view(), name='email_verification'),
    path('verify-email/<str:token>/', views.EmailVerificationConfirmView.as_view(), name='verify_email'),

    # Email change URLs
    path('change-email/', views.EmailChangeInitiateView.as_view(), name='email_change_initiate'),
    path('change-email/verify-old/', views.EmailChangeVerifyOldView.as_view(), name='email_change_verify_old'),
    path('change-email/verify-new/', views.EmailChangeVerifyNewView.as_view(), name='email_change_verify_new'),

    path('password_reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', views.CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
]