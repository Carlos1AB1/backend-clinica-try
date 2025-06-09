from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

class Owner(models.Model):
    class DocumentType(models.TextChoices):
        CEDULA = 'CC', _('Cédula de Ciudadanía')
        CEDULA_EXTRANJERIA = 'CE', _('Cédula de Extranjería')
        PASAPORTE = 'PA', _('Pasaporte')
        NIT = 'NIT', _('NIT')

    document_type = models.CharField(
        max_length=3,
        choices=DocumentType.choices,
        default=DocumentType.CEDULA,
        verbose_name=_('Tipo de documento')
    )
    document_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_('Número de documento'),
        validators=[
            RegexValidator(
                regex=r'^[0-9A-Za-z\-]+$',
                message='El número de documento solo puede contener números, letras y guiones'
            )
        ]
    )
    first_name = models.CharField(max_length=50, verbose_name=_('Nombres'))
    last_name = models.CharField(max_length=50, verbose_name=_('Apellidos'))
    email = models.EmailField(unique=True, verbose_name=_('Correo electrónico'))
    phone = models.CharField(
        max_length=15,
        verbose_name=_('Teléfono'),
        validators=[
            RegexValidator(
                regex=r'^\+?[1-9]\d{1,14}$',
                message='Ingrese un número de teléfono válido'
            )
        ]
    )
    address = models.TextField(verbose_name=_('Dirección'))
    city = models.CharField(max_length=100, verbose_name=_('Ciudad'))
    emergency_contact_name = models.CharField(
        max_length=100,
        verbose_name=_('Nombre contacto de emergencia'),
        blank=True
    )
    emergency_contact_phone = models.CharField(
        max_length=15,
        verbose_name=_('Teléfono contacto de emergencia'),
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\+?[1-9]\d{1,14}$',
                message='Ingrese un número de teléfono válido'
            )
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Fecha de creación'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Fecha de actualización'))
    is_active = models.BooleanField(default=True, verbose_name=_('Activo'))

    class Meta:
        verbose_name = _('Propietario')
        verbose_name_plural = _('Propietarios')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.document_number}"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}" 