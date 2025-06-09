from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from datetime import datetime, date, timedelta
from .models import Prescription, PrescriptionItem, PrescriptionDispensation, PrescriptionDispensationItem
from .serializers import (
    PrescriptionListSerializer, PrescriptionDetailSerializer, PrescriptionCreateSerializer,
    PrescriptionItemSerializer, PrescriptionDispensationSerializer
)
from .utils import generate_prescription_pdf_response

class PrescriptionViewSet(viewsets.ModelViewSet):
    queryset = Prescription.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'status', 'patient_id', 'owner_id', 'veterinarian_id', 'consultation_id',
        'follow_up_required', 'can_be_dispensed_multiple_times'
    ]
    search_fields = ['prescription_number', 'diagnosis', 'symptoms', 'treatment_notes']
    ordering_fields = ['issue_date', 'expiration_date', 'total_amount']
    ordering = ['-issue_date']

    def get_serializer_class(self):
        if self.action == 'list':
            return PrescriptionListSerializer
        elif self.action == 'create':
            return PrescriptionCreateSerializer
        elif self.action == 'retrieve':
            return PrescriptionDetailSerializer
        return PrescriptionDetailSerializer

    def get_queryset(self):
        """Personalizar queryset según rol del usuario"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Los veterinarios solo ven sus propias recetas
        if user.get('role') == 'Veterinario':
            queryset = queryset.filter(veterinarian_id=user.get('id'))
        
        # Filtrar por rango de fechas
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(issue_date__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(issue_date__date__lte=end_date)
        
        return queryset

    def create(self, request, *args, **kwargs):
        """Solo veterinarios pueden crear recetas"""
        if request.user.get('role') != 'Veterinario':
            return Response(
                {'error': 'Solo los veterinarios pueden crear recetas'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def issue(self, request, pk=None):
        """Emitir una receta (cambiar de borrador a emitida)"""
        prescription = self.get_object()
        
        # Verificar permisos
        if (request.user.get('role') != 'Admin' and 
            prescription.veterinarian_id != request.user.get('id')):
            return Response(
                {'error': 'No tiene permisos para emitir esta receta'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if prescription.status != 'BORRADOR':
            return Response(
                {'error': 'Solo se pueden emitir recetas en estado borrador'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar que tenga items
        if not prescription.items.exists():
            return Response(
                {'error': 'La receta debe tener al menos un medicamento'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        prescription.status = 'EMITIDA'
        prescription.save()
        
        serializer = self.get_serializer(prescription)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancelar una receta"""
        prescription = self.get_object()
        
        # Verificar permisos
        if (request.user.get('role') != 'Admin' and 
            prescription.veterinarian_id != request.user.get('id')):
            return Response(
                {'error': 'No tiene permisos para cancelar esta receta'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if prescription.status in ['DISPENSADA', 'CANCELADA']:
            return Response(
                {'error': 'No se puede cancelar una receta dispensada o ya cancelada'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        prescription.status = 'CANCELADA'
        prescription.save()
        
        serializer = self.get_serializer(prescription)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def download_pdf(self, request, pk=None):
        """Descargar PDF de la receta"""
        prescription = self.get_object()
        
        # Verificar que la receta esté emitida
        if prescription.status == 'BORRADOR':
            return Response(
                {'error': 'No se puede generar PDF de recetas en borrador'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            return generate_prescription_pdf_response(prescription)
        except Exception as e:
            return Response(
                {'error': 'Error al generar el PDF'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """Obtener recetas que vencen pronto"""
        days_ahead = int(request.query_params.get('days', 7))
        limit_date = date.today() + timedelta(days=days_ahead)
        
        expiring_prescriptions = self.get_queryset().filter(
            expiration_date__lte=limit_date,
            status__in=['EMITIDA', 'PARCIAL']
        )
        
        serializer = PrescriptionListSerializer(expiring_prescriptions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_prescriptions(self, request):
        """Obtener recetas del veterinario autenticado"""
        if request.user.get('role') != 'Veterinario':
            return Response(
                {'error': 'Solo los veterinarios pueden acceder a sus recetas'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        prescriptions = self.get_queryset().filter(veterinarian_id=request.user.get('id'))
        
        # Filtros adicionales
        status_filter = request.query_params.get('status')
        if status_filter:
            prescriptions = prescriptions.filter(status=status_filter)
        
        page = self.paginate_queryset(prescriptions)
        if page is not None:
            serializer = PrescriptionListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = PrescriptionListSerializer(prescriptions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_medication(self, request, pk=None):
        """Agregar medicamento a una receta"""
        prescription = self.get_object()
        
        # Verificar que esté en borrador
        if prescription.status != 'BORRADOR':
            return Response(
                {'error': 'Solo se pueden agregar medicamentos a recetas en borrador'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = request.data.copy()
        data['prescription'] = prescription.id
        
        serializer = PrescriptionItemSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            item = serializer.save()
            
            # Recalcular total de la receta
            prescription.total_amount = sum(item.total_price for item in prescription.items.all())
            prescription.save()
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PrescriptionDispensationViewSet(viewsets.ModelViewSet):
    queryset = PrescriptionDispensation.objects.all()
    serializer_class = PrescriptionDispensationSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['prescription', 'dispensed_by', 'received_by_document']
    ordering = ['-dispensation_date']

    def create(self, request, *args, **kwargs):
        """Solo recepcionistas y administradores pueden dispensar"""
        if request.user.get('role') not in ['Admin', 'Recepcionista']:
            return Response(
                {'error': 'Solo administradores y recepcionistas pueden dispensar medicamentos'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().create(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def by_prescription(self, request):
        """Obtener dispensaciones de una receta específica"""
        prescription_id = request.query_params.get('prescription_id')
        
        if not prescription_id:
            return Response(
                {'error': 'Se requiere el parámetro prescription_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        dispensations = self.get_queryset().filter(prescription_id=prescription_id)
        serializer = self.get_serializer(dispensations, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def daily_report(self, request):
        """Reporte diario de dispensaciones"""
        report_date = request.query_params.get('date', date.today().isoformat())
        
        try:
            report_date = datetime.strptime(report_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Formato de fecha inválido. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        dispensations = self.get_queryset().filter(dispensation_date__date=report_date)
        
        # Calcular estadísticas
        total_dispensations = dispensations.count()
        total_amount = sum(d.total_amount for d in dispensations)
        unique_prescriptions = dispensations.values('prescription').distinct().count()
        
        report_data = {
            'date': report_date,
            'total_dispensations': total_dispensations,
            'total_amount': total_amount,
            'unique_prescriptions': unique_prescriptions,
            'dispensations': PrescriptionDispensationSerializer(dispensations, many=True).data
        }
        
        return Response(report_data) 