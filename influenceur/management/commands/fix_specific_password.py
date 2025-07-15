from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from influenceur.models import Influenceur

class Command(BaseCommand):
    help = 'Corrige le mot de passe d\'un influenceur spécifique'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, required=True, help='Email de l\'influenceur')
        parser.add_argument('--password', type=str, required=True, help='Nouveau mot de passe')

    def handle(self, *args, **options):
        email = options['email']
        new_password = options['password']
        
        try:
            influenceur = Influenceur.objects.get(email=email)
            
            # Afficher l'ancien mot de passe
            self.stdout.write(f'Ancien mot de passe: {influenceur.password[:30]}...')
            
            # Définir le nouveau mot de passe
            influenceur.set_password(new_password)
            
            self.stdout.write(self.style.SUCCESS(f'Mot de passe mis à jour pour {email}'))
            self.stdout.write(f'Nouveau hash: {influenceur.password[:30]}...')
            
            # Tester le nouveau mot de passe
            if influenceur.check_password(new_password):
                self.stdout.write(self.style.SUCCESS('✓ Le nouveau mot de passe fonctionne'))
            else:
                self.stdout.write(self.style.ERROR('✗ Le nouveau mot de passe ne fonctionne pas'))
                
        except Influenceur.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Influenceur avec email {email} non trouvé')) 