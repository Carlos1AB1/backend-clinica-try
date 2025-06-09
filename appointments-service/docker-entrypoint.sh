#!/bin/bash

# Script de entrada para Appointments Service

set -e

echo "📅 Iniciando Appointments Service..."

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

# Recolectar archivos estáticos
echo "📁 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

echo "🚀 Appointments Service listo!"

# Ejecutar comando pasado como parámetro
exec "$@" 