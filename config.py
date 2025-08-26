# config.py - улучшенная версия
import os
import json
import tempfile
from dotenv import load_dotenv

# Загружаем переменные из .env файла (для локальной разработки)
load_dotenv()

# ЗАМЕНИТЕ ЭТИ ДАННЫЕ НА ВАШИ РЕАЛЬНЫЕ:

# 1. Получите токен у @BotFather и вставьте вместо этой строки
BOT_TOKEN = os.getenv('BOT_TOKEN', '7304310213:AAMg-sJUUlziKrJTQlD2SZpAjZ2Zk32sVc')

# 2. Узнайте свой ID у @userinfobot и вставьте вместо 123456789
ADMIN_ID = int(os.getenv('ADMIN_ID', '7014800288'))

# Firebase настройки
def get_firebase_path():
    """Получает путь к файлу Firebase credentials"""
    firebase_creds = os.getenv('FIREBASE_CREDENTIALS')
    if firebase_creds:
        # Для Railway - создаем временный файл из переменной окружения
        try:
            # Парсим JSON из переменной окружения
            creds_dict = json.loads(firebase_creds)
            
            # Создаем временный файл
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
            json.dump(creds_dict, temp_file, indent=2)
            temp_file.close()
            
            print(f"Firebase credentials загружены из переменной окружения")
            return temp_file.name
        except json.JSONDecodeError as e:
            print(f"Ошибка парсинга FIREBASE_CREDENTIALS: {e}")
            return None
    else:
        # Для локальной разработки
        local_path = os.getenv('FIREBASE_KEY_PATH', 'serviceAccountKey.json')
        if os.path.exists(local_path):
            print(f"Firebase credentials загружены из файла: {local_path}")
            return local_path
        else:
            print(f"Файл Firebase credentials не найден: {local_path}")
            return None

FIREBASE_KEY_PATH = get_firebase_path()

# YooMoney настройки
YOOMONEY_SHOP_ID = os.getenv('YOOMONEY_SHOP_ID', '410011925714261')
YOOMONEY_SECRET_KEY = os.getenv('YOOMONEY_SECRET_KEY', 'not_required_for_wallet')

# Настройки логирования
LOGGING_FORMAT = os.getenv('LOGGING_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
LOGGING_LEVEL = os.getenv('LOGGING_LEVEL', 'INFO')

# Настройки рейтинга по умолчанию
DEFAULT_RATING = float(os.getenv('DEFAULT_RATING', '10.0'))
DEFAULT_BALANCE = float(os.getenv('DEFAULT_BALANCE', '0.0'))
DEFAULT_CLIENT_STATUS = os.getenv('DEFAULT_CLIENT_STATUS', 'active')

# Дополнительные настройки
DATABASE_URL = os.getenv('DATABASE_URL')  # Если используется
WEBHOOK_URL = os.getenv('WEBHOOK_URL')    # Если используется webhook
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

print("config.py загружен")

# Проверка обязательных переменных
if not BOT_TOKEN or BOT_TOKEN == 'your_bot_token_here':
    raise ValueError("BOT_TOKEN не установлен! Добавьте его в переменные окружения Railway")

if not FIREBASE_KEY_PATH:
    print("ВНИМАНИЕ: Firebase credentials не настроены!")

print(f"BOT_TOKEN: {'✓ Настроен' if BOT_TOKEN else '✗ Не найден'}")
print(f"ADMIN_ID: {ADMIN_ID}")
print(f"FIREBASE: {'✓ Настроен' if FIREBASE_KEY_PATH else '✗ Не найден'}")
print(f"YOOMONEY: {'✓ Настроен' if YOOMONEY_SHOP_ID else '✗ Не найден'}")
print(f"DEBUG режим: {DEBUG}")
