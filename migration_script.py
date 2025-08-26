# migration_script.py - добавляет telegram_id к существующим пользователям
import firebase_admin
from firebase_admin import credentials, firestore

# Путь к ключу Firebase
SERVICE_ACCOUNT_PATH = 'serviceAccountKey.json'


def init_firebase():
    """Инициализация Firebase"""
    if not firebase_admin._apps:
        cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
        firebase_admin.initialize_app(cred)
    return firestore.client()


def migrate_users():
    """Добавляет telegram_id ко всем пользователям, у которых его нет"""
    db = init_firebase()

    # Получаем всех пользователей
    users_ref = db.collection('users')
    users = users_ref.stream()

    updated_count = 0
    total_count = 0

    for user_doc in users:
        total_count += 1
        user_data = user_doc.to_dict()
        user_id = user_doc.id

        print(f"Обрабатываем пользователя {user_id}: {user_data.get('username', 'Без имени')}")

        # Проверяем, есть ли уже telegram_id
        if 'telegram_id' not in user_data:
            # Берем значение из chat_id
            chat_id = user_data.get('chat_id')

            if chat_id:
                # Добавляем telegram_id
                users_ref.document(user_id).update({
                    'telegram_id': str(chat_id)
                })
                print(f"  ✅ Добавлен telegram_id: {chat_id}")
                updated_count += 1
            else:
                print(f"  ⚠️ Нет chat_id, пропускаем")
        else:
            print(f"  ℹ️ telegram_id уже существует: {user_data['telegram_id']}")

    print(f"\nМиграция завершена!")
    print(f"Всего пользователей: {total_count}")
    print(f"Обновлено: {updated_count}")


if __name__ == "__main__":
    try:
        migrate_users()
    except Exception as e:
        print(f"Ошибка миграции: {e}")
        import traceback

        traceback.print_exc()