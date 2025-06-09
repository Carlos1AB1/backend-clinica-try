from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', _('Administrador')
        VETERINARIO = 'VETERINARIO', _('Veterinario')
        RECEPCIONISTA = 'RECEPCIONISTA', _('Recepcionista')

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.RECEPCIONISTA,
    )
    email = models.EmailField(_('email address'), unique=True)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            # Asignar grupo según el rol
            group_name = self.role.lower()
            group, _ = Group.objects.get_or_create(name=group_name)
            self.groups.add(group)

class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('password reset token')
        verbose_name_plural = _('password reset tokens')
        ordering = ['-created_at']

    def __str__(self):
        return f"Token for {self.user.email}"

    def is_valid(self):
        from django.utils import timezone
        return not self.is_used and timezone.now() <= self.expires_at 