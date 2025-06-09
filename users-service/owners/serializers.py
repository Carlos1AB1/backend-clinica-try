from rest_framework import serializers
from .models import Owner

class OwnerSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = Owner
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate_document_number(self, value):
        """Validar que el número de documento no esté duplicado"""
        if Owner.objects.filter(document_number=value).exists():
            if not self.instance or self.instance.document_number != value:
                raise serializers.ValidationError("Ya existe un propietario con este número de documento")
        return value

    def validate_email(self, value):
        """Validar que el email no esté duplicado"""
        if Owner.objects.filter(email=value).exists():
            if not self.instance or self.instance.email != value:
                raise serializers.ValidationError("Ya existe un propietario con este correo electrónico")
        return value

class OwnerCreateSerializer(OwnerSerializer):
    class Meta(OwnerSerializer.Meta):
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True},
            'phone': {'required': True},
            'address': {'required': True},
            'city': {'required': True},
        }

class OwnerListSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    patients_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Owner
        fields = ('id', 'document_type', 'document_number', 'full_name', 
                 'email', 'phone', 'city', 'patients_count', 'is_active', 'created_at')

    def get_patients_count(self, obj):
        return obj.patients.filter(is_active=True).count() 