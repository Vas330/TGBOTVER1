# config.py - исправленная версия с USE_FIREBASE
import os
import json
import tempfile

print("Загрузка конфигурации...")

# Основные переменные
BOT_TOKEN = os.getenv('BOT_TOKEN', '8394310213:AAHG-sJ_U11zIdrjTQ1b2SZMpNZ3ZWj25Vs')
ADMIN_ID = int(os.getenv('ADMIN_ID', '7014800288'))

# Firebase настройки
def setup_firebase():
    """Настройка Firebase с поддержкой Variables и файла"""
    firebase_creds = os.getenv('FIREBASE_CREDENTIALS')
    
    if firebase_creds:
        try:
            # Из переменной окружения Railway
            creds_dict = json.loads(firebase_creds)
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
            json.dump(creds_dict, temp_file, indent=2)
            temp_file.close()
            print("Firebase credentials загружены из Railway Variables")
            return temp_file.name
        except Exception as e:
            print(f"Ошибка переменной FIREBASE_CREDENTIALS: {e}")
    
    # Проверяем локальный файл
    if os.path.exists('serviceAccountKey.json'):
        print("Найден serviceAccountKey.json")
        return 'serviceAccountKey.json'
    
    print("Firebase credentials не найдены")
    return None

FIREBASE_KEY_PATH = setup_firebase()

# Остальные настройки
YOOMONEY_SHOP_ID = os.getenv('YOOMONEY_SHOP_ID', '410011929714361')
YOOMONEY_SECRET_KEY = os.getenv('YOOMONEY_SECRET_KEY', 'not_required_for_wallet')
LOGGING_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOGGING_LEVEL = 'INFO'
DEFAULT_RATING = 10.0
DEFAULT_BALANCE = 0.0
DEFAULT_CLIENT_STATUS = 'active'

# ВАЖНО: Добавляем USE_FIREBASE переменную
USE_FIREBASE = FIREBASE_KEY_PATH is not None

print("config.py загружен")
print(f"BOT_TOKEN: {'настроен' if BOT_TOKEN else 'отсутствует'}")
print(f"Firebase: {'настроен' if USE_FIREBASE else 'отключен'}")
print(f"FIREBASE_KEY_PATH: {FIREBASE_KEY_PATH}")
print(f"USE_FIREBASE: {USE_FIREBASE}")
