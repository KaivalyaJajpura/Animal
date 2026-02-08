"""
Config module for Flask app
Handles environment-specific configurations
"""
import os
from datetime import timedelta

class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = False
    TESTING = False
    
    # Database configuration
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'users.db')
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_REFRESH_EACH_REQUEST = True
    
    # Flask configuration
    JSON_SORT_KEYS = False
    
    # Scheduler configuration
    ENABLE_SCHEDULER = os.getenv('ENABLE_SCHEDULER', 'True').lower() == 'true'
    SCHEDULER_INTERVAL_MINUTES = int(os.getenv('SCHEDULER_INTERVAL_MINUTES', 5))

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    ENABLE_SCHEDULER = True  # Enable scheduler in development

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    ENABLE_SCHEDULER = False  # Disable scheduler in serverless environment
    
    # Ensure SECRET_KEY is set in production
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable must be set in production")

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    ENABLE_SCHEDULER = False

def get_config():
    """Get the appropriate configuration based on environment"""
    env = os.getenv('FLASK_ENV', 'development')
    
    if env == 'production':
        return ProductionConfig
    elif env == 'testing':
        return TestingConfig
    else:
        return DevelopmentConfig
