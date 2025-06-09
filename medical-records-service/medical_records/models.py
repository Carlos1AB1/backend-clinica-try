from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator
from django.conf import settings
import uuid
import os

def medical_file_upload_path(instance, filename):
    """Generar ruta de subida para archivos médicos"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('medical_records', str(instance.medical_record.patient_id), filename)

class MedicalRecord(models.Model):
    """Historia clínica principal del paciente - NO eliminable"""
    
    # Referencias a otros microservicios
    patient_id = models.IntegerField(unique=True, verbose_name=_('ID del Paciente'))
    owner_id = models.IntegerField(verbose_name=_('ID del Propietario'))
    
    # Información básica
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Fecha de creación'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Fecha de actualización'))
    created_by = models.IntegerField(verbose_name=_('Creado por (ID usuario)'))
    
    # Información médica general
    allergies = models.TextField(blank=True, verbose_name=_('Alergias conocidas'))
    chronic_conditions = models.TextField(blank=True, verbose_name=_('Condiciones crónicas'))
    current_medications = models.TextField(blank=True, verbose_name=_('Medicamentos actuales'))
    
    # Información física básica
    blood_type = models.CharField(max_length=5, blank=True, verbose_name=_('Tipo de sangre'))
    microchip_number = models.CharField(max_length=15, blank=True, verbose_name=_('Número de microchip'))
    
    # Información de emergencia
    emergency_contact = models.CharField(max_length=15, blank=True, verbose_name=_('Contacto de emergencia'))
    emergency_notes = models.TextField(blank=True, verbose_name=_('Notas de emergencia'))
    
    # Estado
    is_active = models.BooleanField(default=True, verbose_name=_('Activo'))

    class Meta:
        verbose_name = _('Historia Clínica')
        verbose_name_plural = _('Historias Clínicas')
        ordering = ['-created_at']

    def __str__(self):
        return f"Historia Clínica - Paciente {self.patient_id}"

    def delete(self, *args, **kwargs):
        """Sobrescribir delete para no permitir eliminación"""
        raise Exception("Las historias clínicas no pueden ser eliminadas por seguridad.")

class MedicalFile(models.Model):
    """Archivos adjuntos a la historia clínica"""
    
    class FileType(models.TextChoices):
        XRAY = 'RADIOGRAFIA', _('Radiografía')
        ULTRASOUND = 'ECOGRAFIA', _('Ecografía')
        BLOOD_TEST = 'EXAMEN_SANGRE', _('Examen de sangre')
        URINE_TEST = 'EXAMEN_ORINA', _('Examen de orina')
        VACCINE_CARD = 'CARNET_VACUNAS', _('Carnet de vacunas')
        PRESCRIPTION = 'RECETA', _('Receta médica')
        REPORT = 'REPORTE', _('Reporte médico')
        PHOTO = 'FOTO', _('Fotografía')
        OTHER = 'OTRO', _('Otro')

    medical_record = models.ForeignKey(
        MedicalRecord, 
        on_delete=models.CASCADE, 
        related_name='files',
        verbose_name=_('Historia clínica')
    )
    
    file = models.FileField(
        upload_to=medical_file_upload_path,
        validators=[
            FileExtensionValidator(allowed_extensions=settings.ALLOWED_FILE_EXTENSIONS)
        ],
        verbose_name=_('Archivo')
    )
    
    file_type = models.CharField(
        max_length=15,
        choices=FileType.choices,
        default=FileType.OTHER,
        verbose_name=_('Tipo de archivo')
    )
    
    title = models.CharField(max_length=200, verbose_name=_('Título'))
    description = models.TextField(blank=True, verbose_name=_('Descripción'))
    
    # Metadatos
    file_size = models.IntegerField(verbose_name=_('Tamaño del archivo (bytes)'))
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Fecha de subida'))
    uploaded_by = models.IntegerField(verbose_name=_('Subido por (ID usuario)'))

    class Meta:
        verbose_name = _('Archivo Médico')
        verbose_name_plural = _('Archivos Médicos')
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.title} - {self.get_file_type_display()}"

    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
        super().save(*args, **kwargs)

class VitalSigns(models.Model):
    """Signos vitales registrados en consultas"""
    
    medical_record = models.ForeignKey(
        MedicalRecord, 
        on_delete=models.CASCADE, 
        related_name='vital_signs',
        verbose_name=_('Historia clínica')
    )
    
    # Signos vitales básicos
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name=_('Peso (kg)'))
    temperature = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, verbose_name=_('Temperatura (°C)'))
    heart_rate = models.IntegerField(null=True, blank=True, verbose_name=_('Frecuencia cardíaca (bpm)'))
    respiratory_rate = models.IntegerField(null=True, blank=True, verbose_name=_('Frecuencia respiratoria (rpm)'))
    blood_pressure_systolic = models.IntegerField(null=True, blank=True, verbose_name=_('Presión sistólica'))
    blood_pressure_diastolic = models.IntegerField(null=True, blank=True, verbose_name=_('Presión diastólica'))
    
    # Información adicional
    body_condition_score = models.IntegerField(
        null=True, blank=True,
        help_text=_('Escala de 1-9'),
        verbose_name=_('Puntuación condición corporal')
    )
    
    notes = models.TextField(blank=True, verbose_name=_('Notas adicionales'))
    
    # Metadatos
    recorded_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Fecha de registro'))
    recorded_by = models.IntegerField(verbose_name=_('Registrado por (ID usuario)'))
    consultation_id = models.IntegerField(null=True, blank=True, verbose_name=_('ID de consulta'))

    class Meta:
        verbose_name = _('Signos Vitales')
        verbose_name_plural = _('Signos Vitales')
        ordering = ['-recorded_at']

    def __str__(self):
        return f"Signos Vitales - {self.recorded_at.strftime('%d/%m/%Y %H:%M')}" 