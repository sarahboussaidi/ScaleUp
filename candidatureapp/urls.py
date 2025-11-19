from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('list/', views.liste_candidatures, name='liste_candidatures'),

    # Création d'une nouvelle candidature (pas d'ID)
    path('form/', views.form_candidature, name='ajouter_candidature'),

    # Modification d'une candidature existante (avec ID)
    path('form/<int:id>/', views.form_candidature, name='form_candidature'),

    # Suppression
    path('delete/<int:id>/', views.supprimer_candidature, name='supprimer_candidature'),

    # Authentification
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
]

# Gestion des CV en mode DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.CVS_URL, document_root=settings.CVS_ROOT)
