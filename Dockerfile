# 1. Usar uma imagem oficial do Python
FROM python:3.10-slim

# 2. Definir a pasta de trabalho dentro do container
WORKDIR /app

# 3. Instalar dependências do sistema (necessárias para uvicorn/gunicorn)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 4. Copiar o arquivo de requisitos e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar o restante do código
COPY . .

# O comando de inicialização a gente define no Docker Compose para 
# poder separar o que é API e o que é Celery.