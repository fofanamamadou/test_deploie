from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import Influenceur
from .serializers import InfluenceurSerializer
from .permissions import IsInfluenceurOrAdmin, IsOwnerOrAdmin
import json
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([AllowAny])
def admin_login_view(request):
    """
    Vue de connexion spécifique pour les administrateurs (superusers)
    """
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return Response({
                'error': 'Email et mot de passe requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Authentifier comme superuser Django
        user = authenticate(username=email, password=password)
        
        if user and user.is_superuser:
            # Générer les tokens JWT
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
            
            response_data = {
                'success': True,
                'message': 'Connexion administrateur réussie',
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user_type': 'admin',
                'permissions': {
                    'is_admin': True,
                    'is_moderateur': False,
                    'peut_creer_influenceurs': True,
                    'peut_valider_prospects': True,
                    'peut_payer_remises': True,
                    'peut_voir_statistiques': True,
                    'peut_gerer_systeme': True
                },
                'token_type': 'Bearer',
                'expires_in': 86400,  # 24 heures en secondes
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_superuser': True
                }
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            # Essayer avec l'email si l'authentification par username a échoué
            try:
                superuser = User.objects.get(email=email, is_superuser=True)
                user = authenticate(username=superuser.username, password=password)
                
                if user and user.is_superuser:
                    # Générer les tokens JWT
                    refresh = RefreshToken.for_user(user)
                    access_token = str(refresh.access_token)
                    refresh_token = str(refresh)
                    
                    response_data = {
                        'success': True,
                        'message': 'Connexion administrateur réussie',
                        'access_token': access_token,
                        'refresh_token': refresh_token,
                        'user_type': 'admin',
                        'permissions': {
                            'is_admin': True,
                            'is_moderateur': False,
                            'peut_creer_influenceurs': True,
                            'peut_valider_prospects': True,
                            'peut_payer_remises': True,
                            'peut_voir_statistiques': True,
                            'peut_gerer_systeme': True
                        },
                        'token_type': 'Bearer',
                        'expires_in': 86400,
                        'user': {
                            'id': user.id,
                            'username': user.username,
                            'email': user.email,
                            'first_name': user.first_name,
                            'last_name': user.last_name,
                            'is_superuser': True
                        }
                    }
                    
                    return Response(response_data, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                pass
            
            return Response({
                'error': 'Email ou mot de passe incorrect pour l\'administrateur'
            }, status=status.HTTP_401_UNAUTHORIZED)
            
    except json.JSONDecodeError:
        return Response({
            'error': 'Données JSON invalides'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Erreur lors de la connexion admin: {str(e)}")
        return Response({
            'error': 'Erreur lors de la connexion'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def influenceur_login_view(request):
    """
    Vue de connexion spécifique pour les influenceurs
    """
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return Response({
                'error': 'Email et mot de passe requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Vérifier si l'influenceur existe
        try:
            influenceur = Influenceur.objects.get(email=email)
        except Influenceur.DoesNotExist:
            return Response({
                'error': 'Email ou mot de passe incorrect'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Vérifier si le compte peut se connecter
        can_login, message = influenceur.can_login()
        if not can_login:
            influenceur.increment_login_attempts()
            return Response({
                'error': message
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Vérifier le mot de passe
        if not influenceur.check_password(password):
            influenceur.increment_login_attempts()
            return Response({
                'error': 'Email ou mot de passe incorrect'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Créer ou récupérer l'utilisateur Django pour les tokens JWT
        # Utiliser l'email comme username pour éviter les conflits
        user, created = User.objects.get_or_create(
            username=influenceur.email,
            defaults={
                'email': influenceur.email,
                'first_name': influenceur.nom.split()[0] if influenceur.nom else '',
                'last_name': ' '.join(influenceur.nom.split()[1:]) if len(influenceur.nom.split()) > 1 else '',
                'is_active': influenceur.is_active,
                'password': '!'  # Mot de passe factice car on utilise l'influenceur pour l'auth
            }
        )
        
        # Mettre à jour les informations utilisateur si nécessaire
        if not created:
            user.first_name = influenceur.nom.split()[0] if influenceur.nom else ''
            user.last_name = ' '.join(influenceur.nom.split()[1:]) if len(influenceur.nom.split()) > 1 else ''
            user.is_active = influenceur.is_active
            user.save()
        
        # Générer les tokens JWT
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        # Mettre à jour la dernière connexion
        influenceur.update_last_login()
        
        # Sérialiser les données de l'influenceur
        serializer = InfluenceurSerializer(influenceur)
        
        response_data = {
            'success': True,
            'message': 'Connexion influenceur réussie',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user_type': 'influenceur',
            'permissions': influenceur.get_all_permissions(),
            'token_type': 'Bearer',
            'expires_in': 86400,  # 24 heures en secondes
            'influenceur': serializer.data
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
            
    except json.JSONDecodeError:
        return Response({
            'error': 'Données JSON invalides'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Erreur lors de la connexion influenceur: {str(e)}")
        return Response({
            'error': 'Erreur lors de la connexion'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token_view(request):
    """
    Vue pour rafraîchir un token JWT
    """
    try:
        data = json.loads(request.body)
        refresh_token = data.get('refresh_token')
        
        if not refresh_token:
            return Response({
                'error': 'Refresh token requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Rafraîchir le token
        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)
            
            return Response({
                'success': True,
                'access_token': access_token,
                'refresh_token': str(refresh),
                'token_type': 'Bearer',
                'expires_in': 86400
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Erreur lors du refresh token: {str(e)}")
            return Response({
                'error': 'Token de rafraîchissement invalide'
            }, status=status.HTTP_401_UNAUTHORIZED)
            
    except json.JSONDecodeError:
        return Response({
            'error': 'Données JSON invalides'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Erreur lors du refresh token: {str(e)}")
        return Response({
            'error': 'Erreur lors du rafraîchissement du token'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    Vue de déconnexion
    """
    try:
        data = json.loads(request.body)
        refresh_token = data.get('refresh_token')
        
        if not refresh_token:
            return Response({
                'error': 'Refresh token requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Déconnecter en blacklistant le token
        try:
            refresh = RefreshToken(refresh_token)
            refresh.blacklist()
            
            return Response({
                'success': True,
                'message': 'Déconnexion réussie'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Erreur lors de la déconnexion: {str(e)}")
            return Response({
                'error': 'Token invalide'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except json.JSONDecodeError:
        return Response({
            'error': 'Données JSON invalides'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Erreur lors de la déconnexion: {str(e)}")
        return Response({
            'error': 'Erreur lors de la déconnexion'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_view(request):
    """
    Vue pour récupérer le profil de l'utilisateur connecté
    """
    try:
        # Récupérer l'utilisateur depuis le token JWT
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            
            # Décoder le token pour récupérer l'utilisateur
            from rest_framework_simplejwt.tokens import AccessToken
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            
            user = User.objects.get(id=user_id)
            
            # Vérifier si c'est un superuser
            if user.is_superuser:
                response_data = {
                    'user_type': 'admin',
                    'permissions': {
                        'is_admin': True,
                        'is_moderateur': False,
                        'peut_creer_influenceurs': True,
                        'peut_valider_prospects': True,
                        'peut_payer_remises': True,
                        'peut_voir_statistiques': True,
                        'peut_gerer_systeme': True
                    },
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'is_superuser': True,
                        'date_joined': user.date_joined,
                        'last_login': user.last_login
                    }
                }
            else:
                # C'est un influenceur
                try:
                    influenceur = Influenceur.objects.get(email=user.email)
                    serializer = InfluenceurSerializer(influenceur)
                    
                    response_data = {
                        'user_type': 'influenceur',
                        'permissions': influenceur.get_all_permissions(),
                        'influenceur': serializer.data,
                        'last_login': influenceur.date_derniere_connexion,
                        'account_status': {
                            'is_active': influenceur.is_active,
                            'is_locked': influenceur.is_locked(),
                            'login_attempts': influenceur.nombre_tentatives_connexion
                        }
                    }
                except Influenceur.DoesNotExist:
                    return Response({
                        'error': 'Influenceur non trouvé'
                    }, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({
                'error': 'Token d\'authentification requis'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du profil: {str(e)}")
        return Response({
            'error': 'Erreur lors de la récupération du profil'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """
    Vue d'inscription pour les nouveaux influenceurs
    """
    try:
        data = json.loads(request.body)
        nom = data.get('nom')
        email = data.get('email')
        password = data.get('password')
        telephone = data.get('telephone', '')  # Optionnel
        
        if not nom or not email or not password:
            return Response({
                'error': 'Nom, email et mot de passe requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Vérifier si l'email existe déjà
        if Influenceur.objects.filter(email=email).exists():
            return Response({
                'error': 'Un influenceur avec cet email existe déjà'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Créer le nouvel influenceur avec mot de passe hashé
        influenceur = Influenceur.create_influenceur(
            nom=nom,
            email=email,
            telephone=telephone,
            password=password,  # Sera hashé automatiquement
            role='influenceur'  # Par défaut
        )
        
        # Créer l'utilisateur Django pour les tokens JWT
        # Utiliser l'email comme username pour éviter les conflits
        user, created = User.objects.get_or_create(
            username=influenceur.email,
            defaults={
                'email': influenceur.email,
                'first_name': influenceur.nom.split()[0] if influenceur.nom else '',
                'last_name': ' '.join(influenceur.nom.split()[1:]) if len(influenceur.nom.split()) > 1 else '',
                'is_active': influenceur.is_active,
                'password': '!'  # Mot de passe factice car on utilise l'influenceur pour l'auth
            }
        )
        
        # Générer les tokens JWT
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        # Sérialiser les données de l'influenceur
        serializer = InfluenceurSerializer(influenceur)
        
        return Response({
            'success': True,
            'message': 'Inscription réussie',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'influenceur': serializer.data,
            'permissions': influenceur.get_all_permissions(),
            'token_type': 'Bearer',
            'expires_in': 86400
        }, status=status.HTTP_201_CREATED)
            
    except json.JSONDecodeError:
        return Response({
            'error': 'Données JSON invalides'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Erreur lors de l'inscription: {str(e)}")
        return Response({
            'error': 'Erreur lors de l\'inscription'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password_view(request):
    """
    Vue pour changer le mot de passe
    """
    try:
        data = json.loads(request.body)
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return Response({
                'error': 'Ancien et nouveau mot de passe requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Récupérer l'utilisateur depuis le token
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            
            # Décoder le token pour récupérer l'utilisateur
            from rest_framework_simplejwt.tokens import AccessToken
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            
            user = User.objects.get(id=user_id)
            
            # Changer le mot de passe du superuser
            if user.is_superuser:
                if not user.check_password(current_password):
                    return Response({
                        'error': 'Ancien mot de passe incorrect'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                user.set_password(new_password)
                user.save()
            else:
                # Changer le mot de passe de l'influenceur
                try:
                    influenceur = Influenceur.objects.get(email=user.email)
                    if not influenceur.check_password(current_password):
                        return Response({
                            'error': 'Ancien mot de passe incorrect'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    influenceur.set_password(new_password)
                except Influenceur.DoesNotExist:
                    return Response({
                        'error': 'Influenceur non trouvé'
                    }, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({
                'error': 'Token d\'authentification requis'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response({
            'success': True,
            'message': 'Mot de passe modifié avec succès'
        }, status=status.HTTP_200_OK)
        
    except json.JSONDecodeError:
        return Response({
            'error': 'Données JSON invalides'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Erreur lors du changement de mot de passe: {str(e)}")
        return Response({
            'error': 'Erreur lors du changement de mot de passe'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
