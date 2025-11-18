import os
from datetime import timedelta

class Config:
    """Configuración base de la aplicación"""
    
    # Configuración básica de Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-positiva-2024'
    
    # Configuración de carpetas
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    OUTPUT_FOLDER = os.path.join(BASE_DIR, 'outputs')
    
    # Configuración de archivos
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB máximo
    ALLOWED_EXTENSIONS = set(os.environ.get('ALLOWED_EXTENSIONS', 'xlsx,xls,xlsb').split(','))
    
    # Configuración de sesión
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Información de la empresa
    COMPANY_NAME = 'Positiva Compañía de Seguros'
    SYSTEM_NAME = 'Sistema de Automatización'
    VERSION = '1.0.0'


class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False
    TESTING = False


# Diccionario de configuraciones
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}