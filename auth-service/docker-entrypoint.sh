#!/bin/bash

# Script de entrada para Auth Service

set -e

echo "🔐 Iniciando Auth Service..."

# Esperar a que la base de datos esté disponible
echo "⏳ Esperando conexión a la base de datos..."
while ! mysql -h"$DB_HOST" -u"$DB_USER" -p"$DB_PASSWORD" -e "SELECT 1" >/dev/null 2>&1; do
  echo "⏳ Base de datos no disponible, esperando..."
  sleep 2
done

echo "✅ Base de datos conectada"

# Ejecutar migraciones
echo "📋 Ejecutando migraciones..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput

# Crear superusuario si no existe
echo "👤 Verificando superusuario..."
python manage.py shell -c "
from users.models import User
if not User.objects.filter(email='admin@clinica.com').exists():
    User.objects.create_superuser(
        email='admin@clinica.com',
        password='Admin123!',
        first_name='Admin',
        last_name='Sistema',
        role='Admin'
    )
    print('✅ Superusuario creado: admin@clinica.com / Admin123!')
else:
    print('ℹ️ Superusuario ya existe')
"

# Crear usuarios de prueba
echo "👥 Creando usuarios de prueba..."
python manage.py shell -c "
from users.models import User

# Veterinario
if not User.objects.filter(email='vet@clinica.com').exists():
    User.objects.create_user(
        email='vet@clinica.com',
        password='Vet123!',
        first_name='Dr. Juan',
        last_name='Pérez',
        role='Veterinario'
    )
    print('✅ Veterinario creado: vet@clinica.com / Vet123!')

# Recepcionista
if not User.objects.filter(email='recep@clinica.com').exists():
    User.objects.create_user(
        email='recep@clinica.com',
        password='Recep123!',
        first_name='María',
        last_name='García',
        role='Recepcionista'
    )
    print('✅ Recepcionista creada: recep@clinica.com / Recep123!')
"

# Recolectar archivos estáticos
echo "📁 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

echo "🚀 Auth Service listo!"

# Ejecutar comando pasado como parámetro
exec "$@" 