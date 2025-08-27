# config.py - для работы с отдельными Firebase переменными
import os
import json
import tempfile

print("Загрузка конфигурации...")

# Основные переменные
BOT_TOKEN = os.getenv('BOT_TOKEN', '8274498333:AAHqgvtdBNyTJrZdJGpjd7eRX5bKIKjNLCM')
ADMIN_ID = int(os.getenv('ADMIN_ID', '7014800288'))

def setup_firebase():
    """Настройка Firebase из отдельных переменных"""
    
    # Вариант 1: Полная переменная FIREBASE_CREDENTIALS
    firebase_creds = os.getenv('FIREBASE_CREDENTIALS')
    if firebase_creds:
        try:
            creds_dict = json.loads(firebase_creds)
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
            json.dump(creds_dict, temp_file, indent=2)
            temp_file.close()
            print("Firebase credentials загружены из FIREBASE_CREDENTIALS")
            return temp_file.name
        except Exception as e:
            print(f"Ошибка FIREBASE_CREDENTIALS: {e}")
    
    # Вариант 2: Отдельные переменные (как у вас)
    firebase_fields = {
        'type': os.getenv('type'),
        'project_id': os.getenv('project_id'),
        'private_key_id': os.getenv('private_key_id'),
        'private_key': os.getenv('private_key'),
        'client_email': os.getenv('client_email'),
        'client_id': os.getenv('client_id'),
        'auth_uri': os.getenv('auth_uri'),
        'token_uri': os.getenv('token_uri'),
        'auth_provider_x509_cert_url': os.getenv('auth_provider_x509_cert_url'),
        'client_x509_cert_url': os.getenv('client_x509_cert_url'),
        'universe_domain': os.getenv('universe_domain')
    }
    
    # Проверяем что все ключевые поля есть
    required_fields = ['type', 'project_id', 'private_key', 'client_email']
    if all(firebase_fields.get(field) for field in required_fields):
        try:
            # Собираем JSON из отдельных переменных
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
            json.dump(firebase_fields, temp_file, indent=2)
            temp_file.close()
            print("Firebase credentials собраны из отдельных переменных")
            print(f"Project ID: {firebase_fields['project_id']}")
            print(f"Client Email: {firebase_fields['client_email'][:50]}...")
            return temp_file.name
        except Exception as e:
            print(f"Ошибка сборки Firebase из переменных: {e}")
    
    # Вариант 3: Локальный файл
    if os.path.exists('serviceAccountKey.json'):
        print("Найден локальный serviceAccountKey.json")
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

# Флаг использования Firebase
USE_FIREBASE = FIREBASE_KEY_PATH is not None

print("config.py загружен")
print(f"BOT_TOKEN: {'настроен' if BOT_TOKEN else 'отсутствует'}")
print(f"Firebase: {'настроен' if USE_FIREBASE else 'отключен'}")
print(f"USE_FIREBASE: {USE_FIREBASE}")

