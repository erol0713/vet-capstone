from django.urls import path

from . import views

urlpatterns = [
    path('reports/public/', views.public_report, name='reports_public'),
    path('reports/', views.public_list, name='reports_public_list'),
    path('staff/reports/', views.staff_list, name='reports_staff_list'),
    path('staff/reports/<int:pk>/', views.staff_detail, name='reports_staff_detail'),
    path('staff/reports/<int:pk>/status/', views.update_status, name='reports_update_status'),
]
