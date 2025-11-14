from django.urls import path
from . import views

urlpatterns = [
    path('', views.stage_list, name='stage_list'),
    path('create/', views.stage_create, name='stage_form'),
    path('<int:id_stage>/', views.stage_detail, name='stage_detail'),
    path('<int:id_stage>/update/', views.stage_update, name='stage_edit'),  # Fixed: was stage_update
    path('<int:id_stage>/delete/', views.stage_delete, name='stage_delete'),
   

]