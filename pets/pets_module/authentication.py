from django.contrib.auth.models import AnonymousUser
from rest_framework import authentication, exceptions

from pets import settings


class APIKeyAuthentication(authentication.BaseAuthentication):
    def authenticate_header(self, request):
        return settings.API_KEY_HEADER

    def authenticate(self, request):
        api_key_header = request.headers.get(settings.API_KEY_HEADER)
        if api_key_header != settings.API_KEY:
            raise exceptions.NotAuthenticated('API KEY is not valid')
        return AnonymousUser, None
