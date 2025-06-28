# Use uma imagem base Python oficial e otimizada
FROM python:3.11-slim

# Definir variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Criar diretório de trabalho
WORKDIR /app

# Copiar arquivos de dependências
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY main.py .

# Criar diretório para uploads temporários
RUN mkdir -p /tmp/uploads

# Expor porta
EXPOSE 8000

# Definir usuário não-root para segurança
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app /tmp/uploads
USER appuser

# Configurar limite de threads para CPU
ENV OMP_NUM_THREADS=4

# Comando para executar a aplicação
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"] 