from django.urls import path

from . import views

urlpatterns = [
    path('staff/penalties/checklist/', views.checklist, name='penalties_checklist'),
    path('staff/penalties/receipt/<int:case_id>/', views.receipt, name='penalties_receipt'),
]
