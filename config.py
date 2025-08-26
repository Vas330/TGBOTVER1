# config.py - версия для отладки Firebase
import os
import json

print("Загрузка конфигурации...")

# Основные переменные
BOT_TOKEN = os.getenv('BOT_TOKEN', '8394310213:AAHG-sJ_U11zIdrjTQ1b2SZMpNZ3ZWj25Vs')
ADMIN_ID = int(os.getenv('ADMIN_ID', '7014800288'))

# Отладка Firebase
def debug_firebase():
    """Отладка проблем с Firebase"""
    print("=== ОТЛАДКА FIREBASE ===")
    
    # Проверяем существование файла
    if os.path.exists('serviceAccountKey.json'):
        print("✓ Файл serviceAccountKey.json найден")
        
        # Проверяем размер файла
        size = os.path.getsize('serviceAccountKey.json')
        print(f"Размер файла: {size} байт")
        
        try:
            # Читаем и проверяем JSON
            with open('serviceAccountKey.json', 'r') as f:
                data = json.load(f)
            
            print("✓ JSON валидный")
            print(f"Проект: {data.get('project_id', 'НЕ НАЙДЕН')}")
            print(f"Client email: {data.get('client_email', 'НЕ НАЙДЕН')[:50]}...")
            
            # Проверяем приватный ключ
            private_key = data.get('private_key', '')
            if private_key:
                print(f"Private key длина: {len(private_key)} символов")
                print(f"Начинается с: {private_key[:50]}")
                print(f"Заканчивается на: {private_key[-50:]}")
                
                # Проверяем формат приватного ключа
                if '-----BEGIN PRIVATE KEY-----' in private_key:
                    print("✓ Private key имеет правильный заголовок")
                else:
                    print("✗ ОШИБКА: Private key не имеет заголовка")
                    
                if '-----END PRIVATE KEY-----' in private_key:
                    print("✓ Private key имеет правильный финал")
                else:
                    print("✗ ОШИБКА: Private key не имеет финала")
                    
                # Проверяем переводы строк
                if '\\n' in private_key:
                    print("✓ Private key содержит \\n (правильно)")
                else:
                    print("✗ ПРЕДУПРЕЖДЕНИЕ: Private key может быть без \\n")
                    
            else:
                print("✗ ОШИБКА: Private key отсутствует")
                
            return 'serviceAccountKey.json'
            
        except json.JSONDecodeError as e:
            print(f"✗ ОШИБКА JSON: {e}")
            return None
        except Exception as e:
            print(f"✗ ОШИБКА чтения файла: {e}")
            return None
    else:
        print("✗ Файл serviceAccountKey.json НЕ НАЙДЕН")
        print("Содержимое директории:")
        try:
            files = os.listdir('.')
            for file in files:
                print(f"  - {file}")
        except:
            print("  Не удалось прочитать директорию")
        return None

FIREBASE_KEY_PATH = debug_firebase()

# Остальные настройки
YOOMONEY_SHOP_ID = os.getenv('YOOMONEY_SHOP_ID', '410011929714361')
YOOMONEY_SECRET_KEY = os.getenv('YOOMONEY_SECRET_KEY', 'not_required_for_wallet')
LOGGING_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOGGING_LEVEL = 'INFO'
DEFAULT_RATING = 10.0
DEFAULT_BALANCE = 0.0
DEFAULT_CLIENT_STATUS = 'active'

USE_FIREBASE = FIREBASE_KEY_PATH is not None

print("========================")
print("config.py загружен")
print(f"Firebase будет: {'использоваться' if USE_FIREBASE else 'отключен'}")
