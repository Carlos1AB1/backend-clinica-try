# 🔧 Guía de Configuración de Variables de Entorno

## 📋 Resumen

Tu proyecto ya tiene configurado un archivo `.env` con todas las variables necesarias. Puedes personalizarlo según tus necesidades.

## 📁 Archivos de Variables de Entorno

```
✅ .env                 # Archivo de configuración activo (creado automáticamente)
✅ env.example          # Plantilla de variables (para referencia)
```

## 🛠️ Variables Configuradas Automáticamente

### **🗄️ Bases de Datos MySQL**
```env
# Contraseña raíz común
MYSQL_ROOT_PASSWORD=rootpassword

# Auth Service
AUTH_DB_NAME=auth_db
AUTH_DB_USER=auth_user
AUTH_DB_PASSWORD=auth_password

# Users Service
USERS_DB_NAME=users_db
USERS_DB_USER=users_user
USERS_DB_PASSWORD=users_password

# Appointments Service
APPOINTMENTS_DB_NAME=appointments_db
APPOINTMENTS_DB_USER=appointments_user
APPOINTMENTS_DB_PASSWORD=appointments_password

# Medical Records Service  
MEDICAL_DB_NAME=medical_records_db
MEDICAL_DB_USER=medical_user
MEDICAL_DB_PASSWORD=medical_password

# Prescriptions Service
PRESCRIPTIONS_DB_NAME=prescriptions_db
PRESCRIPTIONS_DB_USER=prescriptions_user
PRESCRIPTIONS_DB_PASSWORD=prescriptions_password

# Reports Service
REPORTS_DB_NAME=reports_db
REPORTS_DB_USER=reports_user
REPORTS_DB_PASSWORD=reports_password
```

### **🔗 URLs de Microservicios**
```env
AUTH_SERVICE_URL=http://auth_service:8000
USERS_SERVICE_URL=http://users_service:8000
APPOINTMENTS_SERVICE_URL=http://appointments_service:8000
MEDICAL_RECORDS_SERVICE_URL=http://medical_records_service:8000
PRESCRIPTIONS_SERVICE_URL=http://prescriptions_service:8000
REPORTS_SERVICE_URL=http://reports_service:8000
```

### **🔐 Configuración JWT**
```env
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_LIFETIME=1440  # 24 horas
JWT_REFRESH_TOKEN_LIFETIME=10080  # 7 días
```

### **📧 Configuración de Email**
```env
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

## 🔧 Personalización para Desarrollo

Si quieres cambiar alguna configuración para desarrollo, edita el archivo `.env`:

### **1. Cambiar Contraseñas de Base de Datos**
```env
# Cambiar contraseñas por algo más seguro
MYSQL_ROOT_PASSWORD=MiPasswordSuperSeguro123!
AUTH_DB_PASSWORD=AuthPassword2024!
USERS_DB_PASSWORD=UsersPassword2024!
# ... etc
```

### **2. Configurar Email Real**
```env
# Para Gmail (requiere App Password)
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-app-password-de-gmail

# Para Outlook
EMAIL_HOST=smtp.office365.com
EMAIL_HOST_USER=tu-email@outlook.com
EMAIL_HOST_PASSWORD=tu-password
```

### **3. Cambiar Secret Keys**
```env
# Generar claves secretas únicas
JWT_SECRET_KEY=mi-clave-jwt-super-secreta-2024
SECRET_KEY=mi-clave-django-super-secreta-2024
```

## 🚀 Configuración para Producción

Para producción, **DEBES** cambiar las siguientes variables:

### **1. Seguridad**
```env
DEBUG=False
SECRET_KEY=clave-super-secreta-para-produccion
JWT_SECRET_KEY=clave-jwt-super-secreta-para-produccion
```

### **2. Dominio**
```env
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com
CORS_ALLOWED_ORIGINS=https://tu-dominio.com,https://www.tu-dominio.com
```

### **3. Contraseñas Seguras**
```env
MYSQL_ROOT_PASSWORD=ContraseñaSúperSegura2024!@#
AUTH_DB_PASSWORD=AuthProd2024!@#
USERS_DB_PASSWORD=UsersProd2024!@#
# ... todas las demás
```

### **4. Email de Producción**
```env
EMAIL_HOST=smtp.tu-proveedor.com
EMAIL_HOST_USER=noreply@tu-dominio.com
EMAIL_HOST_PASSWORD=tu-password-seguro
DEFAULT_FROM_EMAIL=noreply@tu-dominio.com
```

## 🔄 Cómo Aplicar Cambios

### **1. Editar el archivo .env**
```bash
# En Windows
notepad .env

# En Linux/Mac
nano .env
```

### **2. Reiniciar los servicios**
```bash
# Detener servicios
docker-compose down

# Iniciar con nueva configuración
docker-compose up -d --build
```

### **3. Verificar que los cambios se aplicaron**
```bash
# Ver configuración actual
docker-compose config

# Ver variables de un servicio específico
docker-compose exec auth_service env | grep DB_
```

## 🚨 Consideraciones Importantes

### **🔐 Seguridad**
- ✅ **Nunca** subas el archivo `.env` a control de versiones
- ✅ El archivo `.env` está en `.gitignore` automáticamente
- ✅ Usa contraseñas seguras en producción
- ✅ Cambia todas las claves por defecto

### **📁 Backup de Configuración**
```bash
# Hacer backup del .env
copy .env .env.backup

# Restaurar desde backup
copy .env.backup .env
```

### **🔄 Valores por Defecto**
Si no configuras una variable en `.env`, Docker Compose usará los valores por defecto definidos en `docker-compose.yml` con la sintaxis `${VARIABLE:-default_value}`.

## 📋 Verificación de Variables

### **Script para verificar configuración**
```bash
# Ver todas las variables de entorno
docker-compose config | grep environment -A 20

# Verificar una variable específica
docker-compose run --rm auth_service echo $JWT_SECRET_KEY
```

## 🎯 Casos de Uso Comunes

### **Desarrollo Local**
```env
DEBUG=True
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### **Testing**
```env
DEBUG=True
DATABASE_URL=sqlite:///test.db
```

### **Staging**
```env
DEBUG=False
ALLOWED_HOSTS=staging.tu-dominio.com
```

### **Producción**
```env
DEBUG=False
ALLOWED_HOSTS=tu-dominio.com
CORS_ALLOW_ALL_ORIGINS=False
```

---

## ✅ Estado Actual

Tu proyecto está configurado con:

- ✅ **Archivo .env creado** con todas las variables necesarias
- ✅ **Docker Compose actualizado** para usar variables de entorno
- ✅ **Valores por defecto seguros** para desarrollo
- ✅ **Plantilla env.example** para nuevos deployments

**🚀 ¡Listo para usar! Simplemente ejecuta `docker-compose up -d --build` y todo funcionará con la configuración actual.** 