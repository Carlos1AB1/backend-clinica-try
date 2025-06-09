#!/bin/bash

# Script de entrada para Reports Service

set -e

echo "📊 Iniciando Reports Service..."

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

# Crear plantillas de reportes iniciales
echo "📋 Creando plantillas de reportes..."
python manage.py shell -c "
from reports.models import ReportTemplate

# Plantillas básicas de reportes
templates = [
    {
        'name': 'Reporte de Usuarios',
        'description': 'Listado completo de propietarios registrados',
        'category': 'USUARIOS',
        'sql_query': 'SELECT * FROM owners WHERE created_at BETWEEN \${start_date} AND \${end_date}',
        'parameters': {'start_date': 'date', 'end_date': 'date'},
        'available_formats': ['PDF', 'EXCEL', 'CSV'],
        'requires_admin': False,
        'created_by': 1
    },
    {
        'name': 'Reporte de Citas',
        'description': 'Reporte de citas por período',
        'category': 'CITAS',
        'sql_query': 'SELECT * FROM appointments WHERE appointment_date BETWEEN \${start_date} AND \${end_date}',
        'parameters': {'start_date': 'date', 'end_date': 'date'},
        'available_formats': ['PDF', 'EXCEL'],
        'requires_admin': False,
        'created_by': 1
    },
    {
        'name': 'Reporte Financiero',
        'description': 'Reporte de ingresos y gastos',
        'category': 'FINANCIERO',
        'sql_query': 'SELECT * FROM financial_transactions WHERE date BETWEEN \${start_date} AND \${end_date}',
        'parameters': {'start_date': 'date', 'end_date': 'date'},
        'available_formats': ['PDF', 'EXCEL'],
        'requires_admin': True,
        'created_by': 1
    }
]

for template_data in templates:
    template, created = ReportTemplate.objects.get_or_create(
        name=template_data['name'],
        defaults=template_data
    )
    if created:
        print(f'✅ Plantilla creada: {template.name}')
"

# Recolectar archivos estáticos
echo "📁 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

echo "🚀 Reports Service listo!"

# Ejecutar comando pasado como parámetro
exec "$@" 