from django.core.management.base import BaseCommand
from influenceur.models import Influenceur

class Command(BaseCommand):
    help = 'Teste la connexion d\'un influenceur avec un mot de passe'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, required=True, help='Email de l\'influenceur')
        parser.add_argument('--password', type=str, required=True, help='Mot de passe à tester')

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        
        try:
            influenceur = Influenceur.objects.get(email=email)
            
            self.stdout.write(f'\n=== TEST DE CONNEXION POUR {email} ===')
            self.stdout.write(f'Nom: {influenceur.nom}')
            self.stdout.write(f'Email: {influenceur.email}')
            self.stdout.write(f'Mot de passe testé: {password}')
            
            # Tester la connexion
            if influenceur.check_password(password):
                self.stdout.write(self.style.SUCCESS('✓ CONNEXION RÉUSSIE'))
                self.stdout.write('Le mot de passe est correct !')
            else:
                self.stdout.write(self.style.ERROR('✗ CONNEXION ÉCHOUÉE'))
                self.stdout.write('Le mot de passe est incorrect.')
                
                # Afficher des suggestions
                self.stdout.write('\nSuggestions:')
                self.stdout.write('- Vérifiez l\'orthographe du mot de passe')
                self.stdout.write('- Vérifiez les espaces avant/après')
                self.stdout.write('- Vérifiez la casse (majuscules/minuscules)')
                
        except Influenceur.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Influenceur avec email {email} non trouvé')) 