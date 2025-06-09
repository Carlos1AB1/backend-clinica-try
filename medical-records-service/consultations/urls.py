from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ConsultationViewSet, ConsultationProcedureViewSet, ConsultationNoteViewSet, TreatmentViewSet

router = DefaultRouter()
router.register(r'consultations', ConsultationViewSet)
router.register(r'procedures', ConsultationProcedureViewSet)
router.register(r'notes', ConsultationNoteViewSet)
router.register(r'treatments', TreatmentViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 