import uuid

from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver


class PetType(models.Model):
    """Model for a variety of pets"""
    name = models.CharField(max_length=100, db_index=True)

    def __str__(self):
        return self.name


class Pet(models.Model):
    """Model for describing a particular pet"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, auto_created=True)
    name = models.CharField(max_length=50, verbose_name='Pet name')
    age = models.IntegerField()
    type = models.ForeignKey(PetType, on_delete=models.CASCADE, verbose_name='Pet type')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'''
                Name: {self.name}
                Age: {self.age}
                Type: {self.type}
                '''


class PetImage(models.Model):
    """Model for specific pet images"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, auto_created=True)
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='images/', max_length=100, blank=True)

    def __str__(self):
        return self.image


@receiver(pre_delete, sender=PetImage)
def image_model_delete(sender, instance, **kwargs):
    if instance.image.name:
        instance.image.delete(save=False)
