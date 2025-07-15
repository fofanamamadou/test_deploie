from django.db import models
from django.utils import timezone
from influenceur.models import Influenceur
from remise.models import Remise

# Create your models here.
class Prospect(models.Model):
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('confirme', 'Confirmé'),
        ('rejeter', 'Rejeté'),
    ]
    
    # Choix pour le niveau d'étude
    NIVEAU_ETUDE_CHOICES = [
        ('bac', 'Baccalauréat'),
        ('licence', 'Licence'),
        ('master', 'Master'),
        ('autre', 'Autre'),
    ]
    
    # Choix pour la série du bac (système malien)
    SERIE_BAC_CHOICES = [
        ('tse', 'TSE - Sciences Exactes'),
        ('tsexp', 'TSEXP - Sciences Expérimentales'),
        ('tseco', 'TSECO - Sciences Économiques'),
        ('tss', 'TSS - Sciences Sociales'),
        ('tll', 'TLL - Lettres et Langues'),
        ('autre', 'Autre'),
    ]
    
    # Choix pour les filières
    FILIERE_CHOICES = [
        ('ig', 'Informatique de Gestion'),
        ('rit', 'Réseaux Informatiques et Télécommunications'),
        ('irs', 'Ingénierie des Réseaux et Systèmes'),
        ('gl', 'Génie Logiciel et Technologie Web / Analyste programmeur'),
        ('gc', 'Génie Civil - Bâtiments et Infrastructures'),
        ('gpg', 'Génie Pétrole et Gaz'),
        ('fc', 'Finance Comptabilité'),
        ('ba', 'Banque et Assurance'),
        ('mm', 'Marketing - Management / Communication'),
        ('grh', 'Gestion des Ressources Humaines'),
        ('glt', 'Gestion de la Logistique et du Transport'),
        ('cim', 'Commerce International et Marketing'),
        ('gea', 'Gestion des Entreprises et des Administrations'),
        ('audit', 'Audit et Contrôle de Gestion'),
        ('autre', 'Autre'),
    ]
    
    # Champs existants
    nom = models.CharField(max_length=100)
    email = models.EmailField(blank=True, unique=True)
    telephone = models.CharField(max_length=8, blank=False, unique=True)
    date_inscription = models.DateTimeField(default=timezone.now)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    influenceur = models.ForeignKey(Influenceur, on_delete=models.CASCADE, related_name='prospects')
    remise = models.ForeignKey(Remise, on_delete=models.SET_NULL, null=True, blank=True, related_name='prospects')
    
    # Nouveaux champs éducatifs
    niveau_etude = models.CharField(max_length=20, choices=NIVEAU_ETUDE_CHOICES, blank=True, null=True)
    niveau_etude_autre = models.CharField(max_length=100, blank=True, null=True)
    
    serie_bac = models.CharField(max_length=20, choices=SERIE_BAC_CHOICES, blank=True, null=True)
    serie_bac_autre = models.CharField(max_length=100, blank=True, null=True)
    
    filiere_souhaitee = models.CharField(max_length=30, choices=FILIERE_CHOICES, blank=True, null=True)
    filiere_autre = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.nom
    
    def get_niveau_etude_display(self):
        """Retourne le niveau d'étude avec le texte personnalisé si 'autre'"""
        if self.niveau_etude == 'autre' and self.niveau_etude_autre:
            return self.niveau_etude_autre
        return super().get_niveau_etude_display()
    
    def get_serie_bac_display(self):
        """Retourne la série du bac avec le texte personnalisé si 'autre'"""
        if self.serie_bac == 'autre' and self.serie_bac_autre:
            return self.serie_bac_autre
        return super().get_serie_bac_display()
    
    def get_filiere_souhaitee_display(self):
        """Retourne la filière souhaitée avec le texte personnalisé si 'autre'"""
        if self.filiere_souhaitee == 'autre' and self.filiere_autre:
            return self.filiere_autre
        return super().get_filiere_souhaitee_display()
    
    def get_serie_bac_required(self):
        """Retourne True si la série du bac est requise (niveau = bac)"""
        return self.niveau_etude == 'bac'
    
    class Meta:
        verbose_name = "Prospect"
        verbose_name_plural = "Prospects"
        ordering = ['-date_inscription']