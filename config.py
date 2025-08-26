# config.py - исправленная версия с защитой от ошибок Firebase
import os
import json
import tempfile

print("Загрузка конфигурации...")

# Основные переменные
BOT_TOKEN = os.getenv('BOT_TOKEN', '8394310213:AAHG-sJ_U11zIdrjTQ1b2SZMpNZ3ZWj25Vs')
ADMIN_ID = int(os.getenv('ADMIN_ID', '7014800288'))

# Firebase с защитой от ошибок
def setup_firebase_safely():
    """Безопасная настройка Firebase"""
    try:
        firebase_creds = os.getenv('FIREBASE_CREDENTIALS')
        
        if firebase_creds:
            # Из переменной окружения Railway
            creds_dict = json.loads(firebase_creds)
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
            json.dump(creds_dict, temp_file, indent=2)
            temp_file.close()
            print("Firebase credentials загружены из Railway Variables")
            return temp_file.name
            
        elif os.path.exists('serviceAccountKey.json'):
            # Локальный файл - НО проверяем его валидность
            with open('serviceAccountKey.json', 'r') as f:
                data = json.load(f)
                # Проверяем ключевые поля
                required_fields = ['type', 'project_id', 'private_key', 'client_email']
                if all(field in data for field in required_fields):
                    print("Найден валидный локальный serviceAccountKey.json")
                    return 'serviceAccountKey.json'
                else:
                    print("ОШИБКА: serviceAccountKey.json поврежден - отсутствуют ключевые поля")
                    return None
        else:
            print("Firebase credentials не найдены")
            return None
            
    except json.JSONDecodeError as e:
        print(f"ОШИБКА: Неверный JSON в Firebase credentials: {e}")
        return None
    except Exception as e:
        print(f"ОШИБКА настройки Firebase: {e}")
        return None

FIREBASE_KEY_PATH = setup_firebase_safely()

# Остальные настройки
YOOMONEY_SHOP_ID = os.getenv('YOOMONEY_SHOP_ID', '410011929714361')
YOOMONEY_SECRET_KEY = os.getenv('YOOMONEY_SECRET_KEY', 'not_required_for_wallet')
LOGGING_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOGGING_LEVEL = 'INFO'
DEFAULT_RATING = 10.0
DEFAULT_BALANCE = 0.0
DEFAULT_CLIENT_STATUS = 'active'

print("config.py загружен")
print(f"BOT_TOKEN: {'настроен' if BOT_TOKEN else 'отсутствует'}")
print(f"Firebase: {'настроен' if FIREBASE_KEY_PATH else 'отключен'}")

# Флаг для использования Firebase
USE_FIREBASE = FIREBASE_KEY_PATH is not None
