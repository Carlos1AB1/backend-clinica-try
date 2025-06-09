# 🐳 Clínica Veterinaria - Dockerización Completa

## 📋 Descripción

Este proyecto está **completamente dockerizado** con 6 microservicios independientes, cada uno con su propia base de datos MySQL y configuración Docker.

## 🏗️ Arquitectura Docker

```
🏥 Clínica Veterinaria
├── 🔐 Auth Service (Puerto 8001) + MySQL (3306)
├── 👥 Users Service (Puerto 8002) + MySQL (3307)
├── 📅 Appointments Service (Puerto 8003) + MySQL (3308)
├── 🏥 Medical Records Service (Puerto 8004) + MySQL (3309)
├── 💊 Prescriptions Service (Puerto 8005) + MySQL (3310)
├── 📊 Reports Service (Puerto 8006) + MySQL (3311)
└── 🔧 Redis (Puerto 6379)
```

## 🚀 Inicio Rápido

### **Opción 1: Script Automático (Recomendado)**

```bash
# Iniciar todo el sistema
./docker-scripts/start-all.sh

# Ver logs
./docker-scripts/logs.sh

# Detener todo
./docker-scripts/stop-all.sh
```

### **Opción 2: Comandos Docker Compose**

```bash
# Construir e iniciar todos los servicios
docker-compose up -d --build

# Ver estado de los servicios
docker-compose ps

# Ver logs de todos los servicios
docker-compose logs -f

# Detener todos los servicios
docker-compose down
```

## 📦 Servicios Disponibles

| Servicio | Puerto | URL | Swagger |
|----------|--------|-----|---------|
| 🔐 **Auth Service** | 8001 | http://localhost:8001 | http://localhost:8001/api/docs/ |
| 👥 **Users Service** | 8002 | http://localhost:8002 | http://localhost:8002/api/docs/ |
| 📅 **Appointments Service** | 8003 | http://localhost:8003 | http://localhost:8003/api/docs/ |
| 🏥 **Medical Records Service** | 8004 | http://localhost:8004 | http://localhost:8004/api/docs/ |
| 💊 **Prescriptions Service** | 8005 | http://localhost:8005 | http://localhost:8005/api/docs/ |
| 📊 **Reports Service** | 8006 | http://localhost:8006 | http://localhost:8006/api/docs/ |

## 🗄️ Bases de Datos

| Base de Datos | Puerto | Usuario | Contraseña |
|---------------|--------|---------|------------|
| **auth_db** | 3306 | auth_user | auth_password |
| **users_db** | 3307 | users_user | users_password |
| **appointments_db** | 3308 | appointments_user | appointments_password |
| **medical_records_db** | 3309 | medical_user | medical_password |
| **prescriptions_db** | 3310 | prescriptions_user | prescriptions_password |
| **reports_db** | 3311 | reports_user | reports_password |

## 👤 Usuarios por Defecto

| Rol | Email | Contraseña |
|-----|-------|------------|
| **Administrador** | admin@clinica.com | Admin123! |
| **Veterinario** | vet@clinica.com | Vet123! |
| **Recepcionista** | recep@clinica.com | Recep123! |

## 🛠️ Scripts de Gestión

### **build-all.sh**
Construye todas las imágenes Docker de los microservicios.

```bash
./docker-scripts/build-all.sh
```

### **start-all.sh**
Inicia todo el sistema completo con verificaciones y configuración automática.

```bash
./docker-scripts/start-all.sh
```

### **stop-all.sh**
Detiene todos los servicios con opciones de limpieza.

```bash
./docker-scripts/stop-all.sh
```

### **logs.sh**
Menú interactivo para ver logs de cualquier servicio.

```bash
./docker-scripts/logs.sh
```

## 🔧 Comandos Útiles

### **Ver Estado de Servicios**
```bash
docker-compose ps
```

### **Ver Logs de un Servicio Específico**
```bash
docker-compose logs -f auth_service
docker-compose logs -f users_service
docker-compose logs -f appointments_service
```

### **Reiniciar un Servicio**
```bash
docker-compose restart auth_service
```

### **Ejecutar Comandos en un Contenedor**
```bash
# Acceder al shell de un servicio
docker-compose exec auth_service bash

# Ejecutar migraciones manualmente
docker-compose exec auth_service python manage.py migrate

# Crear superusuario
docker-compose exec auth_service python manage.py createsuperuser
```

### **Conectar a Base de Datos**
```bash
# Conectar a auth_db
docker-compose exec auth_db mysql -u auth_user -p auth_db

# Conectar a users_db
docker-compose exec users_db mysql -u users_user -p users_db
```

