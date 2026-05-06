from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.EmailLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('verify-email/sent/', views.verify_email_sent, name='verify_email_sent'),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('profile/<int:pk>/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('delete/', views.account_delete, name='account_delete'),
]
