import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    
    # Flask-Session configuration
    SESSION_TYPE = 'filesystem'  # Можно использовать 'redis' если установлен Redis
    SESSION_FILE_DIR = './flask_session/'  # Директория для хранения файлов сессий
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)  # Время жизни сессии
    SESSION_FILE_THRESHOLD = 500  # Максимальное количество сессий
    SESSION_USE_SIGNER = True  # Использовать подпись для безопасности
    SESSION_KEY_PREFIX = 'fefu_calc:'  # Префикс для ключей сессии

    
    # Увеличиваем размер cookie для обычной сессии (на всякий случай)
    SESSION_COOKIE_NAME = 'fefu_calc_session'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # Установите True для HTTPS
    SESSION_COOKIE_SAMESITE = 'Lax'