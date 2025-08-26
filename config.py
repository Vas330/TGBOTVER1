# config.py - упрощенная версия
import os

# ЗАМЕНИТЕ ЭТИ ДАННЫЕ НА ВАШИ РЕАЛЬНЫЕ:

# 1. Получите токен у @BotFather и вставьте вместо этой строки
BOT_TOKEN = '8394310213:AAHG-sJ_U11zIdrjTQ1b2SZMpNZ3ZWj25Vs'

# 2. Узнайте свой ID у @userinfobot и вставьте вместо 123456789
ADMIN_ID = 7014800288

# Остальные настройки (не трогать)
FIREBASE_KEY_PATH = 'serviceAccountKey.json'
YOOMONEY_SHOP_ID = '410011929714361'
YOOMONEY_SECRET_KEY = 'not_required_for_wallet'
LOGGING_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOGGING_LEVEL = 'INFO'
DEFAULT_RATING = 10.0
DEFAULT_BALANCE = 0.0
DEFAULT_CLIENT_STATUS = 'active'

print("config.py загружен")