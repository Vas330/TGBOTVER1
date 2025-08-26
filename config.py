# config.py - исправленная версия для Railway
import os
import json
import tempfile
from dotenv import load_dotenv

# Загружаем переменные из .env (для локальной разработки)
load_dotenv()

print("Загрузка конфигурации...")

# Читаем переменные из окружения Railway
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', '7014800288'))

# Firebase настройки для Railway
def get_firebase_path():
    """Получает путь к Firebase credentials для Railway"""
    firebase_creds = os.getenv('FIREBASE_CREDENTIALS')
    
    if firebase_creds:
        try:
            # Парсим JSON из переменной окружения
            if isinstance(firebase_creds, str):
                creds_dict = json.loads(firebase_creds)
            else:
                creds_dict = firebase_creds
            
            # Создаем временный файл в Railway
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
            json.dump(creds_dict, temp_file, indent=2)
            temp_file.close()
            
            print("Firebase credentials загружены из переменной окружения Railway")
            return temp_file.name
            
        except json.JSONDecodeError as e:
            print(f"ОШИБКА: Неверный формат FIREBASE_CREDENTIALS: {e}")
            return None
        except Exception as e:
            print(f"ОШИБКА Firebase setup: {e}")
            return None
    else:
        # Для локальной разработки
        local_path = 'serviceAccountKey.json'
        if os.path.exists(local_path):
            print(f"Firebase credentials найдены локально: {local_path}")
            return local_path
        else:
            print("ВНИМАНИЕ: Firebase credentials не найдены!")
            return None

FIREBASE_KEY_PATH = get_firebase_path()

# YooMoney настройки
YOOMONEY_SHOP_ID = os.getenv('YOOMONEY_SHOP_ID', '410011929714361')
YOOMONEY_SECRET_KEY = os.getenv('YOOMONEY_SECRET_KEY', 'not_required_for_wallet')

# Настройки логирования
LOGGING_FORMAT = os.getenv('LOGGING_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
LOGGING_LEVEL = os.getenv('LOGGING_LEVEL', 'INFO')

# Дефолтные значения
DEFAULT_RATING = float(os.getenv('DEFAULT_RATING', '10.0'))
DEFAULT_BALANCE = float(os.getenv('DEFAULT_BALANCE', '0.0'))
DEFAULT_CLIENT_STATUS = os.getenv('DEFAULT_CLIENT_STATUS', 'active')

# Дополнительные переменные для Railway
PORT = int(os.getenv('PORT', '8000'))
RAILWAY_ENVIRONMENT = os.getenv('RAILWAY_ENVIRONMENT', 'production')

# Проверка критических переменных
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не установлен! Добавьте токен в переменные Railway")

if not FIREBASE_KEY_PATH:
    raise ValueError("❌ FIREBASE_CREDENTIALS не настроены! Добавьте JSON в переменные Railway")

# Логирование статуса загрузки
print("✅ config.py успешно загружен")
print(f"✅ BOT_TOKEN: {'Настроен' if BOT_TOKEN else 'Отсутствует'}")
print(f"✅ ADMIN_ID: {ADMIN_ID}")
print(f"✅ FIREBASE: {'Настроен' if FIREBASE_KEY_PATH else 'Отсутствует'}")
print(f"✅ YOOMONEY: {'Настроен' if YOOMONEY_SHOP_ID else 'Отсутствует'}")
print(f"✅ Railway Environment: {RAILWAY_ENVIRONMENT}")

# Экспортируем все необходимые переменные
__all__ = [
    'BOT_TOKEN', 'ADMIN_ID', 'FIREBASE_KEY_PATH',
    'YOOMONEY_SHOP_ID', 'YOOMONEY_SECRET_KEY',
    'LOGGING_FORMAT', 'LOGGING_LEVEL',
    'DEFAULT_RATING', 'DEFAULT_BALANCE', 'DEFAULT_CLIENT_STATUS'
]
