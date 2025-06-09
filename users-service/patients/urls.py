from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PatientViewSet, VaccinationViewSet

router = DefaultRouter()
router.register(r'', PatientViewSet)
router.register(r'vaccinations', VaccinationViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 