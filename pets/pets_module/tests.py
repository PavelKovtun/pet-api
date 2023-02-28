from django.urls import reverse
from django.conf import settings
from rest_framework import status
from rest_framework.test import APITestCase

from pets.settings import API_KEY, API_KEY_HEADER
from pets_module.models import Pet, PetImage, PetType

from PIL import Image
import tempfile

from pets_module.serializers import PetSerializer

settings.MEDIA_ROOT = '/test'


class TestCreatePet(APITestCase):
    """ Test module for POST request pet API """

    fixtures = ['pet_types.json']

    def setUp(self) -> None:
        self.headers = {'HTTP_' + API_KEY_HEADER: API_KEY}

    def test_unauthorized(self):
        url = reverse('pets-list')
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_pet(self):
        url = reverse('pets-list')
        self.client.credentials(**self.headers)
        data = {'name': 'SomePet', 'age': 6, 'type': 2}
        self.assertEqual(Pet.objects.count(), 0)
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Pet.objects.count(), 1)
        pet = Pet.objects.get()
        serializer = PetSerializer(pet, many=False)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(pet.name, 'SomePet')
        self.assertEqual(pet.age, 6)
        self.assertEqual(pet.type.name, 'dog')

    def test_fail_create_pet_with_photo(self):
        url = reverse('pets-list')
        self.client.credentials(**self.headers)
        image = temporary_file()
        data = {'name': 'SomePet', 'age': 6, 'type': 2, 'photos': image}
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_fail_create_without_req_field(self):
        url = reverse('pets-list')
        self.client.credentials(**self.headers)
        self.assertEqual(Pet.objects.count(), 0)
        response = self.client.post(url, {'name': 'SomePet', 'age': 6}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.post(url, {'age': 6, 'type': 2}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.post(url, {'name': 'SomePet', 'type': 2}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Pet.objects.count(), 0)

    def test_upload_pet_photo(self):
        pet = Pet.objects.create(name='Pet', age=6, type=PetType.objects.get(pk=2))
        pet.save()
        url = reverse('pets-photo', kwargs={'pk': pet.pk})
        self.client.credentials(**self.headers)
        image = temporary_file()
        self.assertEqual(PetImage.objects.count(), 0)
        response = self.client.post(url, {'file': image}, format='multipart')
        self.assertEqual(PetImage.objects.count(), 1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        photo = PetImage.objects.get()
        self.assertEqual(response.data['id'], photo.pk)

    def test_fail_upload_photo_with_wrong_id(self):
        self.client.credentials(**self.headers)
        url = reverse('pets-photo', kwargs={'pk': '1'})
        image = temporary_file()
        response = self.client.post(url, {'file': image}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_fail_upload_photo_to_deleted_pet(self):
        pet = Pet.objects.create(name='Pet', age=6, type=PetType.objects.get(pk=2))
        pet.save()
        self.client.credentials(**self.headers)
        self.client.delete(reverse('pets-list'), {'ids': [pet.pk]}, format='json')
        url = reverse('pets-photo', kwargs={'pk': pet.pk})
        image = temporary_file()
        response = self.client.post(url, {'file': image}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_fail_upload_photo_without_file(self):
        pet = Pet.objects.create(name='Pet', age=6, type=PetType.objects.get(pk=2))
        pet.save()
        url = reverse('pets-photo', kwargs={'pk': pet.pk})
        self.client.credentials(**self.headers)
        response = self.client.post(url, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestDeletePets(APITestCase):
    """ Test module for DELETE request pet API """

    fixtures = ['pet_types.json']

    def setUp(self) -> None:
        self.headers = {'HTTP_' + API_KEY_HEADER: API_KEY}
        self.url = reverse('pets-list')
        self.first_pet = Pet.objects.create(name='FirstPet', age=16, type=PetType.objects.get(pk=1))
        self.first_pet.save()
        self.second_pet = Pet.objects.create(name='SecondPet', age=6, type=PetType.objects.get(pk=2))
        self.second_pet.save()

    def test_unauthorized(self):
        response = self.client.delete(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_pets(self):
        self.client.credentials(**self.headers)
        self.assertEqual(Pet.objects.all().count(), 2)
        response = self.client.delete(self.url, {'ids': [self.first_pet.pk, self.second_pet.pk]}, format='json')
        self.assertEqual(Pet.objects.all().count(), 0)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['deleted'], 2)
        self.assertEqual(response.data['errors'], [])

    def test_delete_without_ids(self):
        self.client.credentials(**self.headers)
        response = self.client.delete(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_bad_format_ids(self):
        self.client.credentials(**self.headers)
        response = self.client.delete(self.url, {'ids': self.first_pet.pk}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_nonexistent_pet(self):
        self.client.credentials(**self.headers)
        self.client.delete(self.url, {'ids': [self.first_pet.pk]}, format='json')
        self.assertEqual(Pet.objects.all().count(), 1)
        response = self.client.delete(self.url, {'ids': ["1"]}, format='json')
        self.assertEqual(Pet.objects.all().count(), 1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['deleted'], 0)
        self.assertEqual(len(response.data['errors']), 1)

    def test_delete_not_uuid(self):
        self.client.credentials(**self.headers)
        response = self.client.delete(self.url, {'ids': ["1"]}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['deleted'], 0)
        self.assertEqual(len(response.data['errors']), 1)

    def test_delete_photo_with_pet(self):
        self.client.credentials(**self.headers)
        image = temporary_file()
        self.client.post(reverse('pets-photo', kwargs={'pk': self.first_pet.pk}), {'file': image}, format='multipart')
        self.assertEqual(PetImage.objects.count(), 1)
        self.client.delete(self.url, {'ids': [self.first_pet.pk]}, format='json')
        self.assertEqual(PetImage.objects.count(), 0)


class TestGetPets(APITestCase):
    """ Test module for GET request pet API """

    fixtures = ['pet_types.json']

    def setUp(self) -> None:
        self.headers = {'HTTP_' + API_KEY_HEADER: API_KEY}
        self.create_pets_with_photos(5)
        self.create_pets_without_photos(10)

    def create_pets_without_photos(self, count):
        for i in range(count):
            pet = Pet.objects.create(name=f'Pet{i}', age=16, type=PetType.objects.get(pk=1))
            pet.save()

    def create_pets_with_photos(self, count):
        for i in range(count):
            pet = Pet.objects.create(name=f'Pet{i}', age=6, type=PetType.objects.get(pk=2))
            pet.save()
            image = temporary_file()
            self.client.post(reverse('pets-photo', kwargs={'pk': pet.pk}), {'file': image}, **self.headers,
                             format='multipart')

    def test_unauthorized(self):
        url = reverse('pets-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_pets(self):
        url = reverse('pets-list')
        self.client.credentials(**self.headers)
        response = self.client.get(url, **self.headers, type='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 15)
        self.assertEqual(len(response.data['data']), 15)

    def test_limit_pets(self):
        url = reverse('pets-list')
        self.client.credentials(**self.headers)
        response = self.client.get(url, {'limit': 10}, type='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 15)
        self.assertEqual(len(response.data['data']), 10)

    def test_default_limit_pets(self):
        url = reverse('pets-list')
        self.client.credentials(**self.headers)
        self.create_pets_without_photos(10)  # 15 + 10 = 25
        response = self.client.get(url, type='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 25)
        self.assertEqual(len(response.data['data']), 20)

    def test_offset_pets(self):
        url = reverse('pets-list')
        self.client.credentials(**self.headers)
        response = self.client.get(url, {'offset': 2}, type='json')
        third_pet = Pet.objects.filter()[2:3].get()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data'][0]['id'], str(third_pet.pk))  # the same id
        self.assertEqual(response.data['count'], 15)
        self.assertEqual(len(response.data['data']), 13)  # 15 - 2 = 13

    def test_default_offset_pets(self):
        url = reverse('pets-list')
        self.client.credentials(**self.headers)
        first_pet = Pet.objects.filter()[:1].get()
        response = self.client.get(url, type='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data'][0]['id'], str(first_pet.pk))  # the same id
        self.assertEqual(response.data['count'], 15)
        self.assertEqual(len(response.data['data']), 15)

    def test_get_pets_with_photo_filter(self):
        url = reverse('pets-list')
        self.client.credentials(**self.headers)
        response = self.client.get(url, {'has_photos': 'True'}, type='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 5)
        self.assertEqual(len(response.data['data']), 5)
        response = self.client.get(url, {'has_photos': 'False'}, type='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 10)
        self.assertEqual(len(response.data['data']), 10)

    def test_bad_query_params(self):
        url = reverse('pets-list')
        self.client.credentials(**self.headers)
        bad_patterns = ['-1', 'fff']
        query_params = ['limit', 'offset', 'has_photos']
        for pattern in bad_patterns:
            for param in query_params:
                response = self.client.get(url, {param: pattern}, type='json')
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


def temporary_file():
    image = Image.new('RGB', (100, 100))
    tmp_file = tempfile.NamedTemporaryFile(prefix='test', suffix='.jpg')
    image.save(tmp_file)
    tmp_file.seek(0)
    return image
