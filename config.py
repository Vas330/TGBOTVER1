# config.py - временно без Firebase для диагностики
import os

print("Загрузка конфигурации...")

# Основные переменные
BOT_TOKEN = os.getenv('BOT_TOKEN', '8394310213:AAHG-sJ_U11zIdrjTQ1b2SZMpNZ3ZWj25Vs')
ADMIN_ID = int(os.getenv('ADMIN_ID', '7014800288'))

# ВРЕМЕННО ОТКЛЮЧАЕМ FIREBASE
FIREBASE_KEY_PATH = None  # Отключено для диагностики
USE_FIREBASE = False

# YooMoney настройки  
YOOMONEY_SHOP_ID = os.getenv('YOOMONEY_SHOP_ID', '410011929714361')
YOOMONEY_SECRET_KEY = os.getenv('YOOMONEY_SECRET_KEY', 'not_required_for_wallet')

# Настройки логирования
LOGGING_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOGGING_LEVEL = 'INFO'

# Дефолтные значения
DEFAULT_RATING = 10.0
DEFAULT_BALANCE = 0.0
DEFAULT_CLIENT_STATUS = 'active'

print("Config загружен БЕЗ Firebase")
print(f"BOT_TOKEN: {'настроен' if BOT_TOKEN else 'отсутствует'}")
print(f"ADMIN_ID: {ADMIN_ID}")
print("ВНИМАНИЕ: Firebase временно отключен!")
