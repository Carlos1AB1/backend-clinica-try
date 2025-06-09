from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal

class MedicationCategory(models.Model):
    """Categorías de medicamentos"""
    name = models.CharField(max_length=100, unique=True, verbose_name=_('Nombre'))
    description = models.TextField(blank=True, verbose_name=_('Descripción'))
    is_active = models.BooleanField(default=True, verbose_name=_('Activo'))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Categoría de Medicamento')
        verbose_name_plural = _('Categorías de Medicamentos')
        ordering = ['name']

    def __str__(self):
        return self.name

class Medication(models.Model):
    """Medicamentos disponibles en inventario"""
    
    class MedicationType(models.TextChoices):
        TABLET = 'TABLETA', _('Tableta')
        CAPSULE = 'CAPSULA', _('Cápsula')
        LIQUID = 'LIQUIDO', _('Líquido')
        INJECTION = 'INYECCION', _('Inyección')
        TOPICAL = 'TOPICO', _('Tópico')
        SPRAY = 'SPRAY', _('Spray')
        POWDER = 'POLVO', _('Polvo')
        OTHER = 'OTRO', _('Otro')

    class PrescriptionType(models.TextChoices):
        OTC = 'LIBRE', _('Venta libre')
        PRESCRIPTION = 'RECETA', _('Con receta')
        CONTROLLED = 'CONTROLADO', _('Medicamento controlado')

    # Información básica
    name = models.CharField(max_length=200, verbose_name=_('Nombre comercial'))
    generic_name = models.CharField(max_length=200, verbose_name=_('Nombre genérico'))
    category = models.ForeignKey(
        MedicationCategory, 
        on_delete=models.SET_NULL, 
        null=True,
        verbose_name=_('Categoría')
    )
    
    # Detalles del medicamento
    active_ingredient = models.CharField(max_length=300, verbose_name=_('Principio activo'))
    concentration = models.CharField(max_length=100, verbose_name=_('Concentración'))
    medication_type = models.CharField(
        max_length=15,
        choices=MedicationType.choices,
        verbose_name=_('Tipo de medicamento')
    )
    
    # Información regulatoria
    prescription_type = models.CharField(
        max_length=15,
        choices=PrescriptionType.choices,
        default=PrescriptionType.PRESCRIPTION,
        verbose_name=_('Tipo de prescripción')
    )
    
    # Información comercial
    manufacturer = models.CharField(max_length=200, verbose_name=_('Fabricante'))
    batch_number = models.CharField(max_length=50, blank=True, verbose_name=_('Número de lote'))
    
    # Precios
    unit_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name=_('Precio unitario')
    )
    
    # Inventario
    current_stock = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_('Stock actual')
    )
    minimum_stock = models.IntegerField(
        default=10,
        validators=[MinValueValidator(0)],
        verbose_name=_('Stock mínimo')
    )
    
    # Fechas importantes
    expiration_date = models.DateField(verbose_name=_('Fecha de vencimiento'))
    manufactured_date = models.DateField(null=True, blank=True, verbose_name=_('Fecha de fabricación'))
    
    # Información adicional
    dosage_instructions = models.TextField(blank=True, verbose_name=_('Instrucciones de dosificación'))
    contraindications = models.TextField(blank=True, verbose_name=_('Contraindicaciones'))
    side_effects = models.TextField(blank=True, verbose_name=_('Efectos secundarios'))
    storage_conditions = models.TextField(blank=True, verbose_name=_('Condiciones de almacenamiento'))
    
    # Estado
    is_active = models.BooleanField(default=True, verbose_name=_('Activo'))
    requires_prescription = models.BooleanField(default=True, verbose_name=_('Requiere receta'))
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Fecha de creación'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Fecha de actualización'))
    created_by = models.IntegerField(verbose_name=_('Creado por (ID usuario)'))

    class Meta:
        verbose_name = _('Medicamento')
        verbose_name_plural = _('Medicamentos')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.concentration})"

    @property
    def is_low_stock(self):
        """Verificar si el stock está bajo"""
        return self.current_stock <= self.minimum_stock

    @property
    def is_expired(self):
        """Verificar si el medicamento está vencido"""
        from datetime import date
        return self.expiration_date < date.today()

    @property
    def stock_status(self):
        """Estado del stock"""
        if self.current_stock == 0:
            return 'AGOTADO'
        elif self.is_low_stock:
            return 'STOCK_BAJO'
        else:
            return 'DISPONIBLE'

class StockMovement(models.Model):
    """Movimientos de inventario"""
    
    class MovementType(models.TextChoices):
        PURCHASE = 'COMPRA', _('Compra')
        SALE = 'VENTA', _('Venta')
        ADJUSTMENT = 'AJUSTE', _('Ajuste de inventario')
        RETURN = 'DEVOLUCION', _('Devolución')
        EXPIRED = 'VENCIDO', _('Medicamento vencido')
        TRANSFER = 'TRANSFERENCIA', _('Transferencia')

    medication = models.ForeignKey(
        Medication, 
        on_delete=models.CASCADE, 
        related_name='movements',
        verbose_name=_('Medicamento')
    )
    
    movement_type = models.CharField(
        max_length=15,
        choices=MovementType.choices,
        verbose_name=_('Tipo de movimiento')
    )
    
    quantity = models.IntegerField(verbose_name=_('Cantidad'))
    unit_cost = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True, blank=True,
        verbose_name=_('Costo unitario')
    )
    
    # Referencias
    reference_document = models.CharField(max_length=100, blank=True, verbose_name=_('Documento de referencia'))
    prescription_id = models.IntegerField(null=True, blank=True, verbose_name=_('ID de receta'))
    
    # Información adicional
    reason = models.TextField(blank=True, verbose_name=_('Motivo'))
    notes = models.TextField(blank=True, verbose_name=_('Notas'))
    
    # Stock después del movimiento
    stock_after = models.IntegerField(verbose_name=_('Stock después del movimiento'))
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Fecha del movimiento'))
    created_by = models.IntegerField(verbose_name=_('Registrado por (ID usuario)'))

    class Meta:
        verbose_name = _('Movimiento de Stock')
        verbose_name_plural = _('Movimientos de Stock')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.medication.name} ({self.quantity})" 