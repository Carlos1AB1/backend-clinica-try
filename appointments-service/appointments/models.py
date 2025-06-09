from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta

class Appointment(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = 'AGENDADA', _('Agendada')
        CONFIRMED = 'CONFIRMADA', _('Confirmada')
        IN_PROGRESS = 'EN_PROGRESO', _('En Progreso')
        COMPLETED = 'COMPLETADA', _('Completada')
        CANCELLED = 'CANCELADA', _('Cancelada')
        NO_SHOW = 'NO_ASISTIO', _('No Asistió')

    class Priority(models.TextChoices):
        LOW = 'BAJA', _('Baja')
        NORMAL = 'NORMAL', _('Normal')
        HIGH = 'ALTA', _('Alta')
        EMERGENCY = 'EMERGENCIA', _('Emergencia')

    class AppointmentType(models.TextChoices):
        CONSULTATION = 'CONSULTA', _('Consulta General')
        VACCINATION = 'VACUNACION', _('Vacunación')
        SURGERY = 'CIRUGIA', _('Cirugía')
        EMERGENCY = 'EMERGENCIA', _('Emergencia')
        FOLLOW_UP = 'SEGUIMIENTO', _('Seguimiento')
        GROOMING = 'ESTETICA', _('Estética')

    # Referencias a otros microservicios (solo IDs)
    patient_id = models.IntegerField(verbose_name=_('ID del Paciente'))
    owner_id = models.IntegerField(verbose_name=_('ID del Propietario'))
    veterinarian_id = models.IntegerField(verbose_name=_('ID del Veterinario'))
    
    # Información de la cita
    appointment_date = models.DateField(verbose_name=_('Fecha de la cita'))
    appointment_time = models.TimeField(verbose_name=_('Hora de la cita'))
    duration_minutes = models.IntegerField(
        default=30,
        validators=[MinValueValidator(15), MaxValueValidator(240)],
        verbose_name=_('Duración (minutos)')
    )
    
    appointment_type = models.CharField(
        max_length=15,
        choices=AppointmentType.choices,
        default=AppointmentType.CONSULTATION,
        verbose_name=_('Tipo de cita')
    )
    
    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.SCHEDULED,
        verbose_name=_('Estado')
    )
    
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.NORMAL,
        verbose_name=_('Prioridad')
    )
    
    # Información adicional
    reason = models.TextField(verbose_name=_('Motivo de la consulta'))
    notes = models.TextField(blank=True, verbose_name=_('Notas adicionales'))
    
    # Información de contacto
    contact_phone = models.CharField(max_length=15, verbose_name=_('Teléfono de contacto'))
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Fecha de creación'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Fecha de actualización'))
    created_by = models.IntegerField(verbose_name=_('Creado por (ID usuario)'))
    
    # Campos para notificaciones
    reminder_sent = models.BooleanField(default=False, verbose_name=_('Recordatorio enviado'))
    confirmation_required = models.BooleanField(default=True, verbose_name=_('Requiere confirmación'))
    confirmed_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Confirmado en'))

    class Meta:
        verbose_name = _('Cita')
        verbose_name_plural = _('Citas')
        ordering = ['appointment_date', 'appointment_time']
        unique_together = ['patient_id', 'appointment_date', 'appointment_time']

    def __str__(self):
        return f"Cita {self.id} - Paciente {self.patient_id} - {self.appointment_date} {self.appointment_time}"

    def clean(self):
        """Validaciones personalizadas"""
        if self.appointment_date and self.appointment_time:
            # Validar que la cita no sea en el pasado
            appointment_datetime = datetime.combine(self.appointment_date, self.appointment_time)
            if appointment_datetime < datetime.now():
                raise ValidationError('No se pueden agendar citas en el pasado')
            
            # Validar horario de trabajo
            from django.conf import settings
            start_time = datetime.strptime(settings.WORKING_HOURS_START, '%H:%M').time()
            end_time = datetime.strptime(settings.WORKING_HOURS_END, '%H:%M').time()
            
            if not (start_time <= self.appointment_time <= end_time):
                raise ValidationError(f'Las citas deben estar entre {start_time} y {end_time}')

    @property
    def end_time(self):
        """Calcula la hora de finalización de la cita"""
        appointment_datetime = datetime.combine(self.appointment_date, self.appointment_time)
        end_datetime = appointment_datetime + timedelta(minutes=self.duration_minutes)
        return end_datetime.time()

    @property
    def is_past(self):
        """Determina si la cita ya pasó"""
        appointment_datetime = datetime.combine(self.appointment_date, self.appointment_time)
        return appointment_datetime < datetime.now()

class VeterinarianSchedule(models.Model):
    class DayOfWeek(models.TextChoices):
        MONDAY = 'LUNES', _('Lunes')
        TUESDAY = 'MARTES', _('Martes')
        WEDNESDAY = 'MIERCOLES', _('Miércoles')
        THURSDAY = 'JUEVES', _('Jueves')
        FRIDAY = 'VIERNES', _('Viernes')
        SATURDAY = 'SABADO', _('Sábado')
        SUNDAY = 'DOMINGO', _('Domingo')

    veterinarian_id = models.IntegerField(verbose_name=_('ID del Veterinario'))
    day_of_week = models.CharField(
        max_length=10,
        choices=DayOfWeek.choices,
        verbose_name=_('Día de la semana')
    )
    start_time = models.TimeField(verbose_name=_('Hora de inicio'))
    end_time = models.TimeField(verbose_name=_('Hora de fin'))
    is_active = models.BooleanField(default=True, verbose_name=_('Activo'))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Horario del Veterinario')
        verbose_name_plural = _('Horarios de Veterinarios')
        unique_together = ['veterinarian_id', 'day_of_week']

    def __str__(self):
        return f"Veterinario {self.veterinarian_id} - {self.day_of_week}: {self.start_time}-{self.end_time}"

class AppointmentBlock(models.Model):
    """Bloqueos de horarios para vacaciones, reuniones, etc."""
    veterinarian_id = models.IntegerField(verbose_name=_('ID del Veterinario'))
    start_datetime = models.DateTimeField(verbose_name=_('Inicio del bloqueo'))
    end_datetime = models.DateTimeField(verbose_name=_('Fin del bloqueo'))
    reason = models.CharField(max_length=200, verbose_name=_('Razón del bloqueo'))
    is_active = models.BooleanField(default=True, verbose_name=_('Activo'))
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.IntegerField(verbose_name=_('Creado por (ID usuario)'))

    class Meta:
        verbose_name = _('Bloqueo de Horario')
        verbose_name_plural = _('Bloqueos de Horarios')
        ordering = ['start_datetime']

    def __str__(self):
        return f"Bloqueo Veterinario {self.veterinarian_id} - {self.start_datetime} a {self.end_datetime}" 