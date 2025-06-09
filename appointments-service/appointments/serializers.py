from rest_framework import serializers
from django.conf import settings
from datetime import datetime, timedelta
import requests
from .models import Appointment, VeterinarianSchedule, AppointmentBlock

class AppointmentSerializer(serializers.ModelSerializer):
    end_time = serializers.ReadOnlyField()
    is_past = serializers.ReadOnlyField()
    patient_name = serializers.CharField(read_only=True)
    owner_name = serializers.CharField(read_only=True)
    veterinarian_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = Appointment
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'reminder_sent')

    def validate(self, data):
        """Validaciones complejas de citas"""
        appointment_date = data.get('appointment_date')
        appointment_time = data.get('appointment_time')
        veterinarian_id = data.get('veterinarian_id')
        patient_id = data.get('patient_id')
        duration_minutes = data.get('duration_minutes', 30)

        if appointment_date and appointment_time and veterinarian_id:
            # Verificar disponibilidad del veterinario
            self._validate_veterinarian_availability(
                veterinarian_id, appointment_date, appointment_time, duration_minutes
            )
            
            # Verificar que no haya otra cita para el mismo paciente en el mismo horario
            self._validate_patient_availability(
                patient_id, appointment_date, appointment_time
            )

        return data

    def _validate_veterinarian_availability(self, vet_id, date, time, duration):
        """Validar que el veterinario esté disponible"""
        # Verificar horario de trabajo del veterinario
        day_name = date.strftime('%A').upper()
        day_mapping = {
            'MONDAY': 'LUNES', 'TUESDAY': 'MARTES', 'WEDNESDAY': 'MIERCOLES',
            'THURSDAY': 'JUEVES', 'FRIDAY': 'VIERNES', 'SATURDAY': 'SABADO', 'SUNDAY': 'DOMINGO'
        }
        
        try:
            schedule = VeterinarianSchedule.objects.get(
                veterinarian_id=vet_id,
                day_of_week=day_mapping[day_name],
                is_active=True
            )
            
            if not (schedule.start_time <= time <= schedule.end_time):
                raise serializers.ValidationError({
                    'appointment_time': f'El veterinario no está disponible a esta hora. Horario: {schedule.start_time}-{schedule.end_time}'
                })
        except VeterinarianSchedule.DoesNotExist:
            raise serializers.ValidationError({
                'veterinarian_id': 'El veterinario no tiene horario configurado para este día'
            })

        # Verificar bloqueos de horario
        appointment_datetime = datetime.combine(date, time)
        end_datetime = appointment_datetime + timedelta(minutes=duration)
        
        blocks = AppointmentBlock.objects.filter(
            veterinarian_id=vet_id,
            is_active=True,
            start_datetime__lt=end_datetime,
            end_datetime__gt=appointment_datetime
        )
        
        if blocks.exists():
            raise serializers.ValidationError({
                'appointment_time': 'El veterinario tiene el horario bloqueado en este momento'
            })

        # Verificar conflictos con otras citas
        conflicting_appointments = Appointment.objects.filter(
            veterinarian_id=vet_id,
            appointment_date=date,
            status__in=['AGENDADA', 'CONFIRMADA', 'EN_PROGRESO']
        ).exclude(id=self.instance.id if self.instance else None)

        for apt in conflicting_appointments:
            existing_start = datetime.combine(apt.appointment_date, apt.appointment_time)
            existing_end = existing_start + timedelta(minutes=apt.duration_minutes)
            
            if not (end_datetime <= existing_start or appointment_datetime >= existing_end):
                raise serializers.ValidationError({
                    'appointment_time': f'Conflicto con cita existente de {apt.appointment_time} a {apt.end_time}'
                })

    def _validate_patient_availability(self, patient_id, date, time):
        """Validar que el paciente no tenga otra cita al mismo tiempo"""
        conflicting = Appointment.objects.filter(
            patient_id=patient_id,
            appointment_date=date,
            appointment_time=time,
            status__in=['AGENDADA', 'CONFIRMADA', 'EN_PROGRESO']
        ).exclude(id=self.instance.id if self.instance else None)

        if conflicting.exists():
            raise serializers.ValidationError({
                'appointment_time': 'El paciente ya tiene una cita agendada a esta hora'
            })

class AppointmentCreateSerializer(AppointmentSerializer):
    class Meta(AppointmentSerializer.Meta):
        extra_kwargs = {
            'patient_id': {'required': True},
            'owner_id': {'required': True},
            'veterinarian_id': {'required': True},
            'appointment_date': {'required': True},
            'appointment_time': {'required': True},
            'reason': {'required': True},
            'contact_phone': {'required': True},
        }

class AppointmentListSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(read_only=True)
    owner_name = serializers.CharField(read_only=True)
    veterinarian_name = serializers.CharField(read_only=True)
    end_time = serializers.ReadOnlyField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    class Meta:
        model = Appointment
        fields = (
            'id', 'patient_id', 'patient_name', 'owner_name', 'veterinarian_name',
            'appointment_date', 'appointment_time', 'end_time', 'duration_minutes',
            'appointment_type', 'status', 'status_display', 'priority', 'priority_display',
            'reason', 'contact_phone', 'created_at'
        )

class VeterinarianScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = VeterinarianSchedule
        fields = '__all__'
        read_only_fields = ('id', 'created_at')

    def validate(self, data):
        if data['start_time'] >= data['end_time']:
            raise serializers.ValidationError({
                'end_time': 'La hora de fin debe ser posterior a la hora de inicio'
            })
        return data

class AppointmentBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointmentBlock
        fields = '__all__'
        read_only_fields = ('id', 'created_at')

    def validate(self, data):
        if data['start_datetime'] >= data['end_datetime']:
            raise serializers.ValidationError({
                'end_datetime': 'La fecha de fin debe ser posterior a la fecha de inicio'
            })
        return data

class AgendaSerializer(serializers.Serializer):
    """Serializer para mostrar la agenda de un veterinario"""
    date = serializers.DateField()
    veterinarian_id = serializers.IntegerField()
    appointments = AppointmentListSerializer(many=True, read_only=True)
    available_slots = serializers.ListField(child=serializers.TimeField(), read_only=True)
    blocked_periods = serializers.ListField(read_only=True) 