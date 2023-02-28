from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import SimpleRouter

from pets import settings
from pets_module.views import PetViewSet

router = SimpleRouter(trailing_slash=False)
router.register(r'pets', PetViewSet, basename='pets')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(router.urls)),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
