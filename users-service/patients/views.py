from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from .models import Patient, Vaccination
from .serializers import (
    PatientSerializer, PatientCreateSerializer, PatientListSerializer,
    PatientDetailSerializer, VaccinationSerializer, VaccinationCreateSerializer
)

class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.filter(is_active=True)
    serializer_class = PatientSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['species', 'gender', 'size', 'is_neutered', 'owner', 'is_alive']
    search_fields = ['name', 'breed', 'microchip_number', 'owner__first_name', 'owner__last_name', 'owner__document_number']
    ordering_fields = ['created_at', 'name', 'birth_date', 'weight']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return PatientListSerializer
        elif self.action == 'create':
            return PatientCreateSerializer
        elif self.action == 'retrieve':
            return PatientDetailSerializer
        return PatientSerializer

    def perform_destroy(self, instance):
        """Soft delete - marcar como inactivo en lugar de eliminar"""
        instance.is_active = False
        instance.save()

    @action(detail=True, methods=['get'])
    def vaccinations(self, request, pk=None):
        """Obtener todas las vacunaciones de un paciente"""
        patient = self.get_object()
        vaccinations = patient.vaccinations.all()
        serializer = VaccinationSerializer(vaccinations, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_vaccination(self, request, pk=None):
        """Agregar una nueva vacunación a un paciente"""
        patient = self.get_object()
        data = request.data.copy()
        data['patient'] = patient.id
        
        serializer = VaccinationCreateSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def search_by_microchip(self, request):
        """Buscar paciente por número de microchip"""
        microchip_number = request.query_params.get('microchip_number')
        if not microchip_number:
            return Response(
                {'error': 'Se requiere el parámetro microchip_number'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            patient = Patient.objects.get(microchip_number=microchip_number, is_active=True)
            serializer = PatientDetailSerializer(patient)
            return Response(serializer.data)
        except Patient.DoesNotExist:
            return Response(
                {'error': 'Paciente no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def by_owner(self, request):
        """Obtener pacientes por propietario"""
        owner_id = request.query_params.get('owner_id')
        if not owner_id:
            return Response(
                {'error': 'Se requiere el parámetro owner_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        patients = self.get_queryset().filter(owner_id=owner_id)
        serializer = PatientListSerializer(patients, many=True)
        return Response(serializer.data)

class VaccinationViewSet(viewsets.ModelViewSet):
    queryset = Vaccination.objects.all()
    serializer_class = VaccinationSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['patient', 'vaccine_name', 'veterinarian']
    search_fields = ['vaccine_name', 'veterinarian', 'patient__name']
    ordering_fields = ['vaccination_date', 'created_at']
    ordering = ['-vaccination_date']

    def get_serializer_class(self):
        if self.action == 'create':
            return VaccinationCreateSerializer
        return VaccinationSerializer 