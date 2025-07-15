from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password, check_password, is_password_usable
from influenceur.models import Influenceur

class Command(BaseCommand):
    help = 'Diagnostique les problèmes de mot de passe des influenceurs'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='Email spécifique à vérifier')
        parser.add_argument('--password', type=str, help='Mot de passe à tester')

    def handle(self, *args, **options):
        email = options.get('email')
        test_password = options.get('password')
        
        if email:
            # Vérifier un influenceur spécifique
            try:
                influenceur = Influenceur.objects.get(email=email)
                self.stdout.write(f'\n=== DIAGNOSTIC POUR {email} ===')
                self.stdout.write(f'Nom: {influenceur.nom}')
                self.stdout.write(f'Email: {influenceur.email}')
                self.stdout.write(f'Mot de passe stocké: {influenceur.password[:20]}...')
                self.stdout.write(f'Mot de passe hashé: {influenceur.password.startswith("pbkdf2_")}')
                self.stdout.write(f'Mot de passe utilisable: {is_password_usable(influenceur.password)}')
                
                if test_password:
                    is_valid = influenceur.check_password(test_password)
                    self.stdout.write(f'Test avec "{test_password}": {"✓ VALIDE" if is_valid else "✗ INVALIDE"}')
                    
                    # Test avec make_password
                    hashed_test = make_password(test_password)
                    self.stdout.write(f'Hash du test: {hashed_test[:20]}...')
                    
                    # Comparer avec le hash stocké
                    if influenceur.password == hashed_test:
                        self.stdout.write('✓ Les hashes correspondent')
                    else:
                        self.stdout.write('✗ Les hashes ne correspondent pas')
                        
            except Influenceur.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Influenceur avec email {email} non trouvé'))
        else:
            # Lister tous les influenceurs
            influenceurs = Influenceur.objects.all()
            self.stdout.write(f'\n=== DIAGNOSTIC DE TOUS LES INFLUENCEURS ===')
            
            for influenceur in influenceurs:
                self.stdout.write(f'\n{influenceur.email}:')
                self.stdout.write(f'  - Mot de passe: {influenceur.password[:30]}...')
                self.stdout.write(f'  - Hashé: {influenceur.password.startswith("pbkdf2_")}')
                self.stdout.write(f'  - Utilisable: {is_password_usable(influenceur.password)}')
                
                if not influenceur.password.startswith('pbkdf2_'):
                    self.stdout.write(self.style.WARNING(f'  ⚠️  Mot de passe non hashé pour {influenceur.email}')) 