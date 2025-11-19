from django.urls import path
from .views import *

urlpatterns = [
    #----------------formation urls----------------
    path('view_formation',FormationListView.as_view(), name='view_formation'),
    path('formation_admin',FormationList.as_view(), name='formation_admin'),
    path('formationcreate/',FormationCreateView.as_view(),name='formation_create'),
    path('delete/<int:pk>/',FormationDeleteView.as_view(),name='formation_delete'),
    path('update/<int:pk>/',FormationUpdateView.as_view(),name='formation_update'),
    #----------------lessons urls----------------
    path('formationsde/<int:id_formation>/', FormationDetailView.as_view(), name='formation_detail'),
    path('formationsdet/<int:id_formation>/', FormationDetail.as_view(), name='formation_detail_admin'),
    path('lesson/<int:id_formation>/create/', LessonCreateView.as_view(), name='lesson_create'),
    path('lessonup/<int:id_formation>/update/<int:id_lesson>/', LessonUpdateView.as_view(), name='lesson_update'),
    path('lessondel/<int:id_formation>/delete/<int:id_lesson>/', LessonDeleteView.as_view(), name='lesson_delete'),

    ]