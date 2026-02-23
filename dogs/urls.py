from django.urls import path

from . import staff_views, views

urlpatterns = [
    path('dogs/', views.public_list, name='dogs_public_list'),
    path('dogs/<int:pk>/', views.public_detail, name='dogs_public_detail'),
    path('dogs/register/', views.register_dog, name='dogs_register'),
    path('dogs/my-dogs/', views.my_dogs, name='dogs_my_dogs'),
    path('dogs/my-dogs/<int:pk>/', views.owner_detail, name='dogs_owner_detail'),
    path('dogs/my-dogs/<int:pk>/edit/', views.owner_edit, name='dogs_owner_edit'),
    path(
        'dogs/my-dogs/<int:pk>/request-vaccination/',
        views.request_vaccination_schedule,
        name='dogs_request_vaccination_schedule',
    ),
    path('dogs/<int:pk>/delete/', views.delete_registered_dog, name='dogs_delete'),
    path('staff/dogs/', staff_views.manage_list, name='dogs_manage_list'),
    path('staff/dogs/registered/', staff_views.registered_by_owner, name='dogs_registered_by_owner'),
    path(
        'staff/dogs/registered/<int:pk>/',
        staff_views.registered_detail,
        name='dogs_registered_detail',
    ),
    path(
        'staff/dogs/vaccinations/',
        staff_views.vaccination_requests,
        name='dogs_vaccination_requests',
    ),
    path(
        'staff/dogs/<int:pk>/schedule/',
        staff_views.schedule_vaccination,
        name='dogs_schedule_vaccination',
    ),
    path(
        'staff/dogs/<int:pk>/vaccination-record/',
        staff_views.record_vaccination,
        name='dogs_record_vaccination',
    ),
    path('staff/dogs/new/', staff_views.create_dog, name='dogs_create'),
    path('staff/dogs/<int:pk>/edit/', staff_views.edit_dog, name='dogs_edit'),
    path('staff/dogs/<int:pk>/delete/', staff_views.delete_dog, name='dogs_delete_staff'),
]
