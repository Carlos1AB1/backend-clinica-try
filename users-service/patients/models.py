from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from owners.models import Owner

class Patient(models.Model):
    class Species(models.TextChoices):
        DOG = 'PERRO', _('Perro')
        CAT = 'GATO', _('Gato')
        BIRD = 'AVE', _('Ave')
        RABBIT = 'CONEJO', _('Conejo')
        HAMSTER = 'HAMSTER', _('Hámster')
        FISH = 'PEZ', _('Pez')
        REPTILE = 'REPTIL', _('Reptil')
        OTHER = 'OTRO', _('Otro')

    class Gender(models.TextChoices):
        MALE = 'M', _('Macho')
        FEMALE = 'H', _('Hembra')

    class Size(models.TextChoices):
        MINI = 'MINI', _('Mini (0-5kg)')
        SMALL = 'PEQUEÑO', _('Pequeño (6-15kg)')
        MEDIUM = 'MEDIANO', _('Mediano (16-25kg)')
        LARGE = 'GRANDE', _('Grande (26-45kg)')
        GIANT = 'GIGANTE', _('Gigante (+45kg)')

    # Información básica
    name = models.CharField(max_length=50, verbose_name=_('Nombre'))
    species = models.CharField(
        max_length=10,
        choices=Species.choices,
        verbose_name=_('Especie')
    )
    breed = models.CharField(max_length=100, verbose_name=_('Raza'))
    gender = models.CharField(
        max_length=1,
        choices=Gender.choices,
        verbose_name=_('Sexo')
    )
    size = models.CharField(
        max_length=10,
        choices=Size.choices,
        blank=True,
        verbose_name=_('Tamaño')
    )
    color = models.CharField(max_length=100, verbose_name=_('Color'))
    
    # Fechas importantes
    birth_date = models.DateField(verbose_name=_('Fecha de nacimiento'))
    date_of_death = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Fecha de fallecimiento')
    )
    
    # Información física
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0.01), MaxValueValidator(999.99)],
        verbose_name=_('Peso (kg)')
    )
    
    # Información médica básica
    is_neutered = models.BooleanField(default=False, verbose_name=_('Esterilizado'))
    microchip_number = models.CharField(
        max_length=20,
        blank=True,
        unique=True,
        verbose_name=_('Número de microchip')
    )
    
    # Relaciones
    owner = models.ForeignKey(
        Owner,
        on_delete=models.CASCADE,
        related_name='patients',
        verbose_name=_('Propietario')
    )
    
    # Información adicional
    observations = models.TextField(
        blank=True,
        verbose_name=_('Observaciones')
    )
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Fecha de creación'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Fecha de actualización'))
    is_active = models.BooleanField(default=True, verbose_name=_('Activo'))

    class Meta:
        verbose_name = _('Paciente')
        verbose_name_plural = _('Pacientes')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.species} ({self.owner.get_full_name()})"

    @property
    def age_in_years(self):
        """Calcula la edad del paciente en años"""
        from datetime import date
        today = date.today()
        end_date = self.date_of_death if self.date_of_death else today
        
        age = end_date.year - self.birth_date.year
        if end_date.month < self.birth_date.month or \
           (end_date.month == self.birth_date.month and end_date.day < self.birth_date.day):
            age -= 1
        return age

    @property
    def is_alive(self):
        """Determina si el paciente está vivo"""
        return self.date_of_death is None

class Vaccination(models.Model):
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='vaccinations',
        verbose_name=_('Paciente')
    )
    vaccine_name = models.CharField(max_length=100, verbose_name=_('Nombre de la vacuna'))
    vaccination_date = models.DateField(verbose_name=_('Fecha de vacunación'))
    next_vaccination_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Próxima vacunación')
    )
    veterinarian = models.CharField(max_length=100, verbose_name=_('Veterinario'))
    batch_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Número de lote')
    )
    observations = models.TextField(blank=True, verbose_name=_('Observaciones'))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Vacunación')
        verbose_name_plural = _('Vacunaciones')
        ordering = ['-vaccination_date']

    def __str__(self):
        return f"{self.vaccine_name} - {self.patient.name} ({self.vaccination_date})" 