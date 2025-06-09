# Dockerfile para Reports Service
FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        default-mysql-client \
        build-essential \
        default-libmysqlclient-dev \
        pkg-config \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY ../requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . .

# Crear directorio para archivos estáticos y media
RUN mkdir -p staticfiles media

# Exponer puerto
EXPOSE 8000

# Script de inicio
COPY ./docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Comando por defecto
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"] 