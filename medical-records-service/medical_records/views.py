from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse, Http404
from .models import MedicalRecord, MedicalFile, VitalSigns
from .serializers import (
    MedicalRecordListSerializer, MedicalRecordDetailSerializer,
    MedicalRecordCreateSerializer, MedicalRecordUpdateSerializer,
    MedicalFileSerializer, VitalSignsSerializer
)

class MedicalRecordViewSet(viewsets.ModelViewSet):
    queryset = MedicalRecord.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['patient_id', 'owner_id', 'is_active', 'created_by']
    search_fields = ['allergies', 'chronic_conditions', 'current_medications']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return MedicalRecordListSerializer
        elif self.action == 'retrieve':
            return MedicalRecordDetailSerializer
        elif self.action == 'create':
            return MedicalRecordCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return MedicalRecordUpdateSerializer
        return MedicalRecordDetailSerializer

    def get_queryset(self):
        """Personalizar queryset según rol del usuario"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Los veterinarios solo ven historias de sus pacientes
        if user.get('role') == 'Veterinario':
            # Aquí podrías filtrar por las consultas del veterinario
            pass
        
        return queryset

    def destroy(self, request, *args, **kwargs):
        """Prevenir eliminación de historias clínicas"""
        return Response(
            {'error': 'Las historias clínicas no pueden ser eliminadas por seguridad.'},
            status=status.HTTP_403_FORBIDDEN
        )

    @action(detail=True, methods=['get'])
    def by_patient(self, request, pk=None):
        """Obtener historia clínica por ID del paciente"""
        try:
            medical_record = MedicalRecord.objects.get(patient_id=pk)
            serializer = MedicalRecordDetailSerializer(medical_record, context={'request': request})
            return Response(serializer.data)
        except MedicalRecord.DoesNotExist:
            return Response(
                {'error': 'No se encontró historia clínica para este paciente'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def add_vital_signs(self, request, pk=None):
        """Agregar signos vitales a la historia clínica"""
        medical_record = self.get_object()
        
        data = request.data.copy()
        data['medical_record'] = medical_record.id
        
        serializer = VitalSignsSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def vital_signs_history(self, request, pk=None):
        """Obtener historial de signos vitales"""
        medical_record = self.get_object()
        vital_signs = medical_record.vital_signs.all()
        
        # Filtrar por fecha si se especifica
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            vital_signs = vital_signs.filter(recorded_at__date__gte=start_date)
        if end_date:
            vital_signs = vital_signs.filter(recorded_at__date__lte=end_date)
        
        serializer = VitalSignsSerializer(vital_signs, many=True)
        return Response(serializer.data)

class MedicalFileViewSet(viewsets.ModelViewSet):
    queryset = MedicalFile.objects.all()
    serializer_class = MedicalFileSerializer
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['medical_record', 'file_type', 'uploaded_by']
    ordering = ['-uploaded_at']

    def get_queryset(self):
        """Filtrar archivos por historia clínica si se especifica"""
        queryset = super().get_queryset()
        medical_record_id = self.request.query_params.get('medical_record_id')
        
        if medical_record_id:
            queryset = queryset.filter(medical_record_id=medical_record_id)
        
        return queryset

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Descargar archivo médico"""
        try:
            medical_file = self.get_object()
            
            # Verificar permisos de acceso
            user = request.user
            if user.get('role') not in ['Admin', 'Veterinario']:
                return Response(
                    {'error': 'No tiene permisos para descargar este archivo'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            response = HttpResponse(
                medical_file.file.read(),
                content_type='application/octet-stream'
            )
            response['Content-Disposition'] = f'attachment; filename="{medical_file.title}"'
            return response
            
        except Exception as e:
            return Response(
                {'error': 'Error al descargar el archivo'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class VitalSignsViewSet(viewsets.ModelViewSet):
    queryset = VitalSigns.objects.all()
    serializer_class = VitalSignsSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['medical_record', 'recorded_by', 'consultation_id']
    ordering = ['-recorded_at']

    def get_queryset(self):
        """Filtrar signos vitales por historia clínica"""
        queryset = super().get_queryset()
        medical_record_id = self.request.query_params.get('medical_record_id')
        
        if medical_record_id:
            queryset = queryset.filter(medical_record_id=medical_record_id)
        
        return queryset

    @action(detail=False, methods=['get'])
    def latest_by_patient(self, request):
        """Obtener los últimos signos vitales de un paciente"""
        patient_id = request.query_params.get('patient_id')
        
        if not patient_id:
            return Response(
                {'error': 'Se requiere el parámetro patient_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            medical_record = MedicalRecord.objects.get(patient_id=patient_id)
            latest_vital_signs = medical_record.vital_signs.first()
            
            if latest_vital_signs:
                serializer = VitalSignsSerializer(latest_vital_signs)
                return Response(serializer.data)
            else:
                return Response(
                    {'message': 'No se encontraron signos vitales para este paciente'},
                    status=status.HTTP_204_NO_CONTENT
                )
                
        except MedicalRecord.DoesNotExist:
            return Response(
                {'error': 'No se encontró historia clínica para este paciente'},
                status=status.HTTP_404_NOT_FOUND
            ) 