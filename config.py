import os
from cryptography.fernet import Fernet

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-please-change'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///servers.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {'check_same_thread': False}
    }

    # Автоматически генерируем или загружаем ключ Fernet
    _key_file = 'fernet.key'
    if os.path.exists(_key_file):
        with open(_key_file, 'r') as f:
            FERNET_KEY = f.read().strip()
    else:
        FERNET_KEY = Fernet.generate_key().decode()
        with open(_key_file, 'w') as f:
            f.write(FERNET_KEY)

    # Для кэширования (если используется)
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 300
    COMPRESS_MIMETYPES = ['text/html', 'text/css', 'text/javascript', 'application/javascript', 'application/json']
    COMPRESS_LEVEL = 6
    COMPRESS_MIN_SIZE = 500