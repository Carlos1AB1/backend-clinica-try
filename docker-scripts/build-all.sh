#!/bin/bash

# Script para construir todas las imágenes Docker
# Clínica Veterinaria - Microservicios

set -e

echo "🐳 =========================================="
echo "🏥 CONSTRUYENDO IMÁGENES DOCKER"
echo "🐳 =========================================="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para mostrar progreso
show_progress() {
    echo -e "${BLUE}🔨 Construyendo: $1${NC}"
}

show_success() {
    echo -e "${GREEN}✅ Completado: $1${NC}"
}

show_error() {
    echo -e "${RED}❌ Error en: $1${NC}"
}

# Navegar al directorio raíz
cd "$(dirname "$0")/.."

# Construir cada microservicio
echo -e "${YELLOW}📦 Iniciando construcción de microservicios...${NC}"
echo ""

# 1. Auth Service
show_progress "Auth Service"
if docker build -t veterinary-auth-service ./auth-service; then
    show_success "Auth Service"
else
    show_error "Auth Service"
    exit 1
fi
echo ""

# 2. Users Service
show_progress "Users Service"
if docker build -t veterinary-users-service ./users-service; then
    show_success "Users Service"
else
    show_error "Users Service"
    exit 1
fi
echo ""

# 3. Appointments Service
show_progress "Appointments Service"
if docker build -t veterinary-appointments-service ./appointments-service; then
    show_success "Appointments Service"
else
    show_error "Appointments Service"
    exit 1
fi
echo ""

# 4. Medical Records Service
show_progress "Medical Records Service"
if docker build -t veterinary-medical-records-service ./medical-records-service; then
    show_success "Medical Records Service"
else
    show_error "Medical Records Service"
    exit 1
fi
echo ""

# 5. Prescriptions Service
show_progress "Prescriptions Service"
if docker build -t veterinary-prescriptions-service ./prescriptions-service; then
    show_success "Prescriptions Service"
else
    show_error "Prescriptions Service"
    exit 1
fi
echo ""

# 6. Reports Service
show_progress "Reports Service"
if docker build -t veterinary-reports-service ./reports-service; then
    show_success "Reports Service"
else
    show_error "Reports Service"
    exit 1
fi
echo ""

echo -e "${GREEN}🎉 =========================================="
echo "🏥 TODAS LAS IMÁGENES CONSTRUIDAS EXITOSAMENTE"
echo "🎉 ==========================================${NC}"
echo ""
echo -e "${BLUE}📋 Imágenes creadas:${NC}"
echo "   • veterinary-auth-service"
echo "   • veterinary-users-service"
echo "   • veterinary-appointments-service"
echo "   • veterinary-medical-records-service"
echo "   • veterinary-prescriptions-service"
echo "   • veterinary-reports-service"
echo ""
echo -e "${YELLOW}🚀 Para iniciar los servicios ejecuta:${NC}"
echo "   docker-compose up -d" 