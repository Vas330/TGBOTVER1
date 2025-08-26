# firebase_manager.py - исправленная версия с поддержкой админ-панели
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import uuid


class FirebaseManager:
    def __init__(self, service_account_path):
        """Инициализация Firebase"""
        if not firebase_admin._apps:
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)

        self.db = firestore.client()
        print("FirebaseManager инициализирован")

    # ПОЛЬЗОВАТЕЛИ
    def register_client(self, username: str, password: str, chat_id: int = None, telegram_id: str = None) -> bool:
        """Регистрация клиента"""
        try:
            users_ref = self.db.collection('users')
            existing_user = users_ref.where('username', '==', username).limit(1).get()

            if existing_user:
                return False

            user_data = {
                'username': username,
                'password': password,
                'role': 'client',
                'chat_id': chat_id,
                'telegram_id': telegram_id or str(chat_id) if chat_id else None,
                'created_at': datetime.now(),
                'status': 'active'
            }

            users_ref.add(user_data)
            print(f"Клиент {username} зарегистрирован")
            return True

        except Exception as e:
            print(f"Ошибка регистрации клиента: {e}")
            return False

    def register_entrepreneur(self, username: str, password: str, chat_id: int = None, telegram_id: str = None) -> bool:
        """Регистрация исполнителя"""
        try:
            users_ref = self.db.collection('users')
            existing_user = users_ref.where('username', '==', username).limit(1).get()

            if existing_user:
                return False

            user_data = {
                'username': username,
                'password': password,
                'role': 'entrepreneur',
                'chat_id': chat_id,
                'telegram_id': telegram_id or str(chat_id) if chat_id else None,
                'created_at': datetime.now(),
                'balance': 0.0,
                'rating': 10.0,
                'completed_orders': 0,
                'status': 'active'
            }

            users_ref.add(user_data)
            print(f"Исполнитель {username} зарегистрирован")
            return True

        except Exception as e:
            print(f"Ошибка регистрации исполнителя: {e}")
            return False

    def check_client(self, username: str, password: str) -> bool:
        """Проверка авторизации клиента"""
        try:
            print(f"DEBUG: Проверяем клиента {username}")
            users_ref = self.db.collection('users')
            query = users_ref.where('username', '==', username).where('password', '==', password).where('role', '==',
                                                                                                        'client')
            users = query.get()

            result = len(users) > 0
            print(f"DEBUG: Клиент найден: {result}")
            return result

        except Exception as e:
            print(f"Ошибка проверки клиента: {e}")
            return False

    def check_entrepreneur(self, username: str, password: str) -> bool:
        """Проверка авторизации исполнителя (поддерживает роли entrepreneur и executor)"""
        try:
            print(f"DEBUG: Проверяем исполнителя {username} с паролем {password}")
            users_ref = self.db.collection('users')

            # Сначала ищем по username и password
            query = users_ref.where('username', '==', username).where('password', '==', password)
            users = query.get()

            print(f"DEBUG: Найдено пользователей с логином и паролем: {len(users)}")

            if users:
                user_data = users[0].to_dict()
                role = user_data.get('role')
                print(f"DEBUG: Роль пользователя: {role}")

                # Принимаем обе роли: entrepreneur и executor
                result = role in ['entrepreneur', 'executor']
                print(f"DEBUG: Результат проверки исполнителя: {result}")
                return result

            return False

        except Exception as e:
            print(f"Ошибка проверки исполнителя: {e}")
            return False

    def get_client_by_chat_id(self, chat_id: int) -> str:
        """Получение логина клиента по chat_id"""
        try:
            users_ref = self.db.collection('users')
            query = users_ref.where('chat_id', '==', chat_id).where('role', '==', 'client')
            users = query.get()

            if users:
                return users[0].to_dict()['username']
            return None

        except Exception as e:
            print(f"Ошибка получения клиента: {e}")
            return None

    def get_entrepreneur_by_chat_id(self, chat_id: int) -> str:
        """Получение логина исполнителя по chat_id (поддерживает обе роли)"""
        try:
            users_ref = self.db.collection('users')
            query = users_ref.where('chat_id', '==', chat_id)
            users = query.get()

            for user_doc in users:
                user_data = user_doc.to_dict()
                if user_data.get('role') in ['entrepreneur', 'executor']:
                    return user_data['username']

            return None

        except Exception as e:
            print(f"Ошибка получения исполнителя: {e}")
            return None

    def set_client_chat_id(self, username: str, chat_id: int):
        """Установка chat_id для клиента"""
        try:
            users_ref = self.db.collection('users')
            query = users_ref.where('username', '==', username).where('role', '==', 'client')
            users = query.get()

            if users:
                user_doc = users[0]
                user_doc.reference.update({'chat_id': chat_id})
                print(f"Chat ID {chat_id} установлен для клиента {username}")

        except Exception as e:
            print(f"Ошибка установки chat_id: {e}")

    def set_entrepreneur_chat_id(self, username: str, chat_id: int):
        """Установка chat_id для исполнителя"""
        try:
            users_ref = self.db.collection('users')
            query = users_ref.where('username', '==', username)
            users = query.get()

            for user_doc in users:
                user_data = user_doc.to_dict()
                if user_data.get('role') in ['entrepreneur', 'executor']:
                    user_doc.reference.update({'chat_id': chat_id})
                    print(f"Chat ID {chat_id} установлен для исполнителя {username}")
                    break

        except Exception as e:
            print(f"Ошибка установки chat_id: {e}")

    def get_user_by_telegram_id(self, telegram_id: str) -> dict:
        """Получение пользователя по telegram_id"""
        try:
            users_ref = self.db.collection('users')
            query = users_ref.where('telegram_id', '==', telegram_id)
            users = query.get()

            if users:
                user_data = users[0].to_dict()
                user_data['id'] = users[0].id
                return user_data
            return None

        except Exception as e:
            print(f"Ошибка получения пользователя по telegram_id: {e}")
            return None

    def get_user_by_username(self, username: str) -> dict:
        """Получение пользователя по username"""
        try:
            users_ref = self.db.collection('users')
            query = users_ref.where('username', '==', username)
            users = query.get()

            if users:
                user_data = users[0].to_dict()
                user_data['id'] = users[0].id
                return user_data
            return None

        except Exception as e:
            print(f"Ошибка получения пользователя по username: {e}")
            return None

    def get_user_chat_id_by_username(self, username: str) -> int:
        """Получение chat_id пользователя по username"""
        try:
            users_ref = self.db.collection('users')
            query = users_ref.where('username', '==', username)
            users = query.get()

            if users:
                user_data = users[0].to_dict()
                chat_id = user_data.get('chat_id')
                print(f"DEBUG: Chat ID для {username}: {chat_id}")
                return chat_id

            print(f"DEBUG: Пользователь {username} не найден")
            return None

        except Exception as e:
            print(f"Ошибка получения chat_id: {e}")
            return None

    # НОВЫЕ МЕТОДЫ ДЛЯ АДМИН-ПАНЕЛИ

    def get_all_executors(self) -> list:
        """Получение всех исполнителей для админ-панели"""
        try:
            users_ref = self.db.collection('users')
            # Получаем всех пользователей с ролью entrepreneur или executor
            all_users = users_ref.get()

            executors = []
            for user_doc in all_users:
                user_data = user_doc.to_dict()
                role = user_data.get('role')

                if role in ['entrepreneur', 'executor']:
                    user_data['id'] = user_doc.id
                    executors.append(user_data)

            print(f"DEBUG: Найдено исполнителей: {len(executors)}")
            return executors

        except Exception as e:
            print(f"Ошибка получения всех исполнителей: {e}")
            return []

    def delete_executor(self, username: str) -> bool:
        """Удаление исполнителя"""
        try:
            users_ref = self.db.collection('users')
            query = users_ref.where('username', '==', username)
            users = query.get()

            deleted = False
            for user_doc in users:
                user_data = user_doc.to_dict()
                if user_data.get('role') in ['entrepreneur', 'executor']:
                    user_doc.reference.delete()
                    deleted = True
                    print(f"Исполнитель {username} удален")
                    break

            return deleted

        except Exception as e:
            print(f"Ошибка удаления исполнителя: {e}")
            return False

    def get_admin_stats(self) -> dict:
        """Получение статистики для админ-панели"""
        try:
            users_ref = self.db.collection('users')
            orders_ref = self.db.collection('orders')
            portfolio_ref = self.db.collection('portfolio')

            # Получаем всех пользователей
            all_users = users_ref.get()

            clients_count = 0
            executors_count = 0
            total_balance = 0.0

            for user_doc in all_users:
                user_data = user_doc.to_dict()
                role = user_data.get('role')

                if role == 'client':
                    clients_count += 1
                elif role in ['entrepreneur', 'executor']:
                    executors_count += 1
                    total_balance += user_data.get('balance', 0)

            # Получаем заказы
            all_orders = orders_ref.get()
            orders_count = len(all_orders)

            active_orders = 0
            completed_orders = 0

            for order_doc in all_orders:
                order_data = order_doc.to_dict()
                status = order_data.get('status')

                if status in ['in_work', 'pending', 'waiting_payment']:
                    active_orders += 1
                elif status == 'completed':
                    completed_orders += 1

            # Получаем портфолио
            portfolio_items = portfolio_ref.get()
            portfolio_count = len(portfolio_items)

            return {
                'clients_count': clients_count,
                'executors_count': executors_count,
                'total_users': clients_count + executors_count,
                'orders_count': orders_count,
                'active_orders': active_orders,
                'completed_orders': completed_orders,
                'portfolio_count': portfolio_count,
                'total_balance': total_balance
            }

        except Exception as e:
            print(f"Ошибка получения статистики: {e}")
            return {}

    # БАЛАНС И РЕЙТИНГ
    def get_balance(self, username: str) -> float:
        """Получение баланса исполнителя"""
        try:
            users_ref = self.db.collection('users')
            query = users_ref.where('username', '==', username)
            users = query.get()

            for user_doc in users:
                user_data = user_doc.to_dict()
                if user_data.get('role') in ['entrepreneur', 'executor']:
                    return user_data.get('balance', 0.0)

            return 0.0

        except Exception as e:
            print(f"Ошибка получения баланса: {e}")
            return 0.0

    def update_balance(self, username: str, amount: float):
        """Обновление баланса исполнителя"""
        try:
            users_ref = self.db.collection('users')
            query = users_ref.where('username', '==', username)
            users = query.get()

            for user_doc in users:
                user_data = user_doc.to_dict()
                if user_data.get('role') in ['entrepreneur', 'executor']:
                    current_balance = user_data.get('balance', 0.0)
                    new_balance = current_balance + amount

                    user_doc.reference.update({'balance': new_balance})
                    print(f"Баланс {username} обновлен: {current_balance} -> {new_balance}")
                    break

        except Exception as e:
            print(f"Ошибка обновления баланса: {e}")

    def get_rating(self, username: str) -> float:
        """Получение рейтинга исполнителя"""
        try:
            users_ref = self.db.collection('users')
            query = users_ref.where('username', '==', username)
            users = query.get()

            for user_doc in users:
                user_data = user_doc.to_dict()
                if user_data.get('role') in ['entrepreneur', 'executor']:
                    return user_data.get('rating', 10.0)

            return 10.0

        except Exception as e:
            print(f"Ошибка получения рейтинга: {e}")
            return 10.0

    def get_top_executor(self) -> str:
        """Получение исполнителя с наивысшим рейтингом"""
        try:
            print("DEBUG: Ищем топ исполнителя...")
            users_ref = self.db.collection('users')

            # Получаем всех исполнителей и сортируем вручную
            all_users = users_ref.get()
            executors = []

            for user_doc in all_users:
                user_data = user_doc.to_dict()
                role = user_data.get('role')
                if role in ['entrepreneur', 'executor']:
                    executors.append(user_data)
                    print(
                        f"DEBUG: Найден исполнитель {user_data.get('username')} с рейтингом {user_data.get('rating', 10)}")

            if executors:
                # Сортируем по рейтингу
                top_executor = max(executors, key=lambda x: x.get('rating', 0))
                username = top_executor['username']
                print(f"DEBUG: Выбран топ исполнитель: {username} с рейтингом {top_executor.get('rating')}")
                return username
            else:
                print("DEBUG: Исполнители не найдены")
                return None

        except Exception as e:
            print(f"DEBUG: Ошибка получения топ исполнителя: {e}")
            import traceback
            traceback.print_exc()
            return None

    # ЗАКАЗЫ
    def create_order(self, order_data: dict) -> str:
        """Создание заказа"""
        try:
            order_data['created_date'] = datetime.now()
            order_data['id'] = str(uuid.uuid4())

            orders_ref = self.db.collection('orders')
            doc_ref = orders_ref.add(order_data)

            # Обновляем ID в документе
            doc_ref[1].update({'id': doc_ref[1].id})

            print(f"Заказ создан: {doc_ref[1].id}")
            return doc_ref[1].id

        except Exception as e:
            print(f"Ошибка создания заказа: {e}")
            return None

    def get_order_by_id(self, order_id: str) -> dict:
        """Получение заказа по ID"""
        try:
            orders_ref = self.db.collection('orders')
            order_doc = orders_ref.document(order_id).get()

            if order_doc.exists:
                return order_doc.to_dict()
            return None

        except Exception as e:
            print(f"Ошибка получения заказа: {e}")
            return None

    def update_order(self, order_id: str, update_data: dict):
        """Обновление заказа"""
        try:
            orders_ref = self.db.collection('orders')
            orders_ref.document(order_id).update(update_data)
            print(f"Заказ {order_id} обновлен")

        except Exception as e:
            print(f"Ошибка обновления заказа: {e}")

    def get_orders_by_customer(self, customer_username: str) -> list:
        """Получение заказов клиента"""
        try:
            orders_ref = self.db.collection('orders')
            query = orders_ref.where('customer.username', '==', customer_username)
            orders = query.get()

            result = []
            for order_doc in orders:
                order_data = order_doc.to_dict()
                order_data['id'] = order_doc.id
                result.append(order_data)

            return result

        except Exception as e:
            print(f"Ошибка получения заказов клиента: {e}")
            return []

    def get_orders_by_executor(self, executor_username: str) -> list:
        """Получение заказов исполнителя"""
        try:
            orders_ref = self.db.collection('orders')
            query = orders_ref.where('executor.username', '==', executor_username)
            orders = query.get()

            result = []
            for order_doc in orders:
                order_data = order_doc.to_dict()
                order_data['id'] = order_doc.id
                result.append(order_data)

            return result

        except Exception as e:
            print(f"Ошибка получения заказов исполнителя: {e}")
            return []

    # СООБЩЕНИЯ
    def add_message(self, order_id: str, user_id: str, user_role: str, text: str):
        """Добавление сообщения в чат"""
        try:
            message_data = {
                'order_id': order_id,
                'user_id': user_id,
                'user_role': user_role,
                'text': text,
                'timestamp': datetime.now()
            }

            messages_ref = self.db.collection('messages')
            messages_ref.add(message_data)
            print(f"Сообщение добавлено в заказ {order_id}")

        except Exception as e:
            print(f"Ошибка добавления сообщения: {e}")

    def get_messages_by_order(self, order_id: str) -> list:
        """Получение сообщений по заказу"""
        try:
            messages_ref = self.db.collection('messages')
            query = messages_ref.where('order_id', '==', order_id).order_by('timestamp')
            messages = query.get()

            result = []
            for msg_doc in messages:
                msg_data = msg_doc.to_dict()
                result.append(msg_data)

            return result

        except Exception as e:
            print(f"Ошибка получения сообщений: {e}")
            return []

    # СОСТОЯНИЯ ПОЛЬЗОВАТЕЛЕЙ
    def set_user_state(self, user_id: int, state: str):
        """Установка состояния пользователя"""
        try:
            states_ref = self.db.collection('user_states')
            states_ref.document(str(user_id)).set({
                'state': state,
                'updated_at': datetime.now()
            })

        except Exception as e:
            print(f"Ошибка установки состояния: {e}")

    def get_user_state(self, user_id: int) -> str:
        """Получение состояния пользователя"""
        try:
            states_ref = self.db.collection('user_states')
            state_doc = states_ref.document(str(user_id)).get()

            if state_doc.exists:
                return state_doc.to_dict().get('state')
            return None

        except Exception as e:
            print(f"Ошибка получения состояния: {e}")
            return None

    def clear_user_state(self, user_id: int):
        """Очистка состояния пользователя"""
        try:
            states_ref = self.db.collection('user_states')
            states_ref.document(str(user_id)).delete()

        except Exception as e:
            print(f"Ошибка очистки состояния: {e}")

    # ПОРТФОЛИО И РАБОТЫ - ИСПРАВЛЕННЫЕ МЕТОДЫ

    def get_portfolio(self) -> list:
        """Получение элементов портфолио - ИСПРАВЛЕНО"""
        try:
            portfolio_ref = self.db.collection('portfolio')
            portfolio_query = portfolio_ref.get()  # Получаем QueryResultsList

            result = []
            # ИСПРАВЛЕНО: перебираем QueryResultsList напрямую, без .docs
            for item_doc in portfolio_query:
                item_data = item_doc.to_dict()
                item_data['id'] = item_doc.id
                result.append(item_data)

            print(f"DEBUG: Загружено элементов портфолио: {len(result)}")
            return result

        except Exception as e:
            print(f"Ошибка получения портфолио: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_portfolio_count(self) -> int:
        """Получение количества элементов портфолио"""
        try:
            portfolio_ref = self.db.collection('portfolio')
            portfolio_query = portfolio_ref.get()
            return len(portfolio_query)

        except Exception as e:
            print(f"Ошибка получения количества портфолио: {e}")
            return 0

    def get_works_by_subcategory(self, subcategory: str) -> list:
        """Получение работ по подкатегории - ИСПРАВЛЕНО"""
        try:
            works_ref = self.db.collection('works')
            query = works_ref.where('subcategory', '==', subcategory)
            works_query = query.get()  # Получаем QueryResultsList

            result = []
            # ИСПРАВЛЕНО: перебираем QueryResultsList напрямую, без .docs
            for work_doc in works_query:
                work_data = work_doc.to_dict()
                work_data['id'] = work_doc.id
                result.append(work_data)

            print(f"DEBUG: Загружено работ для {subcategory}: {len(result)}")
            return result

        except Exception as e:
            print(f"Ошибка получения работ: {e}")
            import traceback
            traceback.print_exc()
            return []

    def add_portfolio_item(self, category: str, title: str, description: str, photo: str, photo_type: str = 'file_id'):
        """Добавление элемента в портфолио"""
        try:
            portfolio_data = {
                'category': category,
                'title': title,
                'description': description,
                'photo': photo,
                'photo_type': photo_type,
                'created_at': datetime.now()
            }

            portfolio_ref = self.db.collection('portfolio')
            doc_ref = portfolio_ref.add(portfolio_data)
            print(f"Элемент портфолио добавлен: {title} (ID: {doc_ref[1].id})")

        except Exception as e:
            print(f"Ошибка добавления в портфолио: {e}")
            import traceback
            traceback.print_exc()
            raise e

    def add_work_item(self, subcategory: str, title: str, description: str, photo: str, photo_type: str = 'file_id',
                      url: str = None, price: int = None):
        """Добавление работы в подкатегорию"""
        try:
            work_data = {
                'subcategory': subcategory,
                'title': title,
                'description': description,
                'photo': photo,
                'photo_type': photo_type,
                'url': url,
                'price': price,
                'created_at': datetime.now()
            }

            works_ref = self.db.collection('works')
            doc_ref = works_ref.add(work_data)
            print(f"Работа добавлена: {title} (ID: {doc_ref[1].id})")

        except Exception as e:
            print(f"Ошибка добавления работы: {e}")
            import traceback
            traceback.print_exc()
            raise e

    # ПЛАТЕЖИ
    def create_payment(self, payment_data: dict) -> str:
        """Создание записи о платеже"""
        try:
            payments_ref = self.db.collection('payments')
            doc_ref = payments_ref.add(payment_data)

            print(f"Платеж создан: {doc_ref.id}")
            return doc_ref.id

        except Exception as e:
            print(f"Ошибка создания платежа: {e}")
            return None

    def get_payment_by_order(self, order_id: str) -> dict:
        """Получение платежа по ID заказа"""
        try:
            payments_ref = self.db.collection('payments')
            query = payments_ref.where('order_id', '==', order_id)
            payments = query.get()

            if payments:
                payment_data = payments[0].to_dict()
                payment_data['id'] = payments[0].id
                return payment_data
            return None

        except Exception as e:
            print(f"Ошибка получения платежа: {e}")
            return None

    def get_payment_by_id(self, payment_id: str) -> dict:
        """Получение платежа по payment_id"""
        try:
            payments_ref = self.db.collection('payments')
            query = payments_ref.where('payment_id', '==', payment_id)
            payments = query.get()

            if payments:
                payment_data = payments[0].to_dict()
                payment_data['id'] = payments[0].id
                return payment_data
            return None

        except Exception as e:
            print(f"Ошибка получения платежа по payment_id: {e}")
            return None

    def update_payment_status(self, payment_doc_id: str, status: str, paid_at: datetime = None):
        """Обновление статуса платежа"""
        try:
            payments_ref = self.db.collection('payments')
            update_data = {'status': status}

            if paid_at:
                update_data['paid_at'] = paid_at

            payments_ref.document(payment_doc_id).update(update_data)
            print(f"Статус платежа {payment_doc_id} обновлен: {status}")

        except Exception as e:
            print(f"Ошибка обновления статуса платежа: {e}")

    def get_pending_payments_by_user(self, user_id: int) -> list:
        """Получение ожидающих платежей пользователя"""
        try:
            payments_ref = self.db.collection('payments')
            query = payments_ref.where('user_id', '==', user_id).where('status', '==', 'pending')
            payments = query.get()

            result = []
            for payment_doc in payments:
                payment_data = payment_doc.to_dict()
                payment_data['id'] = payment_doc.id
                result.append(payment_data)

            return result

        except Exception as e:
            print(f"Ошибка получения ожидающих платежей: {e}")
            return []