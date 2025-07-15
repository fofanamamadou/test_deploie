from rest_framework import serializers
from .models import Influenceur

class InfluenceurSerializer(serializers.ModelSerializer):
    """
    Serializer pour la lecture des influenceurs (tous les champs)
    """
    class Meta:
        model = Influenceur
        fields = '__all__'
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def create(self, validated_data):
        # Utiliser la méthode create_influenceur du modèle
        password = validated_data.pop('password', None)
        if password:
            return Influenceur.create_influenceur(
                password=password,
                **validated_data
            )
        else:
            # Si pas de mot de passe, créer normalement
            return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            password = validated_data.pop('password')
            instance.set_password(password)
        return super().update(instance, validated_data)

    def get_affiliation_link(self, obj):
        return obj.get_affiliation_link()

class InfluenceurUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer pour la modification des influenceurs (champs modifiables uniquement)
    """
    class Meta:
        model = Influenceur
        fields = [
            'nom',
            'email', 
            'telephone',
            'role',
            'is_active',
            'peut_creer_influenceurs',
            'peut_valider_prospects',
            'peut_payer_remises',
            'peut_voir_statistiques',
            'password'
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
            'email': {'required': False},  # Email peut être modifié mais pas requis
        }

    def update(self, instance, validated_data):
        # Gérer le mot de passe séparément
        if 'password' in validated_data:
            password = validated_data.pop('password')
            if password:  # Seulement si un nouveau mot de passe est fourni
                instance.set_password(password)
        
        # Mettre à jour les autres champs
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance

class InfluenceurCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour la création d'influenceurs (champs requis pour la création)
    """
    class Meta:
        model = Influenceur
        fields = [
            'nom',
            'email',
            'telephone',
            'password',
            'role',
            'is_active',
            'peut_creer_influenceurs',
            'peut_valider_prospects',
            'peut_payer_remises',
            'peut_voir_statistiques'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'telephone': {'required': False},
            'role': {'required': False},
            'is_active': {'required': False},
            'peut_creer_influenceurs': {'required': False},
            'peut_valider_prospects': {'required': False},
            'peut_payer_remises': {'required': False},
            'peut_voir_statistiques': {'required': False},
        }

    def create(self, validated_data):
        # Utiliser la méthode create_influenceur du modèle
        password = validated_data.pop('password', None)
        if password:
            return Influenceur.create_influenceur(
                password=password,
                **validated_data
            )
        else:
            # Si pas de mot de passe, créer normalement
            return super().create(validated_data)