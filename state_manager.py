# state_manager.py
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from config import DATA_FILE, DEFAULT_BALANCE, DEFAULT_RATING, DEFAULT_CLIENT_STATUS


class UserState:
    def __init__(self, filename: str = DATA_FILE):
        self.filename = filename
        self.state: Dict[int, str] = {}
        self.entrepreneurs = self.load_entrepreneurs()
        self.clients = self.load_clients()
        self.orders = self.load_orders()
        self.active_chats = self.load_chats()
        self.portfolio_items = self.load_portfolio_items()

    def load_entrepreneurs(self) -> Dict[str, Dict[str, Any]]:
        """Загружает данные исполнителей из файла"""
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            entrepreneurs = data.get('entrepreneurs', {})

            # Добавляем баланс для существующих исполнителей, если его нет
            for login in entrepreneurs:
                if 'balance' not in entrepreneurs[login]:
                    entrepreneurs[login]['balance'] = DEFAULT_BALANCE
            return entrepreneurs
        except FileNotFoundError:
            return {}

    def load_clients(self) -> Dict[str, Dict[str, Any]]:
        """Загружает данные клиентов из файла"""
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('clients', {})
        except FileNotFoundError:
            return {}

    def load_orders(self) -> Dict[str, List[Dict[str, Any]]]:
        """Загружает заказы из файла"""
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('orders', {})
        except FileNotFoundError:
            return {}

    def load_chats(self) -> Dict[str, Dict[str, Any]]:
        """Загружает активные чаты из файла"""
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('active_chats', {})
        except FileNotFoundError:
            return {}

    def load_portfolio_items(self) -> Dict[str, List[Dict[str, Any]]]:
        """Загружает элементы портфолио из файла"""
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('portfolio_items', {})
        except FileNotFoundError:
            return {}

    def save_data(self) -> None:
        """Сохраняет все данные в файл"""
        data = {
            'entrepreneurs': self.entrepreneurs,
            'clients': self.clients,
            'orders': self.orders,
            'active_chats': self.active_chats,
            'portfolio_items': self.portfolio_items
        }
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    def set_state(self, user_id: int, state: Optional[str]) -> None:
        """Устанавливает состояние пользователя"""
        if state is None:
            self.state.pop(user_id, None)
        else:
            self.state[user_id] = state

    def get_state(self, user_id: int) -> Optional[str]:
        """Получает состояние пользователя"""
        return self.state.get(user_id)

    # === Методы для работы с исполнителями ===

    def register_entrepreneur(self, login: str, password: str, rating: int = DEFAULT_RATING,
                              chat_id: Optional[int] = None) -> None:
        """Регистрирует нового исполнителя"""
        self.entrepreneurs[login] = {
            'password': password,
            'rating': rating,
            'balance': DEFAULT_BALANCE
        }
        if chat_id is not None:
            self.entrepreneurs[login]['chat_id'] = chat_id
        self.save_data()

    def check_entrepreneur(self, login: str, password: str) -> bool:
        """Проверяет логин и пароль исполнителя"""
        if login in self.entrepreneurs:
            return self.entrepreneurs[login]['password'] == password
        return False

    def get_entrepreneur_by_chat_id(self, chat_id: int) -> Optional[str]:
        """Находит логин исполнителя по chat_id"""
        for login, data in self.entrepreneurs.items():
            if data.get('chat_id') == chat_id:
                return login
        return None

    def get_entrepreneur_rating(self, login: str) -> Optional[int]:
        """Получает рейтинг исполнителя"""
        if login in self.entrepreneurs:
            return self.entrepreneurs[login]['rating']
        return None

    def get_entrepreneur_balance(self, login: str) -> float:
        """Получает баланс исполнителя"""
        if login in self.entrepreneurs:
            return self.entrepreneurs[login].get('balance', DEFAULT_BALANCE)
        return DEFAULT_BALANCE

    def update_entrepreneur_rating(self, login: str, rating: int) -> bool:
        """Обновляет рейтинг исполнителя"""
        if login in self.entrepreneurs:
            self.entrepreneurs[login]['rating'] = rating
            self.save_data()
            return True
        return False

    def update_entrepreneur_balance(self, login: str, amount: float) -> bool:
        """Изменяет баланс исполнителя на указанную сумму"""
        if login in self.entrepreneurs:
            self.entrepreneurs[login]['balance'] += amount
            self.save_data()
            return True
        return False

    def set_entrepreneur_balance(self, login: str, balance: float) -> bool:
        """Устанавливает баланс исполнителя"""
        if login in self.entrepreneurs:
            self.entrepreneurs[login]['balance'] = balance
            self.save_data()
            return True
        return False

    def set_entrepreneur_chat_id(self, login: str, chat_id: int) -> bool:
        """Устанавливает chat_id для исполнителя"""
        if login in self.entrepreneurs:
            self.entrepreneurs[login]['chat_id'] = chat_id
            self.save_data()
            return True
        return False

    def remove_entrepreneur_chat_id(self, login: str) -> bool:
        """Убирает chat_id у исполнителя"""
        if login in self.entrepreneurs and 'chat_id' in self.entrepreneurs[login]:
            del self.entrepreneurs[login]['chat_id']
            self.save_data()
            return True
        return False

    def delete_entrepreneur(self, login: str) -> bool:
        """Удаляет исполнителя"""
        if login in self.entrepreneurs:
            del self.entrepreneurs[login]
            # Также удаляем его заказы
            if login in self.orders:
                del self.orders[login]
            self.save_data()
            return True
        return False

    def get_top_entrepreneur(self) -> Optional[str]:
        """Находит исполнителя с наивысшим рейтингом"""
        if not self.entrepreneurs:
            return None
        return max(self.entrepreneurs, key=lambda x: self.entrepreneurs[x]['rating'])

    def get_entrepreneurs_count(self) -> int:
        """Возвращает количество исполнителей"""
        return len(self.entrepreneurs)

    # === Методы для работы с клиентами ===

    def register_client(self, login: str, password: str, chat_id: Optional[int] = None) -> bool:
        """Регистрирует нового клиента"""
        if login in self.clients:
            return False  # Клиент уже существует

        self.clients[login] = {
            'password': password,
            'status': DEFAULT_CLIENT_STATUS,
            'created_at': datetime.now()
        }
        if chat_id is not None:
            self.clients[login]['chat_id'] = chat_id
        self.save_data()
        return True

    def check_client(self, login: str, password: str) -> bool:
        """Проверяет логин и пароль клиента"""
        if login in self.clients:
            return self.clients[login]['password'] == password
        return False

    def get_client_by_chat_id(self, chat_id: int) -> Optional[str]:
        """Находит логин клиента по chat_id"""
        for login, data in self.clients.items():
            if data.get('chat_id') == chat_id:
                return login
        return None

    def set_client_chat_id(self, login: str, chat_id: int) -> bool:
        """Устанавливает chat_id для клиента"""
        if login in self.clients:
            self.clients[login]['chat_id'] = chat_id
            self.save_data()
            return True
        return False

    def remove_client_chat_id(self, login: str) -> bool:
        """Убирает chat_id у клиента"""
        if login in self.clients and 'chat_id' in self.clients[login]:
            del self.clients[login]['chat_id']
            self.save_data()
            return True
        return False

    # === Методы для работы с заказами ===

    def add_order(self, contractor_login: str, order: Dict[str, Any]) -> None:
        """Добавляет заказ исполнителю"""
        if contractor_login not in self.orders:
            self.orders[contractor_login] = []
        self.orders[contractor_login].append(order)
        self.save_data()

    def get_orders(self, contractor_login: str) -> List[Dict[str, Any]]:
        """Получает заказы исполнителя"""
        return self.orders.get(contractor_login, [])

    def get_client_orders(self, client_login: str) -> List[Dict[str, Any]]:
        """Получает заказы клиента"""
        client_orders = []
        for contractor_login, orders in self.orders.items():
            for order in orders:
                if order.get('client_login') == client_login:
                    order['contractor_login'] = contractor_login
                    client_orders.append(order)
        return client_orders

    def update_order_timer(self, contractor_login: str, order_index: int, end_time: datetime) -> bool:
        """Обновляет таймер заказа"""
        if contractor_login in self.orders and order_index < len(self.orders[contractor_login]):
            self.orders[contractor_login][order_index]['timer_end'] = end_time
            self.orders[contractor_login][order_index]['timer_active'] = True
            self.save_data()
            return True
        return False

    def get_active_orders_with_timers(self) -> List[Dict[str, Any]]:
        """Получает все активные заказы с таймерами"""
        active_orders = []
        for contractor_login, orders in self.orders.items():
            for i, order in enumerate(orders):
                if order.get('timer_active', False):
                    order_copy = order.copy()
                    order_copy['contractor_login'] = contractor_login
                    order_copy['order_index'] = i
                    active_orders.append(order_copy)
        return active_orders

    # === Методы для работы с чатами ===

    def create_chat(self, client_login: str, client_chat_id: int, contractor_login: str, contractor_chat_id: int,
                    order_id: str) -> str:
        """Создает новый чат между клиентом и исполнителем"""
        chat_id = f"{client_login}_{contractor_login}_{order_id}"
        self.active_chats[chat_id] = {
            'client_login': client_login,
            'client_chat_id': client_chat_id,
            'contractor_login': contractor_login,
            'contractor_chat_id': contractor_chat_id,
            'order_id': order_id,
            'created_at': datetime.now(),
            'active': True
        }
        self.save_data()
        return chat_id

    def get_chat_by_user(self, user_chat_id: int) -> Optional[str]:
        """Находит активный чат по chat_id пользователя"""
        for chat_id, chat_data in self.active_chats.items():
            if chat_data.get('active', False):
                if (chat_data.get('client_chat_id') == user_chat_id or
                        chat_data.get('contractor_chat_id') == user_chat_id):
                    return chat_id
        return None

    def get_chat_partner(self, chat_id: str, user_chat_id: int) -> Optional[int]:
        """Получает chat_id партнера по чату"""
        if chat_id in self.active_chats:
            chat_data = self.active_chats[chat_id]
            if chat_data.get('client_chat_id') == user_chat_id:
                return chat_data.get('contractor_chat_id')
            elif chat_data.get('contractor_chat_id') == user_chat_id:
                return chat_data.get('client_chat_id')
        return None

    def get_chat_info(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """Получает информацию о чате"""
        return self.active_chats.get(chat_id)

    def close_chat(self, chat_id: str) -> bool:
        """Закрывает чат"""
        if chat_id in self.active_chats:
            self.active_chats[chat_id]['active'] = False
            self.save_data()
            return True
        return False

    def find_chat_for_order(self, client_login: str, contractor_login: str) -> Optional[str]:
        """Находит активный чат для заказа между клиентом и исполнителем"""
        for chat_id, chat_data in self.active_chats.items():
            if (chat_data.get('active', False) and
                    chat_data.get('client_login') == client_login and
                    chat_data.get('contractor_login') == contractor_login):
                return chat_id
        return None

    # === Методы для работы с портфолио ===

    def add_portfolio_item(self, category: str, title: str, description: str, images: List[str],
                           links: List[str] = None) -> None:
        """Добавляет элемент в портфолио"""
        print(f"DEBUG add_portfolio_item: category={category}, title={title}")

        if category not in self.portfolio_items:
            self.portfolio_items[category] = []
            print(f"DEBUG: Создана новая категория {category}")

        item = {
            'title': title,
            'description': description,
            'images': images,
            'links': links or [],
            'created_at': datetime.now()
        }

        self.portfolio_items[category].append(item)
        print(f"DEBUG: Добавлен элемент в категорию {category}. Всего элементов: {len(self.portfolio_items[category])}")

        # Сразу проверяем, что добавилось
        print(f"DEBUG: Содержимое портфолио: {self.portfolio_items}")

        self.save_data()
        print(f"DEBUG: Данные сохранены в файл")

    def get_portfolio_items(self, category: str) -> List[Dict[str, Any]]:
        """Получает элементы портфолио по категории"""
        items = self.portfolio_items.get(category, [])
        print(f"DEBUG get_portfolio_items: category={category}, found {len(items)} items")
        return items

    def delete_portfolio_item(self, category: str, index: int) -> bool:
        """Удаляет элемент портфолио"""
        if category in self.portfolio_items and 0 <= index < len(self.portfolio_items[category]):
            del self.portfolio_items[category][index]
            self.save_data()
            return True
        return False

    def get_all_categories(self) -> List[str]:
        """Получает все категории портфолио"""
        return list(self.portfolio_items.keys())


# Глобальный экземпляр состояния
user_state = UserState()