# config.py - упрощенная версия (исправленная для Railway)
import os
import json
import tempfile

# Читаем из переменных окружения Railway, с fallback на ваши значения
BOT_TOKEN = os.getenv('BOT_TOKEN', '8394310213:AAHG-sJ_U11zIdrjTQ1b2SZMpNZ3ZWj25Vs')
ADMIN_ID = int(os.getenv('ADMIN_ID', '7014800288'))

# Firebase настройки для Railway
def setup_firebase():
    """Настройка Firebase для Railway"""
    firebase_creds = os.getenv('FIREBASE_CREDENTIALS')
    
    if firebase_creds:
        try:
            # Создаем временный файл из переменной окружения
            creds_dict = json.loads(firebase_creds)
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
            json.dump(creds_dict, temp_file, indent=2)
            temp_file.close()
            print("Firebase credentials загружены из Railway Variables")
            return temp_file.name
        except Exception as e:
            print(f"Ошибка создания Firebase файла: {e}")
    
    # Fallback на локальный файл (если есть)
    if os.path.exists('serviceAccountKey.json'):
        print("Используем локальный serviceAccountKey.json")
        return 'serviceAccountKey.json'
    
    print("ВНИМАНИЕ: Firebase credentials не найдены!")
    return 'serviceAccountKey.json'

FIREBASE_KEY_PATH = setup_firebase()

# Остальные настройки (ваши значения с возможностью переопределения)
YOOMONEY_SHOP_ID = os.getenv('YOOMONEY_SHOP_ID', '410011929714361')
YOOMONEY_SECRET_KEY = os.getenv('YOOMONEY_SECRET_KEY', 'not_required_for_wallet')
LOGGING_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOGGING_LEVEL = 'INFO'
DEFAULT_RATING = 10.0
DEFAULT_BALANCE = 0.0
DEFAULT_CLIENT_STATUS = 'active'

print("config.py загружен")
