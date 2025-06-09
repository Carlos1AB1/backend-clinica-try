from rest_framework import serializers
from .models import Consultation, ConsultationProcedure, ConsultationNote, Treatment

class ConsultationNoteSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = ConsultationNote
        fields = '__all__'
        read_only_fields = ('created_at', 'created_by')

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user.get('id', 0)
        return super().create(validated_data)

class ConsultationProcedureSerializer(serializers.ModelSerializer):
    performed_by_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = ConsultationProcedure
        fields = '__all__'
        read_only_fields = ('performed_at',)

class TreatmentSerializer(serializers.ModelSerializer):
    prescribed_by_name = serializers.CharField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Treatment
        fields = '__all__'
        read_only_fields = ('created_at', 'prescribed_by')

    def create(self, validated_data):
        validated_data['prescribed_by'] = self.context['request'].user.get('id', 0)
        return super().create(validated_data)

    def validate(self, data):
        if data.get('end_date') and data.get('start_date'):
            if data['end_date'] < data['start_date']:
                raise serializers.ValidationError({
                    'end_date': 'La fecha de finalización debe ser posterior a la fecha de inicio'
                })
        return data

class ConsultationListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados"""
    consultation_type_display = serializers.CharField(source='get_consultation_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    veterinarian_name = serializers.CharField(read_only=True)
    patient_name = serializers.CharField(read_only=True)
    procedures_count = serializers.SerializerMethodField()
    treatments_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Consultation
        fields = (
            'id', 'consultation_date', 'consultation_type', 'consultation_type_display',
            'status', 'status_display', 'veterinarian_id', 'veterinarian_name',
            'patient_name', 'chief_complaint', 'primary_diagnosis',
            'follow_up_required', 'follow_up_date', 'procedures_count', 'treatments_count'
        )

    def get_procedures_count(self, obj):
        return obj.procedures.count()

    def get_treatments_count(self, obj):
        return obj.treatments.count()

class ConsultationDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado para vista individual"""
    consultation_type_display = serializers.CharField(source='get_consultation_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    veterinarian_name = serializers.CharField(read_only=True)
    patient_name = serializers.CharField(read_only=True)
    procedures = ConsultationProcedureSerializer(many=True, read_only=True)
    notes = ConsultationNoteSerializer(many=True, read_only=True)
    treatments = TreatmentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Consultation
        fields = '__all__'
        read_only_fields = ('consultation_date', 'updated_at')

class ConsultationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consultation
        fields = '__all__'
        read_only_fields = ('consultation_date', 'updated_at')

    def validate(self, data):
        """Validaciones para creación de consulta"""
        user = self.context['request'].user
        
        # Solo veterinarios pueden crear consultas
        if user.get('role') != 'Veterinario':
            raise serializers.ValidationError('Solo los veterinarios pueden crear consultas')
        
        # Validar que la historia clínica exista
        from medical_records.models import MedicalRecord
        try:
            medical_record = MedicalRecord.objects.get(id=data['medical_record'].id)
            if not medical_record.is_active:
                raise serializers.ValidationError('No se pueden crear consultas en historias clínicas inactivas')
        except MedicalRecord.DoesNotExist:
            raise serializers.ValidationError('La historia clínica especificada no existe')
        
        return data

class ConsultationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consultation
        fields = (
            'consultation_type', 'status', 'history_present_illness',
            'physical_examination', 'primary_diagnosis', 'secondary_diagnosis',
            'differential_diagnosis', 'treatment_plan', 'medications_prescribed',
            'recommendations', 'follow_up_required', 'follow_up_date',
            'follow_up_notes', 'prognosis', 'client_education', 'duration_minutes'
        )

    def validate(self, data):
        """Validaciones para actualización"""
        user = self.context['request'].user
        
        # Solo el veterinario que creó la consulta o administradores pueden editarla
        if (user.get('role') not in ['Admin', 'Veterinario'] or 
            (user.get('role') == 'Veterinario' and self.instance.veterinarian_id != user.get('id'))):
            raise serializers.ValidationError('No tiene permisos para editar esta consulta')
        
        # No permitir cambios si la consulta está completada
        if self.instance.status == 'COMPLETADA' and user.get('role') != 'Admin':
            raise serializers.ValidationError('No se pueden editar consultas completadas')
        
        return data 