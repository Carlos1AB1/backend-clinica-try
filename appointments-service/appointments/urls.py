from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AppointmentViewSet, VeterinarianScheduleViewSet, AppointmentBlockViewSet

router = DefaultRouter()
router.register(r'appointments', AppointmentViewSet)
router.register(r'schedules', VeterinarianScheduleViewSet)
router.register(r'blocks', AppointmentBlockViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 