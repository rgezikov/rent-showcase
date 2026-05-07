from django.urls import path
from . import views

app_name = 'listings'

urlpatterns = [
    path('', views.listing_list, name='list'),
    path('create/', views.listing_create, name='create'),
    path('mine/', views.my_listings, name='my_listings'),
    path('<int:pk>/', views.listing_detail, name='detail'),
    path('<int:pk>/edit/', views.listing_edit, name='edit'),
    path('<int:pk>/delete/', views.listing_delete, name='delete'),
    path('<int:pk>/toggle/', views.listing_toggle_active, name='toggle_active'),
    path('<int:pk>/blocked/add/', views.blocked_date_add, name='blocked_date_add'),
    path('blocked/<int:pk>/delete/', views.blocked_date_delete, name='blocked_date_delete'),
    path('photo/<int:pk>/delete/', views.photo_delete, name='photo_delete'),
]
