from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.db import models
from django.db.models import Sum, Count
from datetime import date, timedelta
from .models import MedicationCategory, Medication, StockMovement
from .serializers import (
    MedicationCategorySerializer, MedicationListSerializer, MedicationDetailSerializer,
    MedicationCreateUpdateSerializer, StockMovementSerializer
)

class MedicationCategoryViewSet(viewsets.ModelViewSet):
    queryset = MedicationCategory.objects.all()
    serializer_class = MedicationCategorySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']
    ordering = ['name']

class MedicationViewSet(viewsets.ModelViewSet):
    queryset = Medication.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'category', 'medication_type', 'prescription_type', 'manufacturer',
        'is_active', 'requires_prescription'
    ]
    search_fields = ['name', 'generic_name', 'active_ingredient', 'manufacturer']
    ordering_fields = ['name', 'current_stock', 'expiration_date', 'unit_price']
    ordering = ['name']

    def get_serializer_class(self):
        if self.action == 'list':
            return MedicationListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return MedicationCreateUpdateSerializer
        return MedicationDetailSerializer

    def get_queryset(self):
        """Personalizar queryset con filtros adicionales"""
        queryset = super().get_queryset()
        
        # Filtro por stock bajo
        low_stock = self.request.query_params.get('low_stock')
        if low_stock == 'true':
            queryset = queryset.filter(current_stock__lte=models.F('minimum_stock'))
        
        # Filtro por medicamentos vencidos
        expired = self.request.query_params.get('expired')
        if expired == 'true':
            queryset = queryset.filter(expiration_date__lt=date.today())
        
        # Filtro por medicamentos que vencen pronto
        expiring_soon = self.request.query_params.get('expiring_soon')
        if expiring_soon:
            try:
                days = int(expiring_soon)
                limit_date = date.today() + timedelta(days=days)
                queryset = queryset.filter(expiration_date__lte=limit_date, expiration_date__gte=date.today())
            except ValueError:
                pass
        
        return queryset

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Obtener medicamentos con stock bajo"""
        low_stock_medications = self.get_queryset().filter(
            current_stock__lte=models.F('minimum_stock'),
            is_active=True
        )
        
        serializer = MedicationListSerializer(low_stock_medications, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def expired(self, request):
        """Obtener medicamentos vencidos"""
        expired_medications = self.get_queryset().filter(
            expiration_date__lt=date.today(),
            is_active=True
        )
        
        serializer = MedicationListSerializer(expired_medications, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """Obtener medicamentos que vencen pronto"""
        days_ahead = int(request.query_params.get('days', 30))
        limit_date = date.today() + timedelta(days=days_ahead)
        
        expiring_medications = self.get_queryset().filter(
            expiration_date__lte=limit_date,
            expiration_date__gte=date.today(),
            is_active=True
        )
        
        serializer = MedicationListSerializer(expiring_medications, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def adjust_stock(self, request, pk=None):
        """Ajustar stock de un medicamento"""
        medication = self.get_object()
        
        # Verificar permisos
        if request.user.get('role') not in ['Admin', 'Recepcionista']:
            return Response(
                {'error': 'Solo administradores y recepcionistas pueden ajustar stock'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        new_stock = request.data.get('new_stock')
        reason = request.data.get('reason', 'Ajuste manual')
        
        if new_stock is None:
            return Response(
                {'error': 'Se requiere especificar el nuevo stock'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            new_stock = int(new_stock)
            if new_stock < 0:
                raise ValueError()
        except (ValueError, TypeError):
            return Response(
                {'error': 'El stock debe ser un número entero positivo'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calcular diferencia
        current_stock = medication.current_stock
        quantity_difference = new_stock - current_stock
        
        # Crear movimiento de stock
        movement_data = {
            'medication': medication.id,
            'movement_type': 'AJUSTE',
            'quantity': quantity_difference,
            'reason': reason,
            'notes': f'Ajuste de stock de {current_stock} a {new_stock}'
        }
        
        movement_serializer = StockMovementSerializer(data=movement_data, context={'request': request})
        if movement_serializer.is_valid():
            movement_serializer.save()
            
            # Actualizar stock del medicamento
            medication.current_stock = new_stock
            medication.save()
            
            serializer = self.get_serializer(medication)
            return Response({
                'medication': serializer.data,
                'movement': movement_serializer.data
            })
        
        return Response(movement_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def inventory_report(self, request):
        """Reporte de inventario"""
        medications = self.get_queryset()
        
        # Calcular estadísticas
        total_medications = medications.count()
        active_medications = medications.filter(is_active=True).count()
        low_stock_count = medications.filter(
            current_stock__lte=models.F('minimum_stock'),
            is_active=True
        ).count()
        expired_count = medications.filter(
            expiration_date__lt=date.today(),
            is_active=True
        ).count()
        
        # Calcular valor total del inventario
        total_value = sum(
            med.current_stock * med.unit_price 
            for med in medications.filter(is_active=True)
        )
        
        report_data = {
            'generated_at': date.today(),
            'statistics': {
                'total_medications': total_medications,
                'active_medications': active_medications,
                'low_stock_count': low_stock_count,
                'expired_count': expired_count,
                'total_inventory_value': total_value
            },
            'low_stock_medications': MedicationListSerializer(
                medications.filter(current_stock__lte=models.F('minimum_stock'), is_active=True),
                many=True
            ).data,
            'expired_medications': MedicationListSerializer(
                medications.filter(expiration_date__lt=date.today(), is_active=True),
                many=True
            ).data
        }
        
        return Response(report_data)

class StockMovementViewSet(viewsets.ModelViewSet):
    queryset = StockMovement.objects.all()
    serializer_class = StockMovementSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['medication', 'movement_type', 'created_by', 'prescription_id']
    ordering = ['-created_at']

    def get_queryset(self):
        """Filtrar movimientos por medicamento si se especifica"""
        queryset = super().get_queryset()
        medication_id = self.request.query_params.get('medication_id')
        
        if medication_id:
            queryset = queryset.filter(medication_id=medication_id)
        
        # Filtrar por rango de fechas
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)
        
        return queryset

    @action(detail=False, methods=['get'])
    def by_medication(self, request):
        """Obtener movimientos de un medicamento específico"""
        medication_id = request.query_params.get('medication_id')
        
        if not medication_id:
            return Response(
                {'error': 'Se requiere el parámetro medication_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        movements = self.get_queryset().filter(medication_id=medication_id)
        serializer = self.get_serializer(movements, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def sales_report(self, request):
        """Reporte de ventas (movimientos de salida)"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            return Response(
                {'error': 'Se requieren los parámetros start_date y end_date'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        sales_movements = self.get_queryset().filter(
            movement_type='VENTA',
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )
        
        # Calcular estadísticas
        total_sales = sales_movements.count()
        total_amount = sum(
            abs(movement.quantity) * movement.unit_cost
            for movement in sales_movements
            if movement.unit_cost
        )
        
        # Agrupar por medicamento
        medications_sold = sales_movements.values(
            'medication__name'
        ).annotate(
            total_quantity=Sum('quantity'),
            total_sales=Count('id')
        ).order_by('-total_quantity')
        
        report_data = {
            'period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'statistics': {
                'total_sales': total_sales,
                'total_amount': total_amount
            },
            'medications_sold': list(medications_sold),
            'sales_movements': StockMovementSerializer(sales_movements, many=True).data
        }
        
        return Response(report_data) 