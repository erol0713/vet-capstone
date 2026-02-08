from django.urls import path

from . import views

urlpatterns = [
    path('api/reports', views.api_reports, name='api_reports'),
    path('api/reports/', views.api_reports),
    path('reports/public/', views.public_report, name='reports_public'),
    path('reports/', views.public_list, name='reports_public_list'),
    path('reports/<int:pk>/delete/', views.public_delete, name='reports_public_delete'),
    path('staff/reports/', views.staff_list, name='reports_staff_list'),
    path('staff/reports/<int:pk>/', views.staff_detail, name='reports_staff_detail'),
    path('staff/reports/<int:pk>/status/', views.update_status, name='reports_update_status'),
]
