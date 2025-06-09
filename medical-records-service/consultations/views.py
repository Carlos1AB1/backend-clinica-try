from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from datetime import datetime, timedelta
from .models import Consultation, ConsultationProcedure, ConsultationNote, Treatment
from .serializers import (
    ConsultationListSerializer, ConsultationDetailSerializer,
    ConsultationCreateSerializer, ConsultationUpdateSerializer,
    ConsultationProcedureSerializer, ConsultationNoteSerializer, TreatmentSerializer
)

class ConsultationViewSet(viewsets.ModelViewSet):
    queryset = Consultation.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'medical_record', 'veterinarian_id', 'consultation_type', 'status',
        'follow_up_required', 'appointment_id'
    ]
    search_fields = [
        'chief_complaint', 'primary_diagnosis', 'secondary_diagnosis',
        'treatment_plan', 'recommendations'
    ]
    ordering_fields = ['consultation_date', 'updated_at']
    ordering = ['-consultation_date']

    def get_serializer_class(self):
        if self.action == 'list':
            return ConsultationListSerializer
        elif self.action == 'retrieve':
            return ConsultationDetailSerializer
        elif self.action == 'create':
            return ConsultationCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ConsultationUpdateSerializer
        return ConsultationDetailSerializer

    def get_queryset(self):
        """Personalizar queryset según rol del usuario"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Los veterinarios solo ven sus propias consultas
        if user.get('role') == 'Veterinario':
            queryset = queryset.filter(veterinarian_id=user.get('id'))
        
        # Filtrar por rango de fechas
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(consultation_date__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(consultation_date__date__lte=end_date)
        
        return queryset

    def create(self, request, *args, **kwargs):
        """Crear consulta asignando el veterinario automáticamente"""
        data = request.data.copy()
        data['veterinarian_id'] = request.user.get('id')
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Marcar consulta como completada"""
        consultation = self.get_object()
        
        # Verificar permisos
        if (request.user.get('role') != 'Admin' and 
            consultation.veterinarian_id != request.user.get('id')):
            return Response(
                {'error': 'No tiene permisos para completar esta consulta'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if consultation.status == 'COMPLETADA':
            return Response(
                {'error': 'La consulta ya está completada'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        consultation.status = 'COMPLETADA'
        consultation.save()
        
        serializer = self.get_serializer(consultation)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_note(self, request, pk=None):
        """Agregar nota a la consulta"""
        consultation = self.get_object()
        
        data = request.data.copy()
        data['consultation'] = consultation.id
        
        serializer = ConsultationNoteSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def add_procedure(self, request, pk=None):
        """Agregar procedimiento a la consulta"""
        consultation = self.get_object()
        
        data = request.data.copy()
        data['consultation'] = consultation.id
        data['performed_by'] = request.user.get('id')
        
        serializer = ConsultationProcedureSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def add_treatment(self, request, pk=None):
        """Agregar tratamiento a la consulta"""
        consultation = self.get_object()
        
        data = request.data.copy()
        data['consultation'] = consultation.id
        
        serializer = TreatmentSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def my_consultations(self, request):
        """Obtener consultas del veterinario autenticado"""
        if request.user.get('role') != 'Veterinario':
            return Response(
                {'error': 'Solo los veterinarios pueden acceder a sus consultas'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        consultations = self.get_queryset().filter(veterinarian_id=request.user.get('id'))
        
        # Filtros adicionales
        status_filter = request.query_params.get('status')
        if status_filter:
            consultations = consultations.filter(status=status_filter)
        
        page = self.paginate_queryset(consultations)
        if page is not None:
            serializer = ConsultationListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ConsultationListSerializer(consultations, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def follow_ups_due(self, request):
        """Obtener consultas que requieren seguimiento"""
        today = datetime.now().date()
        week_ahead = today + timedelta(days=7)
        
        follow_ups = self.get_queryset().filter(
            follow_up_required=True,
            follow_up_date__lte=week_ahead,
            status='COMPLETADA'
        )
        
        serializer = ConsultationListSerializer(follow_ups, many=True)
        return Response(serializer.data)

class ConsultationProcedureViewSet(viewsets.ModelViewSet):
    queryset = ConsultationProcedure.objects.all()
    serializer_class = ConsultationProcedureSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['consultation', 'performed_by']
    ordering = ['-performed_at']

class ConsultationNoteViewSet(viewsets.ModelViewSet):
    queryset = ConsultationNote.objects.all()
    serializer_class = ConsultationNoteSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['consultation', 'note_type', 'is_important', 'created_by']
    ordering = ['-created_at']

class TreatmentViewSet(viewsets.ModelViewSet):
    queryset = Treatment.objects.all()
    serializer_class = TreatmentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['consultation', 'status', 'prescribed_by']
    search_fields = ['treatment_name', 'medication_name', 'description']
    ordering = ['-created_at']

    @action(detail=True, methods=['post'])
    def complete_treatment(self, request, pk=None):
        """Marcar tratamiento como completado"""
        treatment = self.get_object()
        
        if treatment.status == 'COMPLETADO':
            return Response(
                {'error': 'El tratamiento ya está completado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        treatment.status = 'COMPLETADO'
        treatment.end_date = datetime.now().date()
        treatment.save()
        
        serializer = self.get_serializer(treatment)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def discontinue_treatment(self, request, pk=None):
        """Descontinuar tratamiento"""
        treatment = self.get_object()
        
        reason = request.data.get('reason', '')
        if not reason:
            return Response(
                {'error': 'Se requiere especificar la razón para descontinuar'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        treatment.status = 'DESCONTINUADO'
        treatment.end_date = datetime.now().date()
        treatment.special_instructions += f"\n\nDescontinuado: {reason}"
        treatment.save()
        
        serializer = self.get_serializer(treatment)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def active_treatments(self, request):
        """Obtener tratamientos activos"""
        patient_id = request.query_params.get('patient_id')
        
        active_treatments = self.get_queryset().filter(
            status__in=['PRESCRITO', 'EN_PROGRESO']
        )
        
        if patient_id:
            active_treatments = active_treatments.filter(
                consultation__medical_record__patient_id=patient_id
            )
        
        serializer = self.get_serializer(active_treatments, many=True)
        return Response(serializer.data) 