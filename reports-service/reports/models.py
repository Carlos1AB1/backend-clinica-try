from django.db import models
from django.utils import timezone
import uuid

class ReportTemplate(models.Model):
    """
    Plantillas de reportes predefinidas
    """
    REPORT_CATEGORIES = [
        ('USUARIOS', 'Usuarios'),
        ('CITAS', 'Citas'),
        ('HISTORIAS', 'Historias Clínicas'),
        ('RECETAS', 'Recetas'),
        ('INVENTARIO', 'Inventario'),
        ('FINANCIERO', 'Financiero'),
        ('OPERACIONAL', 'Operacional'),
    ]
    
    FORMAT_TYPES = [
        ('PDF', 'PDF'),
        ('EXCEL', 'Excel'),
        ('CSV', 'CSV'),
        ('HTML', 'HTML Web'),
    ]
    
    name = models.CharField(max_length=200, verbose_name='Nombre')
    description = models.TextField(verbose_name='Descripción')
    category = models.CharField(max_length=20, choices=REPORT_CATEGORIES, verbose_name='Categoría')
    sql_query = models.TextField(verbose_name='Consulta SQL', help_text='Query base para generar el reporte')
    parameters = models.JSONField(default=dict, verbose_name='Parámetros', help_text='Parámetros configurables del reporte')
    available_formats = models.JSONField(default=list, verbose_name='Formatos disponibles')
    is_public = models.BooleanField(default=False, verbose_name='Es público')
    requires_admin = models.BooleanField(default=True, verbose_name='Requiere permisos de admin')
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Actualizado')
    created_by = models.IntegerField(verbose_name='Creado por', help_text='ID del usuario del servicio de autenticación')
    
    class Meta:
        verbose_name = 'Plantilla de Reporte'
        verbose_name_plural = 'Plantillas de Reportes'
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.category} - {self.name}"

class ReportExecution(models.Model):
    """
    Historial de ejecuciones de reportes
    """
    STATUS_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('PROCESANDO', 'Procesando'),
        ('COMPLETADO', 'Completado'),
        ('ERROR', 'Error'),
        ('CANCELADO', 'Cancelado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE, verbose_name='Plantilla')
    name = models.CharField(max_length=200, verbose_name='Nombre del reporte')
    parameters = models.JSONField(default=dict, verbose_name='Parámetros utilizados')
    format_type = models.CharField(max_length=10, choices=ReportTemplate.FORMAT_TYPES, verbose_name='Formato')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDIENTE', verbose_name='Estado')
    file_path = models.CharField(max_length=500, blank=True, null=True, verbose_name='Ruta del archivo')
    file_size = models.BigIntegerField(default=0, verbose_name='Tamaño del archivo (bytes)')
    total_rows = models.IntegerField(default=0, verbose_name='Total de filas')
    execution_time = models.FloatField(default=0, verbose_name='Tiempo de ejecución (segundos)')
    error_message = models.TextField(blank=True, null=True, verbose_name='Mensaje de error')
    
    # Metadatos
    requested_by = models.IntegerField(verbose_name='Solicitado por', help_text='ID del usuario')
    requested_at = models.DateTimeField(default=timezone.now, verbose_name='Solicitado')
    started_at = models.DateTimeField(blank=True, null=True, verbose_name='Iniciado')
    completed_at = models.DateTimeField(blank=True, null=True, verbose_name='Completado')
    expires_at = models.DateTimeField(blank=True, null=True, verbose_name='Expira')
    download_count = models.IntegerField(default=0, verbose_name='Descargas')
    
    class Meta:
        verbose_name = 'Ejecución de Reporte'
        verbose_name_plural = 'Ejecuciones de Reportes'
        ordering = ['-requested_at']
    
    def __str__(self):
        return f"{self.name} - {self.status}"
    
    @property
    def is_expired(self):
        """Verificar si el reporte ha expirado"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    @property
    def is_ready(self):
        """Verificar si el reporte está listo para descargar"""
        return self.status == 'COMPLETADO' and not self.is_expired

class ReportFilter(models.Model):
    """
    Filtros guardados por usuarios para reportes
    """
    name = models.CharField(max_length=200, verbose_name='Nombre del filtro')
    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE, verbose_name='Plantilla')
    filter_data = models.JSONField(verbose_name='Datos del filtro')
    is_public = models.BooleanField(default=False, verbose_name='Es público')
    created_by = models.IntegerField(verbose_name='Creado por')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado')
    
    class Meta:
        verbose_name = 'Filtro de Reporte'
        verbose_name_plural = 'Filtros de Reportes'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.template.name} - {self.name}"

class ReportSchedule(models.Model):
    """
    Reportes programados
    """
    FREQUENCY_CHOICES = [
        ('DIARIO', 'Diario'),
        ('SEMANAL', 'Semanal'),
        ('QUINCENAL', 'Quincenal'),
        ('MENSUAL', 'Mensual'),
        ('TRIMESTRAL', 'Trimestral'),
        ('SEMESTRAL', 'Semestral'),
        ('ANUAL', 'Anual'),
    ]
    
    name = models.CharField(max_length=200, verbose_name='Nombre')
    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE, verbose_name='Plantilla')
    parameters = models.JSONField(default=dict, verbose_name='Parámetros')
    format_type = models.CharField(max_length=10, choices=ReportTemplate.FORMAT_TYPES, verbose_name='Formato')
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, verbose_name='Frecuencia')
    recipients = models.JSONField(default=list, verbose_name='Destinatarios', help_text='Lista de emails')
    next_execution = models.DateTimeField(verbose_name='Próxima ejecución')
    last_execution = models.DateTimeField(blank=True, null=True, verbose_name='Última ejecución')
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    created_by = models.IntegerField(verbose_name='Creado por')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado')
    
    class Meta:
        verbose_name = 'Reporte Programado'
        verbose_name_plural = 'Reportes Programados'
        ordering = ['next_execution']
    
    def __str__(self):
        return f"{self.name} - {self.frequency}"
