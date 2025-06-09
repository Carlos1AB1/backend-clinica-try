#!/bin/bash

# Script de entrada para Prescriptions Service

set -e

echo "💊 Iniciando Prescriptions Service..."

# Esperar a que la base de datos esté disponible
echo "⏳ Esperando conexión a la base de datos..."
while ! mysql -h"$DB_HOST" -u"$DB_USER" -p"$DB_PASSWORD" -e "SELECT 1" >/dev/null 2>&1; do
  echo "⏳ Base de datos no disponible, esperando..."
  sleep 2
done

echo "✅ Base de datos conectada"

# Ejecutar migraciones
echo "📋 Ejecutando migraciones..."
python manage.py makemigrations inventory --noinput
python manage.py makemigrations prescriptions --noinput  
python manage.py makemigrations --noinput
python manage.py migrate --noinput

# Crear datos iniciales del inventario
echo "📦 Creando datos iniciales del inventario..."
python manage.py shell -c "
from inventory.models import MedicationCategory, Medication

# Crear categorías si no existen
categories = [
    {'name': 'Antibióticos', 'description': 'Medicamentos para combatir infecciones bacterianas'},
    {'name': 'Antiinflamatorios', 'description': 'Medicamentos para reducir inflamación'},
    {'name': 'Analgésicos', 'description': 'Medicamentos para aliviar el dolor'},
    {'name': 'Vitaminas', 'description': 'Suplementos vitamínicos'},
    {'name': 'Desparasitantes', 'description': 'Medicamentos antiparasitarios'},
]

for cat_data in categories:
    category, created = MedicationCategory.objects.get_or_create(
        name=cat_data['name'],
        defaults=cat_data
    )
    if created:
        print(f'✅ Categoría creada: {category.name}')

# Crear medicamentos de ejemplo
antibioticos = MedicationCategory.objects.get(name='Antibióticos')
if not Medication.objects.filter(name='Amoxicilina').exists():
    Medication.objects.create(
        name='Amoxicilina',
        generic_name='Amoxicilina',
        category=antibioticos,
        active_ingredient='Amoxicilina trihidratada',
        concentration='500mg',
        medication_type='TABLET',
        prescription_type='PRESCRIPTION',
        manufacturer='Laboratorio ABC',
        unit_price=2500.00,
        current_stock=100,
        minimum_stock=20,
        expiration_date='2025-12-31',
        requires_prescription=True,
        created_by=1
    )
    print('✅ Medicamento de ejemplo creado: Amoxicilina')
"

# Recolectar archivos estáticos
echo "📁 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

echo "🚀 Prescriptions Service listo!"

# Ejecutar comando pasado como parámetro
exec "$@" 