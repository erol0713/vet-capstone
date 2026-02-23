from django.urls import path

from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('verify-email/', views.verify_email, name='verify_email'),
    path('verification/', views.verification_status, name='verification_status'),
    path('verification/face/', views.submit_face_verification, name='face_verification'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('staff/verification/<int:pk>/', views.verification_detail, name='verification_detail'),
    path('admin/users/', views.admin_user_management, name='admin_user_management'),
    path('admin/users/action/', views.admin_user_management_action, name='admin_user_management_action'),
]
