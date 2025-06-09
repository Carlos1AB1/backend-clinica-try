from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ReportTemplateViewSet, ReportExecutionViewSet, 
    ReportFilterViewSet, ReportScheduleViewSet
)

router = DefaultRouter()
router.register(r'templates', ReportTemplateViewSet)
router.register(r'executions', ReportExecutionViewSet)
router.register(r'filters', ReportFilterViewSet)
router.register(r'schedules', ReportScheduleViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 