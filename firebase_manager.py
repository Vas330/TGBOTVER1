# firebase_manager.py - исправленная версия с улучшенной аутентификацией
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import json
import os
from config import DEFAULT_RATING, DEFAULT_BALANCE, DEFAULT_CLIENT_STATUS


class FirebaseManager:
    def __init__(self, credentials_path: str = None):
        """Инициализация Firebase Manager"""
        try:
            # Проверяем, не инициализирован ли уже Firebase
            if not firebase_admin._apps:
                print("Инициализация Firebase...")
                
                # Пытаемся загрузить credentials разными способами
                if credentials_path and os.path.exists(credentials_path):
                    print(f"Загружаем credentials из файла: {credentials_path}")
                    cred = credentials.Certificate(credentials_path)
                else:
                    print("Файл credentials не найден, пытаемся использовать переменные окружения...")
                    # Пытаемся собрать из переменных окружения
                    cred_dict = self._get_credentials_from_env()
                    if cred_dict:
                        print("Credentials собраны из переменных окружения")
                        cred = credentials.Certificate(cred_dict)
                    else:
                        raise ValueError("Не удалось найти Firebase credentials")

                # Инициализируем Firebase
                firebase_admin.initialize_app(cred)
                print("Firebase успешно инициализирован!")
            else:
                print("Firebase уже инициализирован")

            # Получаем клиент Firestore
            self.db = firestore.client()
            print("Firestore клиент создан")
            
            # Проверяем соединение
            self._test_connection()
            
        except Exception as e:
            print(f"КРИТИЧЕСКАЯ ОШИБКА при инициализации Firebase: {e}")
            import traceback
            traceback.print_exc()
            raise

    def _get_credentials_from_env(self):
        """Собираем credentials из переменных окружения"""
        try:
            # Сначала пытаемся прочитать полный JSON из FIREBASE_CREDENTIALS
            firebase_credentials = os.getenv('FIREBASE_CREDENTIALS')
            if firebase_credentials:
                print("Найдена переменная FIREBASE_CREDENTIALS")
                try:
                    cred_dict = json.loads(firebase_credentials)
                    print("JSON credentials успешно распарсен")
                    return cred_dict
                except json.JSONDecodeError as e:
                    print(f"Ошибка парсинга JSON из FIREBASE_CREDENTIALS: {e}")
            
            # Если нет полного JSON, пытаемся собрать из отдельных переменных
            required_vars = [
                'FIREBASE_PROJECT_ID', 'FIREBASE_PRIVATE_KEY', 'FIREBASE_CLIENT_EMAIL'
            ]
            
            for var in required_vars:
                if not os.getenv(var):
                    print(f"Переменная окружения {var} не найдена")
                    return None
            
            # Собираем словарь credentials
            cred_dict = {
                "type": "service_account",
                "project_id": os.getenv('FIREBASE_PROJECT_ID'),
                "private_key": os.getenv('FIREBASE_PRIVATE_KEY').replace('\\n', '\n'),
                "client_email": os.getenv('FIREBASE_CLIENT_EMAIL'),
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
            }
            
            # Добавляем дополнительные поля если есть
            if os.getenv('FIREBASE_PRIVATE_KEY_ID'):
                cred_dict["private_key_id"] = os.getenv('FIREBASE_PRIVATE_KEY_ID')
            if os.getenv('FIREBASE_CLIENT_ID'):
                cred_dict["client_id"] = os.getenv('FIREBASE_CLIENT_ID')
                
            return cred_dict
            
        except Exception as e:
            print(f"Ошибка сборки credentials из переменных: {e}")
            return None

    def _test_connection(self):
        """Тестируем соединение с Firebase"""
        try:
            # Пытаемся получить список коллекций или создать тестовый документ
            test_ref = self.db.collection('test').document('connection_test')
            test_ref.set({
                'test': True,
                'timestamp': datetime.now()
            })
            print("✅ Соединение с Firebase работает")
            
            # Удаляем тестовый документ
            test_ref.delete()
            
        except Exception as e:
            print(f"❌ Ошибка при тестировании соединения: {e}")
            raise

    # МЕТОДЫ СОСТОЯНИЙ ПОЛЬЗОВАТЕЛЕЙ
    def set_user_state(self, user_id: int, state: str) -> None:
        """Устанавливает состояние пользователя"""
        try:
            states_ref = self.db.collection('user_states').document(str(user_id))
            states_ref.set({
                'user_id': str(user_id),
                'state': state,
                'updated_at': datetime.now()
            })
        except Exception as e:
            print(f"Ошибка установки состояния пользователя {user_id}: {e}")

    def get_user_state(self, user_id: int) -> str:
        """Получает состояние пользователя"""
        try:
            states_ref = self.db.collection('user_states').document(str(user_id))
            doc = states_ref.get()
            if doc.exists:
                return doc.to_dict().get('state', '')
            return ''
        except Exception as e:
            print(f"Ошибка получения состояния пользователя {user_id}: {e}")
            return ''

    def clear_user_state(self, user_id: int) -> None:
        """Очищает состояние пользователя"""
        try:
            states_ref = self.db.collection('user_states').document(str(user_id))
            states_ref.delete()
        except Exception as e:
            print(f"Ошибка очистки состояния пользователя {user_id}: {e}")

    # МЕТОДЫ РАБОТЫ С КЛИЕНТАМИ
    def get_client_by_chat_id(self, chat_id: int) -> str:
        """Получает логин клиента по chat_id"""
        try:
            users_ref = self.db.collection('users')
            query = users_ref.where(field_path='chat_id', op_string='==', value=chat_id).where(field_path='role', op_string='==', value='client')
            docs = query.get()
            
            for doc in docs:
                data = doc.to_dict()
                return data.get('username')
            return None
        except Exception as e:
            print(f"Ошибка получения клиента по chat_id {chat_id}: {e}")
            return None

    def register_client(self, username: str, password: str, chat_id: int = None, telegram_id: str = None) -> bool:
        """Регистрирует нового клиента"""
        try:
            users_ref = self.db.collection('users')
            
            # Проверяем, существует ли пользователь
            existing_query = users_ref.where(field_path='username', op_string='==', value=username)
            existing_docs = existing_query.get()
            
            if existing_docs:
                return False  # Пользователь уже существует
            
            # Создаем нового клиента
            client_data = {
                'username': username,
                'password': password,  # В реальном проекте должно быть зашифровано
                'role': 'client',
                'status': DEFAULT_CLIENT_STATUS,
                'created_at': datetime.now(),
                'telegram_id': telegram_id or str(chat_id) if chat_id else None,
                'chat_id': chat_id
            }
            
            users_ref.document(username).set(client_data)
            print(f"Клиент {username} зарегистрирован успешно")
            return True
            
        except Exception as e:
            print(f"Ошибка регистрации клиента {username}: {e}")
            return False

    def check_client(self, username: str, password: str) -> bool:
        """Проверяет данные клиента для входа"""
        try:
            users_ref = self.db.collection('users').document(username)
            doc = users_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                return (data.get('password') == password and 
                       data.get('role') == 'client' and
                       data.get('status') == 'active')
            return False
            
        except Exception as e:
            print(f"Ошибка проверки клиента {username}: {e}")
            return False

    def set_client_chat_id(self, username: str, chat_id: int) -> None:
        """Устанавливает chat_id для клиента"""
        try:
            users_ref = self.db.collection('users').document(username)
            users_ref.update({
                'chat_id': chat_id,
                'last_login': datetime.now()
            })
        except Exception as e:
            print(f"Ошибка установки chat_id для клиента {username}: {e}")

    # МЕТОДЫ РАБОТЫ С ИСПОЛНИТЕЛЯМИ
    def get_entrepreneur_by_chat_id(self, chat_id: int) -> str:
        """Получает логин исполнителя по chat_id"""
        try:
            users_ref = self.db.collection('users')
            query = users_ref.where(field_path='chat_id', op_string='==', value=chat_id).where(field_path='role', op_string='==', value='entrepreneur')
            docs = query.get()
            
            for doc in docs:
                data = doc.to_dict()
                return data.get('username')
            return None
        except Exception as e:
            print(f"Ошибка получения исполнителя по chat_id {chat_id}: {e}")
            return None

    def register_entrepreneur(self, username: str, password: str, chat_id: int = None, telegram_id: str = None) -> bool:
        """Регистрирует нового исполнителя"""
        try:
            users_ref = self.db.collection('users')
            
            # Проверяем, существует ли пользователь
            existing_query = users_ref.where(field_path='username', op_string='==', value=username)
            existing_docs = existing_query.get()
            
            if existing_docs:
                print(f"Исполнитель {username} уже существует, обновляем данные")
                # Обновляем существующего
                users_ref.document(username).update({
                    'chat_id': chat_id,
                    'telegram_id': telegram_id or str(chat_id) if chat_id else None,
                    'last_login': datetime.now()
                })
            else:
                # Создаем нового исполнителя
                entrepreneur_data = {
                    'username': username,
                    'password': password,
                    'role': 'entrepreneur',
                    'status': 'active',
                    'balance': DEFAULT_BALANCE,
                    'rating': DEFAULT_RATING,
                    'completed_orders': 0,
                    'created_at': datetime.now(),
                    'telegram_id': telegram_id or str(chat_id) if chat_id else None,
                    'chat_id': chat_id
                }
                
                users_ref.document(username).set(entrepreneur_data)
                print(f"Исполнитель {username} зарегистрирован успешно")
            
            return True
            
        except Exception as e:
            print(f"Ошибка регистрации исполнителя {username}: {e}")
            return False

    def check_entrepreneur(self, username: str, password: str) -> bool:
        """Проверяет данные исполнителя для входа"""
        try:
            users_ref = self.db.collection('users').document(username)
            doc = users_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                return (data.get('password') == password and 
                       data.get('role') == 'entrepreneur' and
                       data.get('status') == 'active')
            return False
            
        except Exception as e:
            print(f"Ошибка проверки исполнителя {username}: {e}")
            return False

    def set_entrepreneur_chat_id(self, username: str, chat_id: int) -> None:
        """Устанавливает chat_id для исполнителя"""
        try:
            users_ref = self.db.collection('users').document(username)
            users_ref.update({
                'chat_id': chat_id,
                'last_login': datetime.now()
            })
        except Exception as e:
            print(f"Ошибка установки chat_id для исполнителя {username}: {e}")

    def get_balance(self, username: str) -> float:
        """Получает баланс исполнителя"""
        try:
            users_ref = self.db.collection('users').document(username)
            doc = users_ref.get()
            
            if doc.exists:
                return doc.to_dict().get('balance', 0.0)
            return 0.0
            
        except Exception as e:
            print(f"Ошибка получения баланса {username}: {e}")
            return 0.0

    def update_balance(self, username: str, amount: float) -> bool:
        """Обновляет баланс исполнителя"""
        try:
            users_ref = self.db.collection('users').document(username)
            doc = users_ref.get()
            
            if doc.exists:
                current_balance = doc.to_dict().get('balance', 0.0)
                new_balance = current_balance + amount
                
                users_ref.update({
                    'balance': new_balance,
                    'updated_at': datetime.now()
                })
                print(f"Баланс {username} обновлен: {current_balance} -> {new_balance}")
                return True
            return False
            
        except Exception as e:
            print(f"Ошибка обновления баланса {username}: {e}")
            return False

    def get_rating(self, username: str) -> float:
        """Получает рейтинг исполнителя"""
        try:
            users_ref = self.db.collection('users').document(username)
            doc = users_ref.get()
            
            if doc.exists:
                return doc.to_dict().get('rating', DEFAULT_RATING)
            return DEFAULT_RATING
            
        except Exception as e:
            print(f"Ошибка получения рейтинга {username}: {e}")
            return DEFAULT_RATING

    def get_top_executor(self) -> str:
        """Получает исполнителя с наивысшим рейтингом"""
        try:
            users_ref = self.db.collection('users')
            query = users_ref.where(field_path='role', op_string='==', value='entrepreneur').where(field_path='status', op_string='==', value='active')
            docs = query.get()
            
            best_executor = None
            best_rating = 0
            
            for doc in docs:
                data = doc.to_dict()
                rating = data.get('rating', DEFAULT_RATING)
                if rating > best_rating:
                    best_rating = rating
                    best_executor = data.get('username')
            
            print(f"Найден топ исполнитель: {best_executor} с рейтингом {best_rating}")
            return best_executor
            
        except Exception as e:
            print(f"Ошибка поиска топ исполнителя: {e}")
            return None

    def get_user_chat_id_by_username(self, username: str) -> int:
        """Получает chat_id пользователя по username"""
        try:
            users_ref = self.db.collection('users').document(username)
            doc = users_ref.get()
            
            if doc.exists:
                return doc.to_dict().get('chat_id')
            return None
            
        except Exception as e:
            print(f"Ошибка получения chat_id для {username}: {e}")
            return None

    # МЕТОДЫ РАБОТЫ С ЗАКАЗАМИ
    def create_order(self, order_data: dict) -> str:
        """Создает новый заказ"""
        try:
            orders_ref = self.db.collection('orders')
            order_data['created_at'] = datetime.now()
            
            # Добавляем заказ и получаем ссылку на документ
            doc_ref = orders_ref.add(order_data)
            order_id = doc_ref[1].id  # doc_ref это кортеж (timestamp, DocumentReference)
            
            print(f"Заказ создан с ID: {order_id}")
            return order_id
            
        except Exception as e:
            print(f"Ошибка создания заказа: {e}")
            return None

    def get_order_by_id(self, order_id: str) -> dict:
        """Получает заказ по ID"""
        try:
            orders_ref = self.db.collection('orders').document(order_id)
            doc = orders_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                data['id'] = order_id
                return data
            return None
            
        except Exception as e:
            print(f"Ошибка получения заказа {order_id}: {e}")
            return None

    def update_order(self, order_id: str, updates: dict) -> bool:
        """Обновляет заказ"""
        try:
            orders_ref = self.db.collection('orders').document(order_id)
            updates['updated_at'] = datetime.now()
            orders_ref.update(updates)
            return True
            
        except Exception as e:
            print(f"Ошибка обновления заказа {order_id}: {e}")
            return False

    def get_orders_by_customer(self, customer_username: str) -> list:
        """Получает заказы клиента"""
        try:
            orders_ref = self.db.collection('orders')
            query = orders_ref.where(field_path='customer.username', op_string='==', value=customer_username)
            docs = query.get()
            
            orders = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                orders.append(data)
            
            return orders
            
        except Exception as e:
            print(f"Ошибка получения заказов клиента {customer_username}: {e}")
            return []

    def get_orders_by_executor(self, executor_username: str) -> list:
        """Получает заказы исполнителя"""
        try:
            orders_ref = self.db.collection('orders')
            query = orders_ref.where(field_path='executor.username', op_string='==', value=executor_username)
            docs = query.get()
            
            orders = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                orders.append(data)
            
            return orders
            
        except Exception as e:
            print(f"Ошибка получения заказов исполнителя {executor_username}: {e}")
            return []

    # МЕТОДЫ РАБОТЫ С СООБЩЕНИЯМИ
    def add_message(self, order_id: str, user_id: str, user_role: str, text: str) -> bool:
        """Добавляет сообщение в чат заказа"""
        try:
            messages_ref = self.db.collection('messages')
            
            message_data = {
                'order_id': order_id,
                'user_id': user_id,
                'user_role': user_role,
                'text': text,
                'timestamp': datetime.now()
            }
            
            messages_ref.add(message_data)
            print(f"Сообщение добавлено в чат заказа {order_id}")
            return True
            
        except Exception as e:
            print(f"Ошибка добавления сообщения: {e}")
            return False

    def get_messages_by_order(self, order_id: str) -> list:
        """Получает сообщения по заказу"""
        try:
            messages_ref = self.db.collection('messages')
            query = messages_ref.where(field_path='order_id', op_string='==', value=order_id).order_by('timestamp')
            docs = query.get()
            
            messages = []
            for doc in docs:
                data = doc.to_dict()
                messages.append(data)
            
            return messages
            
        except Exception as e:
            print(f"Ошибка получения сообщений для заказа {order_id}: {e}")
            return []

    # МЕТОДЫ РАБОТЫ С ПЛАТЕЖАМИ
    def create_payment(self, payment_data: dict) -> str:
        """Создает платеж"""
        try:
            payments_ref = self.db.collection('payments')
            payment_data['created_at'] = datetime.now()
            
            doc_ref = payments_ref.add(payment_data)
            payment_id = doc_ref[1].id
            
            print(f"Платеж создан с ID: {payment_id}")
            return payment_id
            
        except Exception as e:
            print(f"Ошибка создания платежа: {e}")
            return None

    def get_payment_by_order(self, order_id: str) -> dict:
        """Получает платеж по заказу"""
        try:
            payments_ref = self.db.collection('payments')
            query = payments_ref.where(field_path='order_id', op_string='==', value=order_id)
            docs = query.get()
            
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                return data
                
            return None
            
        except Exception as e:
            print(f"Ошибка получения платежа для заказа {order_id}: {e}")
            return None

    def update_payment_status(self, payment_id: str, status: str, timestamp: datetime) -> bool:
        """Обновляет статус платежа"""
        try:
            payments_ref = self.db.collection('payments').document(payment_id)
            payments_ref.update({
                'status': status,
                'status_updated_at': timestamp,
                'updated_at': datetime.now()
            })
            return True
            
        except Exception as e:
            print(f"Ошибка обновления статуса платежа {payment_id}: {e}")
            return False

    def get_pending_payments_by_user(self, user_id: int) -> list:
        """Получает ожидающие платежи пользователя"""
        try:
            payments_ref = self.db.collection('payments')
            query = payments_ref.where(field_path='user_id', op_string='==', value=user_id).where(field_path='status', op_string='==', value='pending')
            docs = query.get()
            
            payments = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                payments.append(data)
            
            return payments
            
        except Exception as e:
            print(f"Ошибка получения ожидающих платежей пользователя {user_id}: {e}")
            return []

    # МЕТОДЫ РАБОТЫ С ПОРТФОЛИО
    def get_portfolio(self) -> list:
        """Получает все элементы портфолио"""
        try:
            portfolio_ref = self.db.collection('portfolio')
            docs = portfolio_ref.get()
            
            portfolio = []
            for doc in docs:
                data = doc.to_dict()
                portfolio.append(data)
            
            return portfolio
            
        except Exception as e:
            print(f"Ошибка получения портфолио: {e}")
            return []

    def get_works_by_subcategory(self, subcategory: str) -> list:
        """Получает работы по подкатегории"""
        try:
            portfolio_ref = self.db.collection('portfolio')
            query = portfolio_ref.where(field_path='subcategory', op_string='==', value=subcategory)
            docs = query.get()
            
            works = []
            for doc in docs:
                data = doc.to_dict()
                works.append(data)
            
            return works
            
        except Exception as e:
            print(f"Ошибка получения работ подкатегории {subcategory}: {e}")
            return []

    # ДОПОЛНИТЕЛЬНЫЕ МЕТОДЫ
    def get_all_executors(self) -> list:
        """Получает всех исполнителей"""
        try:
            users_ref = self.db.collection('users')
            query = users_ref.where(field_path='role', op_string='==', value='entrepreneur')
            docs = query.get()
            
            executors = []
            for doc in docs:
                data = doc.to_dict()
                executors.append(data)
            
            return executors
            
        except Exception as e:
            print(f"Ошибка получения всех исполнителей: {e}")
            return []

    def delete_executor(self, username: str) -> bool:
        """Удаляет исполнителя"""
        try:
            users_ref = self.db.collection('users').document(username)
            doc = users_ref.get()
            
            if doc.exists and doc.to_dict().get('role') == 'entrepreneur':
                users_ref.delete()
                return True
            return False
            
        except Exception as e:
            print(f"Ошибка удаления исполнителя {username}: {e}")
            return False

    def get_portfolio_count(self) -> int:
        """Получает количество элементов портфолио"""
        try:
            portfolio_ref = self.db.collection('portfolio')
            docs = portfolio_ref.get()
            return len(docs)
            
        except Exception as e:
            print(f"Ошибка получения количества портфолио: {e}")
            return 0

    def get_admin_stats(self) -> dict:
        """Получает статистику для админ-панели"""
        try:
            stats = {}
            
            # Считаем пользователей
            users_ref = self.db.collection('users')
            all_users = users_ref.get()
            
            clients_count = 0
            executors_count = 0
            
            for doc in all_users:
                data = doc.to_dict()
                if data.get('role') == 'client':
                    clients_count += 1
                elif data.get('role') == 'entrepreneur':
                    executors_count += 1
            
            stats['clients_count'] = clients_count
            stats['executors_count'] = executors_count
            stats['total_users'] = len(all_users)
            
            # Считаем заказы
            orders_ref = self.db.collection('orders')
            all_orders = orders_ref.get()
            
            active_orders = 0
            completed_orders = 0
            
            for doc in all_orders:
                data = doc.to_dict()
                status = data.get('status', '')
                if status in ['in_work', 'on_review', 'pending']:
                    active_orders += 1
                elif status == 'completed':
                    completed_orders += 1
            
            stats['orders_count'] = len(all_orders)
            stats['active_orders'] = active_orders
            stats['completed_orders'] = completed_orders
            
            # Считаем портфолио
            stats['portfolio_count'] = self.get_portfolio_count()
            
            # Считаем общий баланс исполнителей
            total_balance = 0
            for doc in all_users:
                data = doc.to_dict()
                if data.get('role') == 'entrepreneur':
                    total_balance += data.get('balance', 0)
            
            stats['total_balance'] = total_balance
            
            return stats
            
        except Exception as e:
            print(f"Ошибка получения статистики: {e}")
            return {}
