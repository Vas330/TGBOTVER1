# utils.py
import re
from typing import Optional, Tuple
from datetime import datetime, timedelta


def format_order_info(description: str, deadline: str, budget: str, client_login: str = "Не указан") -> str:
    """Форматирует информацию о заказе"""
    return (f"Новый заказ:\n"
            f"Описание: {description}\n"
            f"Сроки: {deadline}\n"
            f"Бюджет: {budget}\n"
            f"Заказчик: {client_login}")


def is_valid_number(text: str) -> bool:
    """Проверяет, является ли строка корректным числом"""
    try:
        float(text.replace(' ', ''))
        return True
    except ValueError:
        return False


def parse_number(text: str) -> Optional[float]:
    """Парсит число из строки"""
    try:
        return float(text.replace(' ', ''))
    except ValueError:
        return None


def is_valid_rating(rating: int) -> bool:
    """Проверяет, корректен ли рейтинг"""
    return 1 <= rating <= 10


def format_entrepreneur_info(login: str, password: str, rating: int, balance: float, chat_id: Optional[int]) -> str:
    """Форматирует информацию об исполнителе"""
    chat_id_str = str(chat_id) if chat_id is not None else 'Не указан'
    return (f"Логин: {login}\n"
            f"Пароль: {password}\n"
            f"Рейтинг: {rating}/10\n"
            f"Баланс: {balance} руб.\n"
            f"Chat ID: {chat_id_str}")


def format_entrepreneur_list_item(login: str, rating: int, balance: float) -> str:
    """Форматирует элемент списка исполнителей"""
    return f"{login} (★{rating} | {balance}₽)"


def parse_deadline_to_hours(deadline_text: str) -> Optional[int]:
    """
    Парсит время из текста сроков в часы.
    Поддерживает форматы:
    - "2 дня" -> 48 часов
    - "3 часа" -> 3 часа
    - "1 неделя" -> 168 часов
    - "30 минут" -> 0.5 часа (округляется до 1)
    """
    deadline_text = deadline_text.lower().strip()

    # Регулярные выражения для разных форматов
    patterns = [
        (r'(\d+)\s*(?:дня|день|дней)', lambda x: int(x) * 24),
        (r'(\d+)\s*(?:часа|час|часов)', lambda x: int(x)),
        (r'(\d+)\s*(?:недели|неделя|недель)', lambda x: int(x) * 24 * 7),
        (r'(\d+)\s*(?:минут|минута|минуты)', lambda x: max(1, int(x) // 60)),  # минимум 1 час
    ]

    for pattern, converter in patterns:
        match = re.search(pattern, deadline_text)
        if match:
            return converter(match.group(1))

    return None


def calculate_end_time(deadline_text: str) -> Optional[datetime]:
    """Вычисляет время окончания заказа на основе текста сроков"""
    hours = parse_deadline_to_hours(deadline_text)
    if hours:
        return datetime.now() + timedelta(hours=hours)
    return None


def format_time_remaining(end_time: datetime) -> str:
    """Форматирует оставшееся время до окончания"""
    now = datetime.now()
    if now >= end_time:
        return "⏰ Время истекло!"

    diff = end_time - now
    days = diff.days
    hours, remainder = divmod(diff.seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    if days > 0:
        return f"⏱ Осталось: {days} дн. {hours} ч. {minutes} мин."
    elif hours > 0:
        return f"⏱ Осталось: {hours} ч. {minutes} мин."
    else:
        return f"⏱ Осталось: {minutes} мин."


def is_order_expired(end_time: datetime) -> bool:
    """Проверяет, истек ли срок заказа"""
    return datetime.now() >= end_time


def get_user_role_in_chat(user_chat_id: int, chat_data: dict) -> str:
    """Определяет роль пользователя в чате (client/contractor)"""
    if chat_data.get('client_chat_id') == user_chat_id:
        return 'client'
    elif chat_data.get('contractor_chat_id') == user_chat_id:
        return 'contractor'
    return 'unknown'


def format_chat_message(sender_role: str, message: str) -> str:
    """Форматирует сообщение для чата"""
    role_name = "👤 Заказчик" if sender_role == 'client' else "👨‍💼 Исполнитель"
    return f"{role_name}: {message}"