from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password, check_password, is_password_usable
from influenceur.models import Influenceur

class Command(BaseCommand):
    help = 'Corrige les mots de passe double-hashés et hash les mots de passe non hashés'

    def handle(self, *args, **options):
        influenceurs = Influenceur.objects.all()
        count_fixed = 0
        count_hashed = 0
        
        for influenceur in influenceurs:
            password = influenceur.password
            
            # Vérifier si le mot de passe est utilisable (correctement hashé)
            if is_password_usable(password):
                # Le mot de passe est correctement hashé
                self.stdout.write(
                    self.style.SUCCESS(f'Mot de passe OK pour {influenceur.email}')
                )
            else:
                # Le mot de passe n'est pas hashé ou mal hashé
                if password.startswith('pbkdf2_'):
                    # Double hashé - essayer de récupérer le mot de passe original
                    try:
                        # Essayer de vérifier avec le mot de passe tel quel
                        if check_password(password, password):
                            # C'est un double hash, on garde le premier hash
                            self.stdout.write(
                                self.style.WARNING(f'Double hash détecté pour {influenceur.email} - correction...')
                            )
                            # On garde le mot de passe tel quel (premier hash)
                            count_fixed += 1
                        else:
                            # Mot de passe corrompu, le rehasher
                            influenceur.password = make_password(password)
                            influenceur.save(update_fields=['password'])
                            count_hashed += 1
                            self.stdout.write(
                                self.style.SUCCESS(f'Mot de passe rehashé pour {influenceur.email}')
                            )
                    except:
                        # Erreur, rehasher
                        influenceur.password = make_password(password)
                        influenceur.save(update_fields=['password'])
                        count_hashed += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'Mot de passe rehashé pour {influenceur.email}')
                        )
                else:
                    # Mot de passe non hashé
                    influenceur.password = make_password(password)
                    influenceur.save(update_fields=['password'])
                    count_hashed += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'Mot de passe hashé pour {influenceur.email}')
                    )
        
        self.stdout.write(
            self.style.SUCCESS(f'{count_fixed} mots de passe double-hashés corrigés')
        )
        self.stdout.write(
            self.style.SUCCESS(f'{count_hashed} mots de passe hashés')
        ) 