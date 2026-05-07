from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_list, name='list'),
    path('<int:pk>/goto/', views.notification_goto, name='goto'),
    path('mark-all-read/', views.notification_mark_all_read, name='mark_all_read'),
]
