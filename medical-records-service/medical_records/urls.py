from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MedicalRecordViewSet, MedicalFileViewSet, VitalSignsViewSet

router = DefaultRouter()
router.register(r'records', MedicalRecordViewSet)
router.register(r'files', MedicalFileViewSet)
router.register(r'vital-signs', VitalSignsViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 