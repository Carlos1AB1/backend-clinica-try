from rest_framework import serializers
from django.conf import settings
from .models import MedicalRecord, MedicalFile, VitalSigns

class MedicalFileSerializer(serializers.ModelSerializer):
    file_size_mb = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = MedicalFile
        fields = '__all__'
        read_only_fields = ('file_size', 'uploaded_at', 'uploaded_by')

    def get_file_size_mb(self, obj):
        """Convertir tamaño a MB para mejor legibilidad"""
        return round(obj.file_size / (1024 * 1024), 2) if obj.file_size else 0

    def get_file_url(self, obj):
        """Obtener URL completa del archivo"""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None

    def validate_file(self, file):
        """Validar tamaño y tipo de archivo"""
        if file.size > settings.MAX_FILE_SIZE:
            raise serializers.ValidationError(
                f'El archivo es demasiado grande. Máximo permitido: {settings.MAX_FILE_SIZE / (1024 * 1024):.1f}MB'
            )
        
        extension = file.name.split('.')[-1].lower()
        if extension not in settings.ALLOWED_FILE_EXTENSIONS:
            raise serializers.ValidationError(
                f'Tipo de archivo no permitido. Tipos permitidos: {", ".join(settings.ALLOWED_FILE_EXTENSIONS)}'
            )
        
        return file

    def create(self, validated_data):
        """Agregar el usuario que sube el archivo"""
        validated_data['uploaded_by'] = self.context['request'].user.get('id', 0)
        return super().create(validated_data)

class VitalSignsSerializer(serializers.ModelSerializer):
    bmi = serializers.SerializerMethodField()
    
    class Meta:
        model = VitalSigns
        fields = '__all__'
        read_only_fields = ('recorded_at', 'recorded_by')

    def get_bmi(self, obj):
        """Calcular índice de masa corporal si hay peso registrado"""
        if obj.weight:
            # Para animales, usamos una escala diferente
            return obj.body_condition_score if obj.body_condition_score else None
        return None

    def create(self, validated_data):
        """Agregar el usuario que registra los signos vitales"""
        validated_data['recorded_by'] = self.context['request'].user.get('id', 0)
        return super().create(validated_data)

class MedicalRecordListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados"""
    files_count = serializers.SerializerMethodField()
    consultations_count = serializers.SerializerMethodField()
    last_consultation = serializers.SerializerMethodField()
    latest_vital_signs = VitalSignsSerializer(read_only=True)
    
    class Meta:
        model = MedicalRecord
        fields = (
            'id', 'patient_id', 'owner_id', 'created_at', 'updated_at',
            'allergies', 'chronic_conditions', 'is_active',
            'files_count', 'consultations_count', 'last_consultation',
            'latest_vital_signs'
        )

    def get_files_count(self, obj):
        return obj.files.count()

    def get_consultations_count(self, obj):
        return obj.consultations.count()

    def get_last_consultation(self, obj):
        last_consultation = obj.consultations.first()
        if last_consultation:
            return {
                'id': last_consultation.id,
                'date': last_consultation.consultation_date,
                'type': last_consultation.get_consultation_type_display(),
                'diagnosis': last_consultation.primary_diagnosis[:100] + '...' if len(last_consultation.primary_diagnosis) > 100 else last_consultation.primary_diagnosis
            }
        return None

class MedicalRecordDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado para vista individual"""
    files = MedicalFileSerializer(many=True, read_only=True)
    vital_signs = VitalSignsSerializer(many=True, read_only=True)
    consultations_count = serializers.SerializerMethodField()
    patient_name = serializers.CharField(read_only=True)
    owner_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = MedicalRecord
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'created_by')

    def get_consultations_count(self, obj):
        return obj.consultations.count()

class MedicalRecordCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalRecord
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'created_by')

    def validate_patient_id(self, value):
        """Validar que no exista ya una historia clínica para este paciente"""
        if MedicalRecord.objects.filter(patient_id=value).exists():
            raise serializers.ValidationError('Ya existe una historia clínica para este paciente')
        return value

    def create(self, validated_data):
        """Agregar el usuario que crea la historia clínica"""
        validated_data['created_by'] = self.context['request'].user.get('id', 0)
        return super().create(validated_data)

class MedicalRecordUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalRecord
        fields = (
            'allergies', 'chronic_conditions', 'current_medications',
            'blood_type', 'microchip_number', 'emergency_contact',
            'emergency_notes', 'is_active'
        )

    def validate(self, data):
        """Validaciones adicionales para actualización"""
        # No permitir desactivar si hay consultas activas
        if 'is_active' in data and not data['is_active']:
            active_consultations = self.instance.consultations.filter(status='EN_PROGRESO').count()
            if active_consultations > 0:
                raise serializers.ValidationError(
                    'No se puede desactivar la historia clínica con consultas activas'
                )
        return data 