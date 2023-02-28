from rest_framework import serializers
from .models import Pet, PetImage


class PetImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PetImage
        fields = ['id', 'image']


class PetSerializer(serializers.ModelSerializer):
    photos = PetImageSerializer(many=True, read_only=True)

    class Meta:
        model = Pet
        fields = ['id', 'name', 'age', 'type', 'photos', 'created_at']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['type'] = instance.type.name
        representation['created_at'] = instance.created_at.strftime("%Y-%m-%dT%H:%M:%S")
        return representation
