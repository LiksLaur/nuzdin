import os
from dotenv import load_dotenv

load_dotenv()


# конфигурация +  подключение к бд  и логирование 
class Config:
    DATABASE_HOST = os.getenv('DATABASE_HOST', 'localhost')
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'nuzdin_db')
    DATABASE_USER = os.getenv('DATABASE_USER', 'postgres')
    DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD', '')
    DATABASE_PORT = os.getenv('DATABASE_PORT', '5432')
    
    DATABASE_URL = os.getenv(
        'DATABASE_URL',
        f"postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
    )
    
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
