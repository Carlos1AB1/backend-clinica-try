from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import ReportTemplate, ReportExecution, ReportFilter, ReportSchedule
from .serializers import (
    ReportTemplateSerializer, ReportExecutionSerializer, 
    ReportFilterSerializer, ReportScheduleSerializer
)
from django.db import models

# Create your views here.

class ReportTemplateViewSet(viewsets.ModelViewSet):
    queryset = ReportTemplate.objects.filter(is_active=True)
    serializer_class = ReportTemplateSerializer

    def get_queryset(self):
        """Filtrar plantillas según permisos del usuario"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Solo admins pueden ver plantillas que requieren permisos admin
        if user.get('role') != 'Admin':
            queryset = queryset.filter(requires_admin=False)
        
        return queryset

class ReportExecutionViewSet(viewsets.ModelViewSet):
    queryset = ReportExecution.objects.all()
    serializer_class = ReportExecutionSerializer

    def get_queryset(self):
        """Usuarios solo ven sus propias ejecuciones"""
        queryset = super().get_queryset()
        user = self.request.user
        
        if user.get('role') != 'Admin':
            queryset = queryset.filter(requested_by=user.get('id'))
        
        return queryset.order_by('-requested_at')

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Descargar archivo de reporte"""
        execution = self.get_object()
        
        if not execution.is_ready:
            return Response(
                {'error': 'El reporte no está listo para descargar'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Incrementar contador de descargas
        execution.download_count += 1
        execution.save()
        
        # Aquí iría la lógica para servir el archivo
        return Response({'download_url': f'/media/reports/{execution.file_path}'})

class ReportFilterViewSet(viewsets.ModelViewSet):
    queryset = ReportFilter.objects.all()
    serializer_class = ReportFilterSerializer

    def get_queryset(self):
        """Usuarios ven filtros públicos y sus propios filtros"""
        queryset = super().get_queryset()
        user = self.request.user
        
        if user.get('role') != 'Admin':
            queryset = queryset.filter(
                models.Q(is_public=True) | models.Q(created_by=user.get('id'))
            )
        
        return queryset

class ReportScheduleViewSet(viewsets.ModelViewSet):
    queryset = ReportSchedule.objects.all()
    serializer_class = ReportScheduleSerializer

    def get_queryset(self):
        """Solo admins pueden gestionar reportes programados"""
        if self.request.user.get('role') != 'Admin':
            return ReportSchedule.objects.none()
        
        return super().get_queryset().order_by('next_execution')
