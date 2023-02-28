import uuid

from django.db.models import Count
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import exceptions, mixins, status
from rest_framework.decorators import action
from rest_framework.exceptions import ParseError
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from .models import Pet, PetImage
from .serializers import PetSerializer


class PetViewSet(mixins.CreateModelMixin,
                 mixins.ListModelMixin,
                 mixins.DestroyModelMixin,
                 GenericViewSet):
    serializer_class = PetSerializer

    def get_queryset(self):
        has_photos = self.request.query_params.get('has_photos')
        if not has_photos:
            return Pet.objects.all()
        if has_photos.lower() not in ['true', 'false']:
            raise exceptions.ValidationError({'message': 'has_photos should be boolean field'})
        queryset = Pet.objects.annotate(count=Count('photos'))
        return queryset.filter(count__gte=1) if has_photos.lower() == 'true' else queryset.filter(count=0)

    def list(self, request, *args, **kwargs):
        try:
            limit = int(self.request.query_params.get('limit', 20))
            offset = int(self.request.query_params.get('offset', 0))
            assert limit >= 0 and offset >= 0
        except (ValueError, AssertionError):
            raise exceptions.ValidationError({'message': 'limit and offset should be positive integer value'})
        queryset = self.get_queryset()
        shifted_queryset = queryset[offset: offset + limit]
        serializer = self.get_serializer(shifted_queryset, many=True)
        response = Response(serializer.data)
        response.data = {'count': queryset.count(),
                         'data': response.data}
        return response

    def create(self, request, *args, **kwargs):
        if request.data.get('photos'):
            raise exceptions.ValidationError({'message': "To upload photo use endpoint POST /pets/{id}/photo"})
        return super().create(request, *args, **kwargs)

    @action(methods=['post'], detail=True)
    def photo(self, request, pk):
        if not is_valid_uuid(pk):
            raise exceptions.ValidationError({'message': 'Incorrect ID'})
        try:
            file = request.data['file']
            pet = Pet.objects.get(pk=pk)
            pet_img = PetImage(pet=pet, image=file)
            pet_img.save()
            return Response({'id': pet_img.pk,
                             'url': request.build_absolute_uri(pet_img.image.url)})
        except ObjectDoesNotExist:
            raise exceptions.ValidationError({'message': 'Pet with the matching ID was not found'})
        except KeyError:
            raise ParseError('Request has no resource file attached')

    def delete(self, request, *args, **kwargs):
        pet_ids = request.data.get('ids')
        if not pet_ids:
            raise exceptions.ValidationError({'ids': ["This field is required."]})
        if type(pet_ids) != list:
            raise exceptions.ValidationError({'message': 'ids field should be a list with id values'})
        return self.delete_many(pet_ids)

    def delete_many(self, pet_ids):
        errors = []
        existing_ids = set([str(x) for x in Pet.objects.values_list('pk', flat=True)])
        for pet_id in pet_ids:
            if not is_valid_uuid(pet_id):
                errors.append({'id': pet_id, 'error': 'Incorrect ID'})
            elif pet_id not in existing_ids:
                errors.append({'id': pet_id, 'error': 'Pet with the matching ID was not found.'})
        errors_id = [x['id'] for x in errors]
        correct_ids = [x for x in pet_ids if x not in errors_id]
        Pet.objects.filter(pk__in=correct_ids).delete()
        return Response(data={'deleted': len(correct_ids),
                              'errors': errors},
                        status=status.HTTP_200_OK)


def is_valid_uuid(val):
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False
