#!/bin/bash

# Script para detener todos los servicios Docker
# Clínica Veterinaria - Microservicios

set -e

echo "🛑 =========================================="
echo "🏥 DETENIENDO CLÍNICA VETERINARIA"
echo "🛑 =========================================="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Navegar al directorio raíz
cd "$(dirname "$0")/.."

echo -e "${BLUE}🔍 Verificando servicios activos...${NC}"
docker-compose ps

echo ""
echo -e "${YELLOW}🛑 Deteniendo servicios...${NC}"
docker-compose down

echo ""
echo -e "${BLUE}🧹 ¿Deseas limpiar volúmenes de datos? (y/N):${NC}"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo -e "${YELLOW}🗑️ Eliminando volúmenes...${NC}"
    docker-compose down -v
    echo -e "${GREEN}✅ Volúmenes eliminados${NC}"
fi

echo ""
echo -e "${BLUE}🧹 ¿Deseas eliminar imágenes no utilizadas? (y/N):${NC}"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo -e "${YELLOW}🗑️ Limpiando imágenes...${NC}"
    docker image prune -f
    echo -e "${GREEN}✅ Imágenes limpiadas${NC}"
fi

echo ""
echo -e "${GREEN}✅ =========================================="
echo "🏥 CLÍNICA VETERINARIA DETENIDA"
echo "✅ ==========================================${NC}"
echo ""
echo -e "${BLUE}🔧 Comandos útiles:${NC}"
echo -e "${YELLOW}   • Iniciar de nuevo:${NC}  ./docker-scripts/start-all.sh"
echo -e "${YELLOW}   • Ver estado:${NC}        docker-compose ps"
echo -e "${YELLOW}   • Limpiar todo:${NC}      docker system prune -a" 