from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from medical_records.models import MedicalRecord

class Consultation(models.Model):
    """Consultas médicas registradas por veterinarios"""
    
    class ConsultationType(models.TextChoices):
        GENERAL = 'GENERAL', _('Consulta General')
        EMERGENCY = 'EMERGENCIA', _('Emergencia')
        FOLLOW_UP = 'SEGUIMIENTO', _('Seguimiento')
        VACCINATION = 'VACUNACION', _('Vacunación')
        SURGERY = 'CIRUGIA', _('Cirugía')
        DENTAL = 'DENTAL', _('Dental')
        DERMATOLOGY = 'DERMATOLOGIA', _('Dermatología')
        OPHTHALMOLOGY = 'OFTALMOLOGIA', _('Oftalmología')
        CARDIOLOGY = 'CARDIOLOGIA', _('Cardiología')
        ORTHOPEDICS = 'ORTOPEDIA', _('Ortopedia')

    class Status(models.TextChoices):
        IN_PROGRESS = 'EN_PROGRESO', _('En Progreso')
        COMPLETED = 'COMPLETADA', _('Completada')
        CANCELLED = 'CANCELADA', _('Cancelada')

    # Relación con historia clínica
    medical_record = models.ForeignKey(
        MedicalRecord, 
        on_delete=models.CASCADE, 
        related_name='consultations',
        verbose_name=_('Historia clínica')
    )
    
    # Referencias a otros microservicios
    veterinarian_id = models.IntegerField(verbose_name=_('ID del Veterinario'))
    appointment_id = models.IntegerField(null=True, blank=True, verbose_name=_('ID de la cita'))
    
    # Información de la consulta
    consultation_type = models.CharField(
        max_length=15,
        choices=ConsultationType.choices,
        default=ConsultationType.GENERAL,
        verbose_name=_('Tipo de consulta')
    )
    
    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.IN_PROGRESS,
        verbose_name=_('Estado')
    )
    
    # Motivo y diagnóstico
    chief_complaint = models.TextField(verbose_name=_('Motivo principal de consulta'))
    history_present_illness = models.TextField(blank=True, verbose_name=_('Historia de la enfermedad actual'))
    physical_examination = models.TextField(blank=True, verbose_name=_('Examen físico'))
    
    # Diagnósticos
    primary_diagnosis = models.TextField(verbose_name=_('Diagnóstico principal'))
    secondary_diagnosis = models.TextField(blank=True, verbose_name=_('Diagnósticos secundarios'))
    differential_diagnosis = models.TextField(blank=True, verbose_name=_('Diagnóstico diferencial'))
    
    # Plan de tratamiento
    treatment_plan = models.TextField(blank=True, verbose_name=_('Plan de tratamiento'))
    medications_prescribed = models.TextField(blank=True, verbose_name=_('Medicamentos prescritos'))
    recommendations = models.TextField(blank=True, verbose_name=_('Recomendaciones'))
    
    # Seguimiento
    follow_up_required = models.BooleanField(default=False, verbose_name=_('Requiere seguimiento'))
    follow_up_date = models.DateField(null=True, blank=True, verbose_name=_('Fecha de seguimiento'))
    follow_up_notes = models.TextField(blank=True, verbose_name=_('Notas de seguimiento'))
    
    # Información adicional
    prognosis = models.TextField(blank=True, verbose_name=_('Pronóstico'))
    client_education = models.TextField(blank=True, verbose_name=_('Educación al cliente'))
    
    # Metadatos
    consultation_date = models.DateTimeField(auto_now_add=True, verbose_name=_('Fecha de consulta'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Fecha de actualización'))
    duration_minutes = models.IntegerField(null=True, blank=True, verbose_name=_('Duración (minutos)'))
    
    class Meta:
        verbose_name = _('Consulta')
        verbose_name_plural = _('Consultas')
        ordering = ['-consultation_date']
        permissions = [
            ("can_view_all_consultations", "Puede ver todas las consultas"),
            ("can_create_consultation", "Puede crear consultas"),
            ("can_edit_own_consultation", "Puede editar sus propias consultas"),
        ]

    def __str__(self):
        return f"Consulta {self.id} - {self.consultation_date.strftime('%d/%m/%Y')}"

    def clean(self):
        """Validaciones personalizadas"""
        if self.follow_up_required and not self.follow_up_date:
            raise ValidationError('Si requiere seguimiento, debe especificar la fecha')

class ConsultationProcedure(models.Model):
    """Procedimientos realizados durante una consulta"""
    
    consultation = models.ForeignKey(
        Consultation, 
        on_delete=models.CASCADE, 
        related_name='procedures',
        verbose_name=_('Consulta')
    )
    
    procedure_name = models.CharField(max_length=200, verbose_name=_('Nombre del procedimiento'))
    description = models.TextField(blank=True, verbose_name=_('Descripción'))
    duration_minutes = models.IntegerField(null=True, blank=True, verbose_name=_('Duración (minutos)'))
    
    # Información del procedimiento
    performed_by = models.IntegerField(verbose_name=_('Realizado por (ID usuario)'))
    assistant_ids = models.JSONField(default=list, blank=True, verbose_name=_('IDs de asistentes'))
    
    # Resultados
    outcome = models.TextField(blank=True, verbose_name=_('Resultado'))
    complications = models.TextField(blank=True, verbose_name=_('Complicaciones'))
    
    # Metadatos
    performed_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Fecha de realización'))
    
    class Meta:
        verbose_name = _('Procedimiento de Consulta')
        verbose_name_plural = _('Procedimientos de Consulta')
        ordering = ['-performed_at']

    def __str__(self):
        return f"{self.procedure_name} - {self.performed_at.strftime('%d/%m/%Y')}"

class ConsultationNote(models.Model):
    """Notas adicionales durante la consulta"""
    
    consultation = models.ForeignKey(
        Consultation, 
        on_delete=models.CASCADE, 
        related_name='notes',
        verbose_name=_('Consulta')
    )
    
    note_type = models.CharField(
        max_length=50,
        choices=[
            ('CLINICAL', _('Nota Clínica')),
            ('NURSING', _('Nota de Enfermería')),
            ('PHARMACY', _('Nota Farmacéutica')),
            ('OBSERVATION', _('Observación')),
            ('WARNING', _('Advertencia')),
            ('OTHER', _('Otra')),
        ],
        default='CLINICAL',
        verbose_name=_('Tipo de nota')
    )
    
    content = models.TextField(verbose_name=_('Contenido'))
    is_important = models.BooleanField(default=False, verbose_name=_('Importante'))
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Fecha de creación'))
    created_by = models.IntegerField(verbose_name=_('Creado por (ID usuario)'))
    
    class Meta:
        verbose_name = _('Nota de Consulta')
        verbose_name_plural = _('Notas de Consulta')
        ordering = ['-created_at']

    def __str__(self):
        return f"Nota {self.get_note_type_display()} - {self.created_at.strftime('%d/%m/%Y')}"

class Treatment(models.Model):
    """Tratamientos aplicados al paciente"""
    
    class TreatmentStatus(models.TextChoices):
        PRESCRIBED = 'PRESCRITO', _('Prescrito')
        IN_PROGRESS = 'EN_PROGRESO', _('En Progreso')
        COMPLETED = 'COMPLETADO', _('Completado')
        DISCONTINUED = 'DESCONTINUADO', _('Descontinuado')
        SUSPENDED = 'SUSPENDIDO', _('Suspendido')

    consultation = models.ForeignKey(
        Consultation, 
        on_delete=models.CASCADE, 
        related_name='treatments',
        verbose_name=_('Consulta')
    )
    
    treatment_name = models.CharField(max_length=200, verbose_name=_('Nombre del tratamiento'))
    description = models.TextField(verbose_name=_('Descripción'))
    
    # Medicación
    medication_name = models.CharField(max_length=200, blank=True, verbose_name=_('Medicamento'))
    dosage = models.CharField(max_length=100, blank=True, verbose_name=_('Dosis'))
    frequency = models.CharField(max_length=100, blank=True, verbose_name=_('Frecuencia'))
    duration = models.CharField(max_length=100, blank=True, verbose_name=_('Duración'))
    route = models.CharField(max_length=50, blank=True, verbose_name=_('Vía de administración'))
    
    # Estado y fechas
    status = models.CharField(
        max_length=15,
        choices=TreatmentStatus.choices,
        default=TreatmentStatus.PRESCRIBED,
        verbose_name=_('Estado')
    )
    
    start_date = models.DateField(verbose_name=_('Fecha de inicio'))
    end_date = models.DateField(null=True, blank=True, verbose_name=_('Fecha de finalización'))
    
    # Instrucciones especiales
    special_instructions = models.TextField(blank=True, verbose_name=_('Instrucciones especiales'))
    side_effects_to_watch = models.TextField(blank=True, verbose_name=_('Efectos secundarios a vigilar'))
    
    # Metadatos
    prescribed_by = models.IntegerField(verbose_name=_('Prescrito por (ID usuario)'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Fecha de prescripción'))
    
    class Meta:
        verbose_name = _('Tratamiento')
        verbose_name_plural = _('Tratamientos')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.treatment_name} - {self.get_status_display()}" 