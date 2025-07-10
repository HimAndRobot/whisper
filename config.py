"""
Configurações da API Faster-Whisper
"""

import os
from typing import Optional

class Config:
    """Configurações base da aplicação"""
    
    # Configurações do servidor
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Configurações do Whisper
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "base")
    WHISPER_DEVICE: str = os.getenv("WHISPER_DEVICE", "cpu")
    WHISPER_COMPUTE_TYPE: str = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
    
    # Configurações de performance
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "100")) * 1024 * 1024  # 100MB
    OMP_NUM_THREADS: int = int(os.getenv("OMP_NUM_THREADS", "16"))
    
    # Configurações de transcrição padrão
    DEFAULT_BEAM_SIZE: int = 1
    DEFAULT_VAD_FILTER: bool = True
    DEFAULT_WORD_TIMESTAMPS: bool = False
    DEFAULT_LANGUAGE: str = os.getenv("DEFAULT_LANGUAGE", "pt")  # Idioma padrão
    
    # Configurações de segurança
    ALLOWED_EXTENSIONS: list = ['.mp3', '.wav', '.m4a', '.ogg', '.flac', '.aac']
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "*").split(",")
    
    # Configurações de logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Diretórios
    TEMP_DIR: str = os.getenv("TEMP_DIR", "/tmp/uploads")
    
    @classmethod
    def get_model_info(cls) -> dict:
        """Retorna informações sobre o modelo configurado"""
        model_sizes = {
            "tiny": {"size": "39 MB", "speed": "Muito rápido", "quality": "Básica"},
            "base": {"size": "74 MB", "speed": "Rápido", "quality": "Boa"},
            "small": {"size": "244 MB", "speed": "Médio", "quality": "Muito boa"},
            "medium": {"size": "769 MB", "speed": "Lento", "quality": "Excelente"},
            "large-v3": {"size": "1550 MB", "speed": "Muito lento", "quality": "Superior"},
        }
        
        return model_sizes.get(cls.WHISPER_MODEL, {
            "size": "Desconhecido",
            "speed": "Desconhecido",
            "quality": "Desconhecido"
        })
    
    @classmethod
    def validate_config(cls) -> dict:
        """Valida as configurações e retorna status"""
        issues = []
        
        # Validar modelo
        valid_models = ["tiny", "base", "small", "medium", "large-v3", "distil-large-v3"]
        if cls.WHISPER_MODEL not in valid_models:
            issues.append(f"Modelo inválido: {cls.WHISPER_MODEL}. Válidos: {valid_models}")
        
        # Validar device
        valid_devices = ["cpu", "cuda"]
        if cls.WHISPER_DEVICE not in valid_devices:
            issues.append(f"Device inválido: {cls.WHISPER_DEVICE}. Válidos: {valid_devices}")
        
        # Validar compute type
        valid_compute_types = ["int8", "int16", "float16", "float32"]
        if cls.WHISPER_COMPUTE_TYPE not in valid_compute_types:
            issues.append(f"Compute type inválido: {cls.WHISPER_COMPUTE_TYPE}. Válidos: {valid_compute_types}")
        
        # Validar threads
        if cls.OMP_NUM_THREADS < 1 or cls.OMP_NUM_THREADS > 32:
            issues.append(f"Número de threads inválido: {cls.OMP_NUM_THREADS}. Deve estar entre 1-32")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }

class DevelopmentConfig(Config):
    """Configurações para desenvolvimento"""
    DEBUG: bool = True
    RELOAD: bool = True
    LOG_LEVEL: str = "DEBUG"

class ProductionConfig(Config):
    """Configurações para produção"""
    DEBUG: bool = False
    RELOAD: bool = False
    LOG_LEVEL: str = "INFO"
    
    # Configurações mais conservadoras para produção
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    OMP_NUM_THREADS: int = 2

class TestConfig(Config):
    """Configurações para testes"""
    DEBUG: bool = True
    WHISPER_MODEL: str = "tiny"  # Modelo menor para testes rápidos
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB

def get_config() -> Config:
    """Retorna a configuração baseada na variável de ambiente"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionConfig()
    elif env == "test":
        return TestConfig()
    else:
        return DevelopmentConfig()

# Configuração global
config = get_config() 