## 📊 Monitoreo y Debugging

### **Ver Uso de Recursos**
```bash
docker stats
```

### **Inspeccionar Contenedores**
```bash
docker-compose exec auth_service ps aux
docker-compose exec auth_service df -h
```

### **Ver Logs en Tiempo Real**
```bash
# Todos los servicios
docker-compose logs -f

# Solo aplicaciones (sin bases de datos)
docker-compose logs -f auth_service users_service appointments_service medical_records_service prescriptions_service reports_service
```

## 🔄 Desarrollo

### **Reconstruir un Servicio**
```bash
# Reconstruir solo un servicio
docker-compose build auth_service
docker-compose up -d auth_service

# Reconstruir todo
docker-compose build
docker-compose up -d
```

### **Volúmenes de Desarrollo**
Para desarrollo, puedes montar el código fuente como volumen:

```yaml
# En docker-compose.override.yml
services:
  auth_service:
    volumes:
      - ./auth-service:/app
```

## 🧹 Limpieza

### **Limpiar Contenedores Detenidos**
```bash
docker container prune
```

### **Limpiar Imágenes No Utilizadas**
```bash
docker image prune
```

### **Limpiar Todo el Sistema**
```bash
docker system prune -a
```

### **Eliminar Volúmenes de Datos**
```bash
docker-compose down -v
```

## 🚨 Solución de Problemas

### **Problema: Puerto ya en uso**
```bash
# Ver qué está usando el puerto
netstat -tulpn | grep :8001

# Detener servicios y reiniciar
docker-compose down
docker-compose up -d
```

### **Problema: Base de datos no conecta**
```bash
# Ver logs de la base de datos
docker-compose logs auth_db

# Reiniciar base de datos
docker-compose restart auth_db

# Esperar y reiniciar servicio
sleep 10
docker-compose restart auth_service
```

### **Problema: Migraciones no se ejecutan**
```bash
# Ejecutar migraciones manualmente
docker-compose exec auth_service python manage.py migrate

# Ver estado de migraciones
docker-compose exec auth_service python manage.py showmigrations
```

### **Problema: Permisos de archivos**
```bash
# En Linux/Mac, dar permisos a scripts
chmod +x docker-scripts/*.sh

# En Windows, usar Git Bash o WSL
```

## 📝 Configuración Personalizada

### **Variables de Entorno**
Copia `env.example` a `.env` y personaliza:

```bash
cp env.example .env
# Editar .env con tus configuraciones
```

### **Configuración de Email**
Para habilitar envío de emails, configura en `.env`:

```env
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-app-password
```

### **Configuración de Producción**
Para producción, modifica:

```env
DEBUG=False
ALLOWED_HOSTS=tu-dominio.com
SECRET_KEY=clave-super-secreta-de-produccion
```

## 🔐 Seguridad

### **Cambiar Contraseñas por Defecto**
En producción, cambia todas las contraseñas en `docker-compose.yml`:

```yaml
environment:
  MYSQL_PASSWORD: contraseña-super-segura
```

### **Configurar HTTPS**
Para producción, usa un proxy reverso como Nginx:

```yaml
# nginx.conf
server {
    listen 443 ssl;
    server_name tu-dominio.com;
    
    location / {
        proxy_pass http://localhost:8001;
    }
}
```

## 📈 Escalabilidad

### **Múltiples Instancias**
```bash
# Escalar un servicio
docker-compose up -d --scale auth_service=3
```

### **Load Balancer**
Usar Nginx o HAProxy para balancear carga entre instancias.

## 🎯 Testing

### **Ejecutar Tests**
```bash
# Tests en un servicio
docker-compose exec auth_service python manage.py test

# Tests con coverage
docker-compose exec auth_service coverage run --source='.' manage.py test
docker-compose exec auth_service coverage report
```

## 📞 Soporte

Si tienes problemas:

1. **Revisa los logs**: `./docker-scripts/logs.sh`
2. **Verifica el estado**: `docker-compose ps`
3. **Reinicia servicios**: `docker-compose restart [servicio]`
4. **Limpia y reinicia**: `docker-compose down && docker-compose up -d`

---

## 🎉 ¡Listo!

Tu clínica veterinaria está completamente dockerizada y lista para usar. Todos los microservicios están configurados con:

- ✅ **Dockerfiles optimizados**
- ✅ **Scripts de entrada automáticos**
- ✅ **Configuración de bases de datos**
- ✅ **Usuarios por defecto**
- ✅ **Documentación Swagger**
- ✅ **Scripts de gestión**
- ✅ **Monitoreo y logs**

**¡Disfruta tu sistema completamente containerizado! 🐳🏥** 