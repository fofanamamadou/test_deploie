from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from influenceur.models import Influenceur

class Command(BaseCommand):
    help = 'Nettoie les utilisateurs Django orphelins et corrige les problèmes de gestion des utilisateurs'

    def handle(self, *args, **options):
        # 1. Supprimer les utilisateurs Django qui n'ont pas d'influenceur correspondant
        users_to_delete = []
        for user in User.objects.all():
            if not user.is_superuser:  # Ne pas toucher aux superusers
                try:
                    # Vérifier si l'utilisateur correspond à un influenceur
                    influenceur = Influenceur.objects.get(email=user.email)
                    self.stdout.write(
                        self.style.SUCCESS(f'Utilisateur {user.email} OK - influenceur trouvé')
                    )
                except Influenceur.DoesNotExist:
                    # Utilisateur orphelin
                    users_to_delete.append(user)
                    self.stdout.write(
                        self.style.WARNING(f'Utilisateur orphelin trouvé: {user.email}')
                    )
        
        # Supprimer les utilisateurs orphelins
        for user in users_to_delete:
            user.delete()
            self.stdout.write(
                self.style.SUCCESS(f'Utilisateur orphelin supprimé: {user.email}')
            )
        
        # 2. Créer les utilisateurs Django manquants pour les influenceurs
        influenceurs_without_user = []
        for influenceur in Influenceur.objects.all():
            try:
                user = User.objects.get(email=influenceur.email)
                # Mettre à jour les informations utilisateur si nécessaire
                if user.first_name != influenceur.nom.split()[0] if influenceur.nom else '':
                    user.first_name = influenceur.nom.split()[0] if influenceur.nom else ''
                    user.last_name = ' '.join(influenceur.nom.split()[1:]) if len(influenceur.nom.split()) > 1 else ''
                    user.is_active = influenceur.is_active
                    user.save()
                    self.stdout.write(
                        self.style.SUCCESS(f'Utilisateur mis à jour: {influenceur.email}')
                    )
            except User.DoesNotExist:
                # Créer l'utilisateur Django manquant
                influenceurs_without_user.append(influenceur)
        
        # Créer les utilisateurs manquants
        for influenceur in influenceurs_without_user:
            user = User.objects.create(
                username=influenceur.email,
                email=influenceur.email,
                first_name=influenceur.nom.split()[0] if influenceur.nom else '',
                last_name=' '.join(influenceur.nom.split()[1:]) if len(influenceur.nom.split()) > 1 else '',
                is_active=influenceur.is_active,
                password='!'  # Mot de passe factice
            )
            self.stdout.write(
                self.style.SUCCESS(f'Utilisateur créé pour: {influenceur.email}')
            )
        
        # 3. Statistiques
        total_users = User.objects.count()
        total_influenceurs = Influenceur.objects.count()
        superusers = User.objects.filter(is_superuser=True).count()
        
        self.stdout.write(
            self.style.SUCCESS(f'\n=== RÉSUMÉ ===')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Utilisateurs Django orphelins supprimés: {len(users_to_delete)}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Utilisateurs Django créés: {len(influenceurs_without_user)}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Total utilisateurs Django: {total_users} (dont {superusers} superusers)')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Total influenceurs: {total_influenceurs}')
        ) 