# utils.py - вспомогательные функции для обработки данных
import re


def is_valid_number(text: str) -> bool:
    """
    Проверяет, является ли строка валидным числом
    Поддерживает форматы: 1000, 1 000, 1,000, 1000.50, etc.
    """
    if not text or not isinstance(text, str):
        return False

    # Убираем пробелы и заменяем запятые на точки
    cleaned = text.strip().replace(' ', '').replace(',', '.')

    # Проверяем с помощью регулярного выражения
    # Позволяет числа вида: 123, 123.45, .45
    number_pattern = r'^\d*\.?\d+$'

    if re.match(number_pattern, cleaned):
        try:
            float(cleaned)
            return True
        except ValueError:
            return False

    return False


def parse_number(text: str) -> float:
    """
    Парсит строку в число
    Возвращает 0.0 если парсинг невозможен
    """
    if not is_valid_number(text):
        return 0.0

    # Убираем пробелы и заменяем запятые на точки
    cleaned = text.strip().replace(' ', '').replace(',', '.')

    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def format_order_info(description: str, deadline: str, budget: str, customer: str) -> str:
    """
    Форматирует информацию о заказе для отправки исполнителю
    """
    budget_num = parse_number(budget)

    formatted_info = f"""📋 ДЕТАЛИ ЗАКАЗА

📝 Описание: {description}

⏰ Сроки: {deadline}

💰 Бюджет: {budget_num:,.0f} руб.

👤 Заказчик: {customer}

Готовы взяться за этот проект?"""

    return formatted_info


def format_currency(amount: float) -> str:
    """
    Форматирует сумму в рублях с разделителями тысяч
    """
    return f"{amount:,.0f} руб.".replace(',', ' ')


def validate_phone(phone: str) -> bool:
    """
    Проверяет корректность номера телефона
    Поддерживает российские номера
    """
    if not phone or not isinstance(phone, str):
        return False

    # Убираем все лишние символы
    cleaned = re.sub(r'[^\d+]', '', phone.strip())

    # Паттерны для российских номеров
    patterns = [
        r'^\+7\d{10}$',  # +7XXXXXXXXXX
        r'^8\d{10}$',  # 8XXXXXXXXXX
        r'^7\d{10}$',  # 7XXXXXXXXXX
        r'^\d{10}$'  # XXXXXXXXXX
    ]

    return any(re.match(pattern, cleaned) for pattern in patterns)


def format_phone(phone: str) -> str:
    """
    Форматирует номер телефона в стандартный вид
    """
    if not validate_phone(phone):
        return phone

    # Убираем все лишние символы
    cleaned = re.sub(r'[^\d+]', '', phone.strip())

    # Приводим к формату +7XXXXXXXXXX
    if cleaned.startswith('+7') and len(cleaned) == 12:
        return cleaned
    elif cleaned.startswith('8') and len(cleaned) == 11:
        return '+7' + cleaned[1:]
    elif cleaned.startswith('7') and len(cleaned) == 11:
        return '+' + cleaned
    elif len(cleaned) == 10:
        return '+7' + cleaned

    return phone


def sanitize_string(text: str, max_length: int = 1000) -> str:
    """
    Очищает строку от потенциально опасных символов
    """
    if not text or not isinstance(text, str):
        return ""

    # Убираем лишние пробелы
    cleaned = ' '.join(text.split())

    # Ограничиваем длину
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length] + "..."

    return cleaned


def extract_order_id_from_state(state: str, prefix: str) -> str:
    """
    Извлекает ID заказа из состояния пользователя
    Например: 'in_client_chat_ORDER123' -> 'ORDER123'
    """
    if not state or not isinstance(state, str):
        return ""

    if state.startswith(prefix):
        return state[len(prefix):]

    return ""


def format_datetime(dt) -> str:
    """
    Форматирует дату и время для отображения
    Поддерживает Firebase Timestamp и datetime объекты
    """
    try:
        if hasattr(dt, 'toDate'):  # Firebase Timestamp
            date_obj = dt.toDate()
        elif hasattr(dt, 'seconds'):  # Firebase Timestamp dict
            from datetime import datetime
            date_obj = datetime.fromtimestamp(dt.seconds)
        elif hasattr(dt, 'strftime'):  # datetime объект
            date_obj = dt
        else:
            return "Неизвестно"

        return date_obj.strftime("%d.%m.%Y %H:%M")
    except:
        return "Неизвестно"


def get_user_role_display(role: str) -> str:
    """
    Возвращает человекочитаемое название роли
    """
    roles = {
        'customer': 'Заказчик',
        'client': 'Заказчик',
        'executor': 'Исполнитель',
        'entrepreneur': 'Исполнитель',
        'admin': 'Администратор'
    }
    return roles.get(role, 'Пользователь')


def validate_username(username: str) -> tuple[bool, str]:
    """
    Проверяет корректность имени пользователя
    Возвращает (is_valid, error_message)
    """
    if not username or not isinstance(username, str):
        return False, "Имя пользователя не может быть пустым"

    username = username.strip()

    if len(username) < 3:
        return False, "Имя пользователя должно содержать минимум 3 символа"

    if len(username) > 50:
        return False, "Имя пользователя не должно превышать 50 символов"

    # Разрешены только буквы, цифры и подчеркивание
    if not re.match(r'^[a-zA-Zа-яА-Я0-9_]+$', username):
        return False, "Имя пользователя может содержать только буквы, цифры и подчеркивание"

    return True, ""


def validate_password(password: str) -> tuple[bool, str]:
    """
    Проверяет корректность пароля
    Возвращает (is_valid, error_message)
    """
    if not password or not isinstance(password, str):
        return False, "Пароль не может быть пустым"

    if len(password) < 3:  # Упрощенное требование для тестирования
        return False, "Пароль должен содержать минимум 3 символа"

    if len(password) > 100:
        return False, "Пароль не должен превышать 100 символов"

    return True, ""


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Обрезает текст до указанной длины с добавлением суффикса
    """
    if not text or len(text) <= max_length:
        return text or ""

    return text[:max_length - len(suffix)] + suffix


def generate_order_id() -> str:
    """
    Генерирует уникальный ID для заказа
    """
    import secrets
    import string

    # Генерируем случайную строку из букв и цифр
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(12))


def is_admin_user(user_id: int, admin_ids: list = None) -> bool:
    """
    Проверяет, является ли пользователь администратором
    """
    from config import ADMIN_ID

    if admin_ids is None:
        admin_ids = [ADMIN_ID]

    return user_id in admin_ids


def debug_print(message: str, level: str = "INFO"):
    """
    Функция для отладочных сообщений
    """
    from datetime import datetime
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


# Константы для валидации
MAX_ORDER_TITLE_LENGTH = 200
MAX_ORDER_DESCRIPTION_LENGTH = 2000
MAX_MESSAGE_LENGTH = 4000
MIN_ORDER_AMOUNT = 100
MAX_ORDER_AMOUNT = 1000000