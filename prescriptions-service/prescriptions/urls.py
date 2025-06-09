from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PrescriptionViewSet, PrescriptionDispensationViewSet

router = DefaultRouter()
router.register(r'prescriptions', PrescriptionViewSet)
router.register(r'dispensations', PrescriptionDispensationViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 