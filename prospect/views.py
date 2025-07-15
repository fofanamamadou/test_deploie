from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .models import Prospect
from .serializers import ProspectSerializers
from influenceur.models import Influenceur
from influenceur.permissions import CanValidateProspects, IsInfluenceurOrAdmin
from influenceur.auth import get_influenceur_from_user
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

@api_view(['GET'])
@permission_classes([IsInfluenceurOrAdmin])
def prospect_view(request):
    """
    Vue API pour lister tous les prospects (GET)
    Seuls les influenceurs connectés et admins peuvent accéder.
    Support du filtre par influenceur: ?influenceur={id}
    Support du filtre par statut: ?statut={en_attente|confirme|rejeter}
    """
    if request.method == 'GET':
        # Récupérer les filtres depuis les paramètres GET
        influenceur_id = request.GET.get('influenceur')
        statut = request.GET.get('statut')
        
        # Filtrer par influenceur si ce n'est pas un admin
        current_influenceur = get_influenceur_from_user(request.user)
        
        if not request.user.is_superuser and current_influenceur:
            # Influenceur connecté: voir seulement ses prospects
            prospects = Prospect.objects.filter(influenceur=current_influenceur)
        else:
            # Admin: voir tous les prospects
            prospects = Prospect.objects.all()
            
            # Appliquer le filtre par influenceur si spécifié
            if influenceur_id:
                try:
                    influenceur = Influenceur.objects.get(id=influenceur_id)
                    prospects = prospects.filter(influenceur=influenceur)
                except Influenceur.DoesNotExist:
                    return Response({
                        'error': 'Influenceur non trouvé'
                    }, status=status.HTTP_404_NOT_FOUND)
        
        # Appliquer le filtre par statut si spécifié
        if statut and statut in ['en_attente', 'confirme', 'rejeter']:
            prospects = prospects.filter(statut=statut)
            
        serializer = ProspectSerializers(prospects, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsInfluenceurOrAdmin])
def prospect_detail_view(request, pk):
    """
    Vue API pour obtenir les détails d'un prospect (GET)
    """
    prospect = get_object_or_404(Prospect, pk=pk)
    
    # Vérifier les permissions
    current_influenceur = get_influenceur_from_user(request.user)
    if not request.user.is_superuser and current_influenceur and prospect.influenceur != current_influenceur:
        return Response({'error': 'Accès non autorisé'}, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        serializer = ProspectSerializers(prospect)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([CanValidateProspects])
def prospect_valider_view(request, pk):
    """
    Vue API pour valider un prospect (passer son statut à 'confirme').
    Seuls les utilisateurs avec permission de validation peuvent accéder.
    """
    prospect = get_object_or_404(Prospect, pk=pk)
    
    # Vérifier les permissions pour ce prospect spécifique
    current_influenceur = get_influenceur_from_user(request.user)
    if not request.user.is_superuser and current_influenceur and prospect.influenceur != current_influenceur:
        return Response({'error': 'Accès non autorisé'}, status=status.HTTP_403_FORBIDDEN)
    
    if prospect.statut == 'confirme':
        return Response({'detail': 'Ce prospect est déjà confirmé.'}, status=status.HTTP_400_BAD_REQUEST)
    prospect.statut = 'confirme'
    prospect.save()
    serializer = ProspectSerializers(prospect)
    return Response({'detail': 'Prospect validé avec succès.', 'prospect': serializer.data}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([CanValidateProspects])
def prospect_rejeter_view(request, pk):
    """
    Vue API pour rejeter un prospect (passer son statut à 'rejeter').
    Seuls les utilisateurs avec permission de validation peuvent accéder.
    """
    prospect = get_object_or_404(Prospect, pk=pk)
    
    # Vérifier les permissions pour ce prospect spécifique
    current_influenceur = get_influenceur_from_user(request.user)
    if not request.user.is_superuser and current_influenceur and prospect.influenceur != current_influenceur:
        return Response({'error': 'Accès non autorisé'}, status=status.HTTP_403_FORBIDDEN)
    
    if prospect.statut == 'rejeter':
        return Response({'detail': 'Ce prospect est déjà rejeté.'}, status=status.HTTP_400_BAD_REQUEST)
    prospect.statut = 'rejeter'
    prospect.save()
    serializer = ProspectSerializers(prospect)
    return Response({'detail': 'Prospect rejeté avec succès.', 'prospect': serializer.data}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsInfluenceurOrAdmin])
def prospects_sans_remise_view(request):
    """
    Vue API pour lister tous les prospects confirmés sans remise associée.
    Seuls les admins peuvent voir tous les prospects confirmés sans remise.
    """
    current_influenceur = get_influenceur_from_user(request.user)
    if not request.user.is_superuser and current_influenceur:
        prospects = Prospect.objects.filter(
            remise__isnull=True, 
            influenceur=current_influenceur,
            statut='confirme'  # Seulement les prospects confirmés
        )
    else:
        prospects = Prospect.objects.filter(
            remise__isnull=True,
            statut='confirme'  # Seulement les prospects confirmés
        )
        
    serializer = ProspectSerializers(prospects, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsInfluenceurOrAdmin])
def prospects_statistiques_view(request):
    """
    Vue API pour obtenir les statistiques des prospects par statut.
    """
    current_influenceur = get_influenceur_from_user(request.user)
    
    if not request.user.is_superuser and current_influenceur:
        # Influenceur connecté: voir seulement ses prospects
        prospects = Prospect.objects.filter(influenceur=current_influenceur)
    else:
        # Admin: voir tous les prospects
        prospects = Prospect.objects.all()
    
    # Statistiques par statut
    stats = {
        'total': prospects.count(),
        'en_attente': prospects.filter(statut='en_attente').count(),
        'confirme': prospects.filter(statut='confirme').count(),
        'rejeter': prospects.filter(statut='rejeter').count(),
    }
    
    # Calculer le taux de conversion (confirmés / (confirmés + rejetés))
    prospects_traites = stats['confirme'] + stats['rejeter']
    if prospects_traites > 0:
        stats['taux_conversion'] = round((stats['confirme'] / prospects_traites) * 100, 2)
    else:
        stats['taux_conversion'] = 0
    
    return Response(stats, status=status.HTTP_200_OK)

@csrf_exempt
@require_http_methods(["POST"])
def affiliation_form_view(request, code_affiliation):
    """
    Vue pour traiter les soumissions.
    Cette vue est publique (pas d'authentification requise).
    """
    try:
        influenceur = Influenceur.objects.get(code_affiliation=code_affiliation, is_active=True)
    except Influenceur.DoesNotExist:
        return HttpResponse('<h1>Code d\'affiliation invalide</h1>', status=404)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nom = data.get('nom')
            telephone = data.get('telephone')
            email = data.get('email')
            
            # Nouveaux champs éducatifs
            niveau_etude = data.get('niveau_etude')
            niveau_etude_autre = data.get('niveau_etude_autre')
            serie_bac = data.get('serie_bac')
            serie_bac_autre = data.get('serie_bac_autre')
            filiere_souhaitee = data.get('filiere_souhaitee')
            filiere_autre = data.get('filiere_autre')

            if not nom or not telephone:
                return JsonResponse({'error': 'Nom et Téléphone requis'}, status=400)
            
            # Validation des champs conditionnels
            if niveau_etude == 'autre' and not niveau_etude_autre:
                return JsonResponse({'error': 'Veuillez préciser votre niveau d\'étude'}, status=400)
            
            if niveau_etude == 'bac':
                if not serie_bac:
                    return JsonResponse({'error': 'Veuillez sélectionner votre série du bac'}, status=400)
                if serie_bac == 'autre' and not serie_bac_autre:
                    return JsonResponse({'error': 'Veuillez préciser votre série du bac'}, status=400)
            
            if not filiere_souhaitee:
                return JsonResponse({'error': 'Veuillez sélectionner une filière souhaitée'}, status=400)
            if filiere_souhaitee == 'autre' and not filiere_autre:
                return JsonResponse({'error': 'Veuillez préciser votre filière souhaitée'}, status=400)
            
            # Créer le prospect avec les nouveaux champs
            prospect = Prospect.objects.create(
                nom=nom,
                telephone=telephone,
                email=email,
                influenceur=influenceur,
                niveau_etude=niveau_etude,
                niveau_etude_autre=niveau_etude_autre,
                serie_bac=serie_bac,
                serie_bac_autre=serie_bac_autre,
                filiere_souhaitee=filiere_souhaitee,
                filiere_autre=filiere_autre
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Inscription réussie !',
                'prospect_id': prospect.id
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Données JSON invalides'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
