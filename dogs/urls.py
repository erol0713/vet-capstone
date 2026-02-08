from django.urls import path

from . import views

urlpatterns = [
    path('dogs/', views.public_list, name='dogs_public_list'),
    path('dogs/<int:pk>/', views.public_detail, name='dogs_public_detail'),
    path('dogs/register/', views.register_dog, name='dogs_register'),
    path('dogs/<int:pk>/delete/', views.delete_registered_dog, name='dogs_delete'),
    path('staff/dogs/', views.manage_list, name='dogs_manage_list'),
    path('staff/dogs/registered/', views.registered_by_owner, name='dogs_registered_by_owner'),
    path(
        'staff/dogs/registered/<int:pk>/',
        views.registered_detail,
        name='dogs_registered_detail',
    ),
    path('staff/dogs/vaccinations/', views.vaccination_requests, name='dogs_vaccination_requests'),
    path(
        'staff/dogs/<int:pk>/schedule/',
        views.schedule_vaccination,
        name='dogs_schedule_vaccination',
    ),
    path('staff/dogs/new/', views.create_dog, name='dogs_create'),
    path('staff/dogs/<int:pk>/edit/', views.edit_dog, name='dogs_edit'),
    path('staff/dogs/<int:pk>/delete/', views.delete_dog, name='dogs_delete_staff'),
]
