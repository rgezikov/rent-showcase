from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('<int:booking_pk>/send/', views.send_message, name='send'),
]
