from django.urls import path

from . import views

urlpatterns = [
    path('staff/analytics/', views.dashboard, name='analytics_dashboard'),
]
