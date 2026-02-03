from django.urls import path

from . import views

urlpatterns = [
    path('notifications/', views.inbox, name='notifications_inbox'),
    path('notifications/read/<int:pk>/', views.mark_read, name='notifications_read'),
    path('notifications/read-all/', views.mark_all_read, name='notifications_read_all'),
]
