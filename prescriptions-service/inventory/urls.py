from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MedicationCategoryViewSet, MedicationViewSet, StockMovementViewSet

router = DefaultRouter()
router.register(r'categories', MedicationCategoryViewSet)
router.register(r'medications', MedicationViewSet)
router.register(r'stock-movements', StockMovementViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 