#!/bin/bash

# Script para iniciar todos los servicios Docker
# Clínica Veterinaria - Microservicios

set -e

echo "🚀 =========================================="
echo "🏥 INICIANDO CLÍNICA VETERINARIA"
echo "🚀 =========================================="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Navegar al directorio raíz
cd "$(dirname "$0")/.."

echo -e "${BLUE}🔍 Verificando Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker no está instalado${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose no está instalado${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker está disponible${NC}"
echo ""

# Detener servicios existentes
echo -e "${YELLOW}🛑 Deteniendo servicios existentes...${NC}"
docker-compose down --remove-orphans

echo ""
echo -e "${BLUE}🏗️ Construyendo e iniciando servicios...${NC}"

# Iniciar servicios
docker-compose up -d --build

echo ""
echo -e "${YELLOW}⏳ Esperando que los servicios estén listos...${NC}"
sleep 30

echo ""
echo -e "${GREEN}🎉 =========================================="
echo "🏥 CLÍNICA VETERINARIA INICIADA"
echo "🎉 ==========================================${NC}"
echo ""
echo -e "${BLUE}📋 Servicios disponibles:${NC}"
echo ""
echo -e "${YELLOW}🔐 Auth Service:${NC}          http://localhost:8001"
echo -e "${YELLOW}👥 Users Service:${NC}         http://localhost:8002"
echo -e "${YELLOW}📅 Appointments Service:${NC}  http://localhost:8003"
echo -e "${YELLOW}🏥 Medical Records Service:${NC} http://localhost:8004"
echo -e "${YELLOW}💊 Prescriptions Service:${NC} http://localhost:8005"
echo -e "${YELLOW}📊 Reports Service:${NC}       http://localhost:8006"
echo ""
echo -e "${BLUE}📊 Bases de datos MySQL:${NC}"
echo -e "${YELLOW}   • Auth DB:${NC}           localhost:3306"
echo -e "${YELLOW}   • Users DB:${NC}          localhost:3307"
echo -e "${YELLOW}   • Appointments DB:${NC}   localhost:3308"
echo -e "${YELLOW}   • Medical Records DB:${NC} localhost:3309"
echo -e "${YELLOW}   • Prescriptions DB:${NC}  localhost:3310"
echo -e "${YELLOW}   • Reports DB:${NC}        localhost:3311"
echo ""
echo -e "${BLUE}🔧 Herramientas:${NC}"
echo -e "${YELLOW}   • Redis:${NC}             localhost:6379"
echo ""
echo -e "${GREEN}📖 Documentación API:${NC}"
echo -e "${YELLOW}   • Auth Swagger:${NC}      http://localhost:8001/api/docs/"
echo -e "${YELLOW}   • Users Swagger:${NC}     http://localhost:8002/api/docs/"
echo -e "${YELLOW}   • Appointments Swagger:${NC} http://localhost:8003/api/docs/"
echo -e "${YELLOW}   • Medical Swagger:${NC}   http://localhost:8004/api/docs/"
echo -e "${YELLOW}   • Prescriptions Swagger:${NC} http://localhost:8005/api/docs/"
echo -e "${YELLOW}   • Reports Swagger:${NC}   http://localhost:8006/api/docs/"
echo ""
echo -e "${BLUE}👤 Usuarios por defecto:${NC}"
echo -e "${YELLOW}   • Admin:${NC}       admin@clinica.com / Admin123!"
echo -e "${YELLOW}   • Veterinario:${NC} vet@clinica.com / Vet123!"
echo -e "${YELLOW}   • Recepcionista:${NC} recep@clinica.com / Recep123!"
echo ""
echo -e "${GREEN}🔧 Comandos útiles:${NC}"
echo -e "${YELLOW}   • Ver logs:${NC}      docker-compose logs -f [servicio]"
echo -e "${YELLOW}   • Detener todo:${NC}  docker-compose down"
echo -e "${YELLOW}   • Reiniciar:${NC}     docker-compose restart [servicio]"
echo -e "${YELLOW}   • Estado:${NC}        docker-compose ps" 