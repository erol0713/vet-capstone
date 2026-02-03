from django.urls import path

from . import views

urlpatterns = [
    path('adoption/dogs/<int:dog_id>/reserve/', views.reserve_adoption, name='adoption_reserve'),
    path('adoption/dogs/<int:dog_id>/reclaim/', views.request_reclaim, name='adoption_reclaim'),
    path('adoption/my/', views.my_requests, name='adoption_my_requests'),
    path('staff/adoption/queue/', views.staff_queue, name='adoption_staff_queue'),
    path(
        'staff/adoption/<int:pk>/status/<str:status>/',
        views.update_adoption_status,
        name='adoption_update_status',
    ),
    path(
        'staff/reclaim/<int:pk>/status/<str:status>/',
        views.update_reclaim_status,
        name='reclaim_update_status',
    ),
]
