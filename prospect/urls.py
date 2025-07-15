from django.urls import path
from .views import prospect_view, prospect_detail_view, prospect_valider_view, prospect_rejeter_view, prospects_sans_remise_view, prospects_statistiques_view, affiliation_form_view

urlpatterns = [
    path('prospects/', prospect_view, name='prospect_view'),  # GET (liste)
    path('prospects/<int:pk>/', prospect_detail_view, name='prospect_detail'),  # GET
    path('prospects/<int:pk>/valider/', prospect_valider_view, name='prospect_valider'),
    path('prospects/<int:pk>/rejeter/', prospect_rejeter_view, name='prospect_rejeter'),
    path('prospects/sans-remise/', prospects_sans_remise_view, name='prospects_sans_remise'),
    path('prospects/statistiques/', prospects_statistiques_view, name='prospects_statistiques'),
    path('affiliation/<str:code_affiliation>/', affiliation_form_view, name='affiliation_form'),
]