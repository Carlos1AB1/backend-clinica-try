from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from .models import Owner
from .serializers import OwnerSerializer, OwnerCreateSerializer, OwnerListSerializer

class OwnerViewSet(viewsets.ModelViewSet):
    queryset = Owner.objects.filter(is_active=True)
    serializer_class = OwnerSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['document_type', 'city', 'is_active']
    search_fields = ['first_name', 'last_name', 'document_number', 'email']
    ordering_fields = ['created_at', 'first_name', 'last_name']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return OwnerListSerializer
        elif self.action == 'create':
            return OwnerCreateSerializer
        return OwnerSerializer

    def perform_destroy(self, instance):
        """Soft delete - marcar como inactivo en lugar de eliminar"""
        instance.is_active = False
        instance.save()

    @action(detail=True, methods=['get'])
    def patients(self, request, pk=None):
        """Obtener todos los pacientes de un propietario"""
        owner = self.get_object()
        patients = owner.patients.filter(is_active=True)
        
        from patients.serializers import PatientListSerializer
        serializer = PatientListSerializer(patients, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def search_by_document(self, request):
        """Buscar propietario por número de documento"""
        document_number = request.query_params.get('document_number')
        if not document_number:
            return Response(
                {'error': 'Se requiere el parámetro document_number'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            owner = Owner.objects.get(document_number=document_number, is_active=True)
            serializer = self.get_serializer(owner)
            return Response(serializer.data)
        except Owner.DoesNotExist:
            return Response(
                {'error': 'Propietario no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            ) 