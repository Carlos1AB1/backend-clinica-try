#!/bin/bash

# Script para ver logs de los servicios Docker
# Clínica Veterinaria - Microservicios

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Navegar al directorio raíz
cd "$(dirname "$0")/.."

echo "📋 =========================================="
echo "🏥 LOGS DE CLÍNICA VETERINARIA"
echo "📋 =========================================="
echo ""

# Función para mostrar menú
show_menu() {
    echo -e "${BLUE}Selecciona el servicio para ver logs:${NC}"
    echo ""
    echo -e "${YELLOW}1)${NC} Auth Service (Puerto 8001)"
    echo -e "${YELLOW}2)${NC} Users Service (Puerto 8002)"
    echo -e "${YELLOW}3)${NC} Appointments Service (Puerto 8003)"
    echo -e "${YELLOW}4)${NC} Medical Records Service (Puerto 8004)"
    echo -e "${YELLOW}5)${NC} Prescriptions Service (Puerto 8005)"
    echo -e "${YELLOW}6)${NC} Reports Service (Puerto 8006)"
    echo -e "${YELLOW}7)${NC} Todas las bases de datos"
    echo -e "${YELLOW}8)${NC} Redis"
    echo -e "${YELLOW}9)${NC} Todos los servicios"
    echo -e "${YELLOW}0)${NC} Salir"
    echo ""
    echo -e "${BLUE}Opción:${NC} "
}

# Función para mostrar logs
show_logs() {
    local service=$1
    local service_name=$2
    
    echo -e "${GREEN}📋 Mostrando logs de: $service_name${NC}"
    echo -e "${YELLOW}Presiona Ctrl+C para salir${NC}"
    echo ""
    
    docker-compose logs -f --tail=50 $service
}

# Menú principal
while true; do
    show_menu
    read -r choice
    
    case $choice in
        1)
            show_logs "auth_service" "Auth Service"
            ;;
        2)
            show_logs "users_service" "Users Service"
            ;;
        3)
            show_logs "appointments_service" "Appointments Service"
            ;;
        4)
            show_logs "medical_records_service" "Medical Records Service"
            ;;
        5)
            show_logs "prescriptions_service" "Prescriptions Service"
            ;;
        6)
            show_logs "reports_service" "Reports Service"
            ;;
        7)
            echo -e "${GREEN}📋 Mostrando logs de todas las bases de datos${NC}"
            echo -e "${YELLOW}Presiona Ctrl+C para salir${NC}"
            echo ""
            docker-compose logs -f --tail=20 auth_db users_db appointments_db medical_records_db prescriptions_db reports_db
            ;;
        8)
            show_logs "redis" "Redis"
            ;;
        9)
            echo -e "${GREEN}📋 Mostrando logs de todos los servicios${NC}"
            echo -e "${YELLOW}Presiona Ctrl+C para salir${NC}"
            echo ""
            docker-compose logs -f --tail=20
            ;;
        0)
            echo -e "${GREEN}👋 ¡Hasta luego!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Opción inválida. Intenta de nuevo.${NC}"
            echo ""
            ;;
    esac
    
    echo ""
    echo -e "${BLUE}Presiona Enter para continuar...${NC}"
    read -r
    clear
done 