from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from inventory.models import Medication
import uuid

class Prescription(models.Model):
    """Recetas médicas emitidas por veterinarios"""
    
    class Status(models.TextChoices):
        DRAFT = 'BORRADOR', _('Borrador')
        ISSUED = 'EMITIDA', _('Emitida')
        DISPENSED = 'DISPENSADA', _('Dispensada')
        PARTIALLY_DISPENSED = 'PARCIAL', _('Parcialmente dispensada')
        CANCELLED = 'CANCELADA', _('Cancelada')
        EXPIRED = 'EXPIRADA', _('Expirada')

    # Identificación única
    prescription_number = models.CharField(
        max_length=20, 
        unique=True, 
        editable=False,
        verbose_name=_('Número de receta')
    )
    
    # Referencias a otros microservicios
    patient_id = models.IntegerField(verbose_name=_('ID del Paciente'))
    owner_id = models.IntegerField(verbose_name=_('ID del Propietario'))
    veterinarian_id = models.IntegerField(verbose_name=_('ID del Veterinario'))
    consultation_id = models.IntegerField(null=True, blank=True, verbose_name=_('ID de consulta'))
    
    # Información de la receta
    diagnosis = models.TextField(verbose_name=_('Diagnóstico'))
    symptoms = models.TextField(blank=True, verbose_name=_('Síntomas'))
    treatment_notes = models.TextField(blank=True, verbose_name=_('Notas del tratamiento'))
    
    # Estado y fechas
    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name=_('Estado')
    )
    
    issue_date = models.DateTimeField(auto_now_add=True, verbose_name=_('Fecha de emisión'))
    expiration_date = models.DateField(verbose_name=_('Fecha de vencimiento'))
    dispensed_date = models.DateTimeField(null=True, blank=True, verbose_name=_('Fecha de dispensación'))
    
    # Información del veterinario
    veterinarian_license = models.CharField(max_length=50, verbose_name=_('Cédula del veterinario'))
    veterinarian_signature = models.TextField(blank=True, verbose_name=_('Firma digital'))
    
    # Control de dispensación
    can_be_dispensed_multiple_times = models.BooleanField(
        default=False, 
        verbose_name=_('Puede dispensarse múltiples veces')
    )
    max_dispensations = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name=_('Máximo número de dispensaciones')
    )
    dispensation_count = models.IntegerField(default=0, verbose_name=_('Número de dispensaciones'))
    
    # Información adicional
    special_instructions = models.TextField(blank=True, verbose_name=_('Instrucciones especiales'))
    follow_up_required = models.BooleanField(default=False, verbose_name=_('Requiere seguimiento'))
    follow_up_date = models.DateField(null=True, blank=True, verbose_name=_('Fecha de seguimiento'))
    
    # Totales
    total_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        verbose_name=_('Monto total')
    )
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Fecha de creación'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Fecha de actualización'))

    class Meta:
        verbose_name = _('Receta')
        verbose_name_plural = _('Recetas')
        ordering = ['-issue_date']

    def __str__(self):
        return f"Receta {self.prescription_number} - Paciente {self.patient_id}"

    def save(self, *args, **kwargs):
        if not self.prescription_number:
            self.prescription_number = self.generate_prescription_number()
        super().save(*args, **kwargs)

    def generate_prescription_number(self):
        """Generar número único de receta"""
        from datetime import datetime
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        # Formato: RX-YYYY-MM-NNNN
        prefix = f"RX-{current_year}-{current_month:02d}"
        
        # Buscar el último número de secuencia del mes
        last_prescription = Prescription.objects.filter(
            prescription_number__startswith=prefix
        ).order_by('-prescription_number').first()
        
        if last_prescription:
            try:
                last_number = int(last_prescription.prescription_number.split('-')[-1])
                next_number = last_number + 1
            except (ValueError, IndexError):
                next_number = 1
        else:
            next_number = 1
        
        return f"{prefix}-{next_number:04d}"

    @property
    def is_expired(self):
        """Verificar si la receta está vencida"""
        from datetime import date
        return self.expiration_date < date.today()

    @property
    def can_be_dispensed(self):
        """Verificar si la receta puede ser dispensada"""
        if self.status not in ['EMITIDA', 'PARCIAL']:
            return False
        if self.is_expired:
            return False
        if self.dispensation_count >= self.max_dispensations:
            return False
        return True

class PrescriptionItem(models.Model):
    """Medicamentos incluidos en una receta"""
    
    prescription = models.ForeignKey(
        Prescription, 
        on_delete=models.CASCADE, 
        related_name='items',
        verbose_name=_('Receta')
    )
    
    medication = models.ForeignKey(
        Medication, 
        on_delete=models.CASCADE,
        verbose_name=_('Medicamento')
    )
    
    # Cantidad y dosificación
    quantity_prescribed = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name=_('Cantidad prescrita')
    )
    quantity_dispensed = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_('Cantidad dispensada')
    )
    
    # Instrucciones de uso
    dosage = models.CharField(max_length=200, verbose_name=_('Dosis'))
    frequency = models.CharField(max_length=200, verbose_name=_('Frecuencia'))
    duration = models.CharField(max_length=100, verbose_name=_('Duración del tratamiento'))
    administration_route = models.CharField(max_length=100, verbose_name=_('Vía de administración'))
    
    # Instrucciones especiales
    special_instructions = models.TextField(blank=True, verbose_name=_('Instrucciones especiales'))
    with_food = models.BooleanField(default=False, verbose_name=_('Con comida'))
    
    # Precios al momento de la prescripción
    unit_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name=_('Precio unitario')
    )
    total_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name=_('Precio total')
    )
    
    # Estado
    is_substitutable = models.BooleanField(default=True, verbose_name=_('Puede sustituirse'))
    
    class Meta:
        verbose_name = _('Item de Receta')
        verbose_name_plural = _('Items de Receta')
        unique_together = ['prescription', 'medication']

    def __str__(self):
        return f"{self.medication.name} - {self.quantity_prescribed} unidades"

    def save(self, *args, **kwargs):
        # Calcular precio total
        self.total_price = self.quantity_prescribed * self.unit_price
        super().save(*args, **kwargs)

    @property
    def remaining_quantity(self):
        """Cantidad pendiente por dispensar"""
        return self.quantity_prescribed - self.quantity_dispensed

    @property
    def is_fully_dispensed(self):
        """Verificar si el item está completamente dispensado"""
        return self.quantity_dispensed >= self.quantity_prescribed

class PrescriptionDispensation(models.Model):
    """Registro de dispensaciones de recetas"""
    
    prescription = models.ForeignKey(
        Prescription, 
        on_delete=models.CASCADE, 
        related_name='dispensations',
        verbose_name=_('Receta')
    )
    
    # Información de la dispensación
    dispensation_date = models.DateTimeField(auto_now_add=True, verbose_name=_('Fecha de dispensación'))
    dispensed_by = models.IntegerField(verbose_name=_('Dispensado por (ID usuario)'))
    
    # Medicamentos dispensados
    total_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name=_('Monto total dispensado')
    )
    
    # Información del paciente/propietario
    received_by_name = models.CharField(max_length=200, verbose_name=_('Recibido por'))
    received_by_document = models.CharField(max_length=20, verbose_name=_('Documento de quien recibe'))
    
    # Notas
    notes = models.TextField(blank=True, verbose_name=_('Notas de dispensación'))
    
    class Meta:
        verbose_name = _('Dispensación')
        verbose_name_plural = _('Dispensaciones')
        ordering = ['-dispensation_date']

    def __str__(self):
        return f"Dispensación {self.id} - Receta {self.prescription.prescription_number}"

class PrescriptionDispensationItem(models.Model):
    """Items específicos dispensados en cada dispensación"""
    
    dispensation = models.ForeignKey(
        PrescriptionDispensation, 
        on_delete=models.CASCADE, 
        related_name='items',
        verbose_name=_('Dispensación')
    )
    
    prescription_item = models.ForeignKey(
        PrescriptionItem, 
        on_delete=models.CASCADE,
        verbose_name=_('Item de receta')
    )
    
    quantity_dispensed = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name=_('Cantidad dispensada')
    )
    
    unit_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name=_('Precio unitario')
    )
    
    total_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name=_('Precio total')
    )
    
    # Información del lote dispensado
    batch_number = models.CharField(max_length=50, blank=True, verbose_name=_('Número de lote'))
    expiration_date = models.DateField(null=True, blank=True, verbose_name=_('Fecha de vencimiento'))
    
    class Meta:
        verbose_name = _('Item de Dispensación')
        verbose_name_plural = _('Items de Dispensación')

    def __str__(self):
        return f"{self.prescription_item.medication.name} - {self.quantity_dispensed} unidades"

    def save(self, *args, **kwargs):
        self.total_price = self.quantity_dispensed * self.unit_price
        super().save(*args, **kwargs) 