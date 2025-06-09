from rest_framework import serializers
from .models import Patient, Vaccination
from owners.serializers import OwnerListSerializer

class PatientSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    age_in_years = serializers.ReadOnlyField()
    is_alive = serializers.ReadOnlyField()
    
    class Meta:
        model = Patient
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate_microchip_number(self, value):
        """Validar que el número de microchip no esté duplicado"""
        if value and Patient.objects.filter(microchip_number=value).exists():
            if not self.instance or self.instance.microchip_number != value:
                raise serializers.ValidationError("Ya existe un paciente con este número de microchip")
        return value

    def validate(self, data):
        """Validaciones personalizadas"""
        if data.get('date_of_death') and data.get('birth_date'):
            if data['date_of_death'] < data['birth_date']:
                raise serializers.ValidationError({
                    'date_of_death': 'La fecha de fallecimiento no puede ser anterior a la fecha de nacimiento'
                })
        return data

class PatientCreateSerializer(PatientSerializer):
    class Meta(PatientSerializer.Meta):
        extra_kwargs = {
            'name': {'required': True},
            'species': {'required': True},
            'breed': {'required': True},
            'gender': {'required': True},
            'color': {'required': True},
            'birth_date': {'required': True},
            'weight': {'required': True},
            'owner': {'required': True},
        }

class PatientListSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    owner_document = serializers.CharField(source='owner.document_number', read_only=True)
    age_in_years = serializers.ReadOnlyField()
    is_alive = serializers.ReadOnlyField()
    
    class Meta:
        model = Patient
        fields = ('id', 'name', 'species', 'breed', 'gender', 'age_in_years', 
                 'weight', 'owner_name', 'owner_document', 'is_alive', 
                 'microchip_number', 'created_at')

class PatientDetailSerializer(PatientSerializer):
    owner = OwnerListSerializer(read_only=True)
    vaccinations = serializers.SerializerMethodField()
    
    class Meta(PatientSerializer.Meta):
        pass
    
    def get_vaccinations(self, obj):
        recent_vaccinations = obj.vaccinations.all()[:5]
        return VaccinationSerializer(recent_vaccinations, many=True).data

class VaccinationSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    
    class Meta:
        model = Vaccination
        fields = '__all__'
        read_only_fields = ('id', 'created_at')

class VaccinationCreateSerializer(VaccinationSerializer):
    class Meta(VaccinationSerializer.Meta):
        extra_kwargs = {
            'patient': {'required': True},
            'vaccine_name': {'required': True},
            'vaccination_date': {'required': True},
            'veterinarian': {'required': True},
        } 