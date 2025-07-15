from django.urls import path
from .auth_views import (admin_login_view, influenceur_login_view, logout_view, profile_view, register_view, change_password_view,
                        refresh_token_view)
from .views import (influenceur_view, influenceur_detail_view,
                    influenceur_dashboard_view, influenceur_prospects_view, 
                    influenceur_remises_view, dashboard_global_admin_view)

urlpatterns = [
    # URLs d'authentification JWT
    path('auth/admin/login/', admin_login_view, name='admin_login'),
    path('auth/influenceur/login/', influenceur_login_view, name='influenceur_login'),
    path('auth/logout/', logout_view, name='auth_logout'),
    path('auth/refresh/', refresh_token_view, name='auth_refresh'),
    path('auth/profile/', profile_view, name='auth_profile'),
    path('auth/register/', register_view, name='auth_register'),
    path('auth/change-password/', change_password_view, name='auth_change_password'),

    
    # URLs des influenceurs (CRUD) - RESTful complet
    path('influenceurs/', influenceur_view, name='influenceur_view'),  # GET (liste), POST (création)
    path('influenceurs/<int:pk>/', influenceur_detail_view, name='influenceur_detail'),  # GET, PUT, PATCH, DELETE
    path('influenceurs/<int:pk>/dashboard/', influenceur_dashboard_view, name='influenceur_dashboard'),
    path('influenceurs/<int:pk>/prospects/', influenceur_prospects_view, name='influenceur_prospects'),
    path('influenceurs/<int:pk>/remises/', influenceur_remises_view, name='influenceur_remises'),
    path('dashboard-global/', dashboard_global_admin_view, name='dashboard_global_admin'),
]

