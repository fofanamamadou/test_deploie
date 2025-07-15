from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Influenceur
from .serializers import InfluenceurSerializer, InfluenceurUpdateSerializer, InfluenceurCreateSerializer
from .permissions import IsInfluenceurOrAdmin
from .email_service import EmailService
from prospect.models import Prospect
from prospect.serializers import ProspectSerializers
from remise.models import Remise
from remise.serializers import RemiseSerializers
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
import json

def get_influenceur_from_user(user):
    """Récupère l'influenceur correspondant à un utilisateur Django"""
    try:
        return Influenceur.objects.get(email=user.email)
    except Influenceur.DoesNotExist:
        return None

@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def influenceur_view(request):
    """
    Vue API pour lister tous les influenceurs (GET) ou en créer un (POST).
    Seuls les admins peuvent accéder à cette vue.
    """
    if request.method == 'GET':
        influenceurs = Influenceur.objects.all()
        serializer = InfluenceurSerializer(influenceurs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    elif request.method == 'POST':
        # Récupérer les données
        nom = request.data.get('nom')
        email = request.data.get('email')
        password = request.data.get('password')
        telephone = request.data.get('telephone', '')
        role = request.data.get('role', 'influenceur')
        
        # Validation des champs requis
        if not nom or not email or not password:
            return Response({
                'error': 'Nom, email et mot de passe sont requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Vérifier si l'email existe déjà
        if Influenceur.objects.filter(email=email).exists():
            return Response({
                'error': 'Un influenceur avec cet email existe déjà'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Créer l'influenceur avec mot de passe hashé
            influenceur = Influenceur.create_influenceur(
                nom=nom,
                email=email,
                telephone=telephone,
                password=password,
                role=role
            )
            
            # Envoi des emails avec le nouveau service
            try:
                # Email d'affiliation avec le lien
                EmailService.send_affiliation_link(influenceur)
                
                # Email de bienvenue
                EmailService.send_welcome_email(influenceur)
                
            except Exception as e:
                print(f"Erreur lors de l'envoi des emails : {e}")
                # On continue même si l'email échoue
            
            # Sérialiser la réponse
            serializer = InfluenceurSerializer(influenceur)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': f'Erreur lors de la création : {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsInfluenceurOrAdmin])
def influenceur_detail_view(request, pk):
    """
    Vue API pour gérer un influenceur (GET, PUT, PATCH, DELETE).
    L'influenceur peut voir/modifier ses propres détails, les admins peuvent voir/modifier/supprimer tous.
    """
    influenceur = get_object_or_404(Influenceur, pk=pk)
    
    # Vérifier les permissions
    current_influenceur = get_influenceur_from_user(request.user)
    if not request.user.is_superuser and current_influenceur and current_influenceur.id != influenceur.id:
        return Response({'error': 'Accès non autorisé'}, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        # Lecture des détails
        serializer = InfluenceurSerializer(influenceur)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif request.method in ['PUT', 'PATCH']:
        # Modification
        # Utiliser le serializer de mise à jour qui limite les champs modifiables
        serializer = InfluenceurUpdateSerializer(influenceur, data=request.data, partial=(request.method == 'PATCH'))
        
        if serializer.is_valid():
            try:
                serializer.save()
                # Retourner les données complètes avec le serializer de lecture
                response_serializer = InfluenceurSerializer(influenceur)
                return Response(response_serializer.data, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({
                    'error': f'Erreur lors de la mise à jour : {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({
                'error': 'Données invalides',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        # Suppression - Seuls les admins peuvent supprimer
        if not request.user.is_superuser:
            return Response({
                'error': 'Seuls les administrateurs peuvent supprimer des influenceurs'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            nom_influenceur = influenceur.nom
            influenceur.delete()
            return Response({
                'success': True,
                'message': f'Influenceur "{nom_influenceur}" supprimé avec succès'
            }, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({
                'error': f'Erreur lors de la suppression : {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsInfluenceurOrAdmin])
def influenceur_dashboard_view(request, pk):
    """
    Vue API pour afficher le tableau de bord d'un influenceur avec toutes les stats nécessaires au frontend.
    """
    

    influenceur = get_object_or_404(Influenceur, pk=pk)
    current_influenceur = get_influenceur_from_user(request.user)
    if not request.user.is_superuser and current_influenceur and current_influenceur.id != influenceur.id:
        return Response({'error': 'Accès non autorisé'}, status=status.HTTP_403_FORBIDDEN)

    # Prospects et remises de l'influenceur
    prospects = Prospect.objects.filter(influenceur=influenceur)
    remises = Remise.objects.filter(influenceur=influenceur)

    # Statistiques globales
    total_prospects = prospects.count()
    total_remises = remises.count()
    total_gains = remises.filter(statut='payee').aggregate(total=Sum('montant'))['total'] or 0
    nb_prospects_confirmes = prospects.filter(statut='confirme').count()
    nb_prospects_rejetes = prospects.filter(statut='rejeter').count()
    nb_prospects_en_attente = prospects.filter(statut='en_attente').count()
    
    # Taux de conversion (confirmés / (confirmés + rejetés))
    prospects_traites = nb_prospects_confirmes + nb_prospects_rejetes
    taux_conversion = round((nb_prospects_confirmes / prospects_traites) * 100, 2) if prospects_traites > 0 else 0

    # Evolution mensuelle (prospects/remises par mois sur 6 derniers mois)
    today = timezone.now().date()
    first_month = (today.replace(day=1) - timezone.timedelta(days=180)).replace(day=1)
    evolution = []
    for i in range(6):
        month = (today.replace(day=1) - timezone.timedelta(days=30*i)).replace(day=1)
        month_str = month.strftime('%b')
        nb_prospects = prospects.filter(date_inscription__year=month.year, date_inscription__month=month.month).count()
        nb_remises = remises.filter(date_creation__year=month.year, date_creation__month=month.month).count()
        evolution.append({"mois": month_str, "prospects": nb_prospects, "remises": nb_remises})
    evolution = list(reversed(evolution))

    # Répartition des remises par statut
    repartition_remises = []
    for statut, _ in Remise.STATUT_CHOICES:
        count = remises.filter(statut=statut).count()
        repartition_remises.append({"statut": statut, "count": count})

    # Prospects récents (10 derniers)
    prospects_recents_qs = prospects.order_by('-date_inscription')[:10]
    prospects_recents = []
    for p in prospects_recents_qs:
        # Trouver la remise associée (si existe)
        montant = p.remise.montant if p.remise else 0
        prospects_recents.append({
            "nom": p.nom,
            "email": p.email,
            "statut": p.statut,
            "montant": montant,
            "date": p.date_inscription.strftime('%Y-%m-%d')
        })

    dashboard_data = {
        "total_prospects": total_prospects,
        "total_remises": total_remises,
        "total_gains": float(total_gains),
        "taux_conversion": taux_conversion,
        "nb_prospects_confirmes": nb_prospects_confirmes,
        "nb_prospects_rejetes": nb_prospects_rejetes,
        "nb_prospects_en_attente": nb_prospects_en_attente,
        "evolution": evolution,
        "repartition_remises": repartition_remises,
        "prospects_recents": prospects_recents
    }
    return Response(dashboard_data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsInfluenceurOrAdmin])
def influenceur_prospects_view(request, pk):
    """
    Vue API pour lister tous les prospects d'un influenceur donné.
    L'influenceur peut voir ses propres prospects, les admins peuvent voir tous.
    """
    influenceur = get_object_or_404(Influenceur, pk=pk)
    
    # Vérifier les permissions
    current_influenceur = get_influenceur_from_user(request.user)
    if not request.user.is_superuser and current_influenceur and current_influenceur.id != influenceur.id:
        return Response({'error': 'Accès non autorisé'}, status=status.HTTP_403_FORBIDDEN)
    
    prospects = Prospect.objects.filter(influenceur=influenceur)
    serializer = ProspectSerializers(prospects, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsInfluenceurOrAdmin])
def influenceur_remises_view(request, pk):
    """
    Vue API pour lister toutes les remises d'un influenceur donné.
    L'influenceur peut voir ses propres remises, les admins peuvent voir tous.
    """
    influenceur = get_object_or_404(Influenceur, pk=pk)
    
    # Vérifier les permissions
    current_influenceur = get_influenceur_from_user(request.user)
    if not request.user.is_superuser and current_influenceur and current_influenceur.id != influenceur.id:
        return Response({'error': 'Accès non autorisé'}, status=status.HTTP_403_FORBIDDEN)
    
    remises = Remise.objects.filter(influenceur=influenceur)
    serializer = RemiseSerializers(remises, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def dashboard_global_admin_view(request):
    """
    Vue API pour le dashboard global admin (statistiques générales)
    """
    # Statistiques globales
    total_influenceurs = Influenceur.objects.count()
    total_prospects = Prospect.objects.count()
    prospects_en_attente = Prospect.objects.filter(statut='en_attente').count()
    prospects_confirmes = Prospect.objects.filter(statut='confirme').count()
    prospects_rejetes = Prospect.objects.filter(statut='rejeter').count()
    total_primes = Remise.objects.count()
    primes_payees = Remise.objects.filter(statut='payee').count()
    primes_en_attente = Remise.objects.filter(statut='en_attente').count()
    
    # Calculer le taux de conversion global
    prospects_traites_global = prospects_confirmes + prospects_rejetes
    taux_conversion_global = round((prospects_confirmes / prospects_traites_global) * 100, 2) if prospects_traites_global > 0 else 0
    
    # Calculer le montant total des gains
    total_gains_global = Remise.objects.filter(statut='payee').aggregate(total=Sum('montant'))['total'] or 0
    total_gains_en_attente = Remise.objects.filter(statut='en_attente').aggregate(total=Sum('montant'))['total'] or 0

    # Top influenceurs (par nombre de prospects)
    top_influenceurs_qs = Influenceur.objects.annotate(
        nb_prospects=Count('prospects'),
        nb_prospects_confirmes=Count('prospects', filter=Q(prospects__statut='confirme')),
        nb_prospects_rejetes=Count('prospects', filter=Q(prospects__statut='rejeter')),
        nb_prospects_en_attente=Count('prospects', filter=Q(prospects__statut='en_attente'))
    ).order_by('-nb_prospects')[:5]
    
    top_influenceurs = []
    for i in top_influenceurs_qs:
        # Calculer le taux de conversion
        prospects_traites = i.nb_prospects_confirmes + i.nb_prospects_rejetes
        taux_conversion = round((i.nb_prospects_confirmes / prospects_traites) * 100, 2) if prospects_traites > 0 else 0

        # Correction : compter et sommer les remises sans surcomptage
        nb_remises = Remise.objects.filter(influenceur=i).count()
        nb_remises_payees = Remise.objects.filter(influenceur=i, statut='payee').count()
        total_gains = Remise.objects.filter(influenceur=i, statut='payee').aggregate(total=Sum('montant'))['total'] or 0

        top_influenceurs.append({
            'id': i.id,
            'nom': i.nom,
            'email': i.email,
            'code_affiliation': i.code_affiliation,
            'nb_prospects': i.nb_prospects,
            'nb_prospects_confirmes': i.nb_prospects_confirmes,
            'nb_prospects_rejetes': i.nb_prospects_rejetes,
            'nb_prospects_en_attente': i.nb_prospects_en_attente,
            'taux_conversion': taux_conversion,
            'nb_remises': nb_remises,
            'nb_remises_payees': nb_remises_payees,
            'total_gains': float(total_gains),
            'date_creation': i.date_creation.strftime('%Y-%m-%d') if i.date_creation else None
        })

    # Evolution prospects (nombre d'inscriptions par jour sur les 7 derniers jours)
    today = timezone.now().date()
    evolution_prospects = []
    for i in range(7):
        day = today - timedelta(days=6-i)
        count = Prospect.objects.filter(date_inscription__date=day).count()
        evolution_prospects.append({'date': str(day), 'count': count})

    data = {
        'total_influenceurs': total_influenceurs,
        'total_prospects': total_prospects,
        'prospects_en_attente': prospects_en_attente,
        'prospects_confirmes': prospects_confirmes,
        'prospects_rejetes': prospects_rejetes,
        'taux_conversion_global': taux_conversion_global,
        'total_primes': total_primes,
        'primes_payees': primes_payees,
        'primes_en_attente': primes_en_attente,
        'total_gains_global': float(total_gains_global),
        'total_gains_en_attente': float(total_gains_en_attente),
        'top_influenceurs': top_influenceurs,
        'evolution_prospects': evolution_prospects,
    }
    return Response(data)