from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('', views.my_bookings, name='my_bookings'),
    path('requests/', views.booking_requests, name='requests'),
    path('create/<int:listing_pk>/', views.booking_create, name='create'),
    path('<int:pk>/', views.booking_detail, name='detail'),
    path('<int:pk>/confirm/', views.booking_confirm, name='confirm'),
    path('<int:pk>/reject/', views.booking_reject, name='reject'),
    path('<int:pk>/cancel/', views.booking_cancel, name='cancel'),
]
