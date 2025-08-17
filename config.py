# config.py
import os

# Токен бота (рекомендуется вынести в переменные окружения)
BOT_TOKEN = os.getenv('BOT_TOKEN', '8474585568:AAG1ysNj9LYOOzePcKx0pcAgZ4uc4i-Al7M')

# ID администратора
ADMIN_ID = 7014800288

# Путь к файлу данных
DATA_FILE = 'data.json'

# Начальный рейтинг для новых исполнителей
DEFAULT_RATING = 10

# Начальный баланс для новых исполнителей
DEFAULT_BALANCE = 0

# Настройки для клиентов
DEFAULT_CLIENT_STATUS = 'active'

# Логирование
LOGGING_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOGGING_LEVEL = 'INFO'