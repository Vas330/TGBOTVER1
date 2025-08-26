# main.py - модернизированная версия с уведомлениями от администратора (исправленная для Railway)
import logging
import asyncio
from datetime import datetime, timedelta
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters

from config import BOT_TOKEN, LOGGING_FORMAT, LOGGING_LEVEL, FIREBASE_KEY_PATH
from firebase_manager import FirebaseManager
from handlers_common import start, handle_unknown_command
from button_handler import button
from text_handler import handle_text, handle_photo
from handlers_services import (
    our_services_menu,
    video_production_menu,
    website_development_menu,
    video_ads_details,
    video_social_details,
    video_animation_details,
    video_3d_details,
    web_landing_details,
    web_shop_details,
    web_multipage_details,
    web_platforms_details
)
from payment_handlers import (
    send_payment_request,
    handle_payment_confirmation,
    handle_start_work,
    handle_payment_help,
    handle_back_to_payment,
    handle_decline_paid_order
)


def setup_logging() -> None:
    """Настройка логирования"""
    level = getattr(logging, LOGGING_LEVEL.upper(), logging.INFO)
    logging.basicConfig(format=LOGGING_FORMAT, level=level)


def setup_firebase() -> FirebaseManager:
    """Настройка Firebase"""
    try:
        firebase_manager = FirebaseManager(FIREBASE_KEY_PATH)
        print("Firebase успешно подключен!")
        return firebase_manager
    except Exception as e:
        print(f"Ошибка подключения к Firebase: {e}")
        raise


class AdminNotificationService:
    """Сервис для отправки уведомлений от администратора"""

    def __init__(self, firebase_manager, bot_application):
        self.firebase = firebase_manager
        self.application = bot_application
        self.processed_messages = set()  # Храним ID обработанных сообщений
        self.is_running = False

        # Загружаем время последней проверки из Firebase или устанавливаем текущее
        self.load_last_check_time()

    def load_last_check_time(self):
        """Загружает время последней проверки из Firebase"""
        try:
            system_ref = self.firebase.db.collection('system').document('admin_notifications')
            system_doc = system_ref.get()

            if system_doc.exists:
                system_data = system_doc.to_dict()
                self.last_check = system_data.get('last_check', datetime.now())
                print(f"Загружено время последней проверки: {self.last_check}")
            else:
                self.last_check = datetime.now()
                # Сохраняем начальное время
                system_ref.set({
                    'last_check': self.last_check,
                    'updated_at': datetime.now()
                })
                print(f"Установлено новое время последней проверки: {self.last_check}")
        except Exception as e:
            print(f"Ошибка загрузки времени последней проверки: {e}")
            self.last_check = datetime.now()

    def save_last_check_time(self):
        """Сохраняет время последней проверки в Firebase"""
        try:
            system_ref = self.firebase.db.collection('system').document('admin_notifications')
            system_ref.set({
                'last_check': self.last_check,
                'updated_at': datetime.now()
            })
        except Exception as e:
            print(f"Ошибка сохранения времени последней проверки: {e}")

    async def start_monitoring(self):
        """Запускает мониторинг сообщений от администратора"""
        self.is_running = True
        print("Запуск мониторинга сообщений от администратора...")

        while self.is_running:
            try:
                await self.check_admin_messages()
                await asyncio.sleep(30)  # Проверяем каждые 30 секунд
            except Exception as e:
                print(f"Ошибка в мониторинге: {e}")
                await asyncio.sleep(60)  # При ошибке ждем дольше

    def stop_monitoring(self):
        """Останавливает мониторинг"""
        self.is_running = False

    async def check_admin_messages(self):
        """Проверяет новые сообщения от администратора и отправляет уведомления"""
        try:
            current_time = datetime.now()

            # Получаем все сообщения от админа после последней проверки
            admin_messages_ref = self.firebase.db.collection('messages').where('user_role', '==', 'admin')
            admin_messages = admin_messages_ref.stream()

            new_notifications_sent = 0
            newest_message_time = self.last_check

            for msg_doc in admin_messages:
                msg_data = msg_doc.to_dict()
                msg_id = msg_doc.id

                # Пропускаем уже обработанные сообщения
                if msg_id in self.processed_messages:
                    continue

                # Проверяем время сообщения
                msg_timestamp = msg_data.get('timestamp')
                if msg_timestamp:
                    if hasattr(msg_timestamp, 'seconds'):
                        # Firebase Timestamp
                        msg_time = datetime.fromtimestamp(msg_timestamp.seconds)
                    elif hasattr(msg_timestamp, 'timestamp'):
                        # Другой формат timestamp
                        msg_time = msg_timestamp
                    else:
                        # datetime объект
                        msg_time = msg_timestamp

                    # Проверяем, что сообщение новее последней проверки
                    if msg_time <= self.last_check:
                        continue

                    # Обновляем время самого нового сообщения
                    if msg_time > newest_message_time:
                        newest_message_time = msg_time

                print(
                    f"Найдено новое сообщение от администратора: {msg_data.get('text', '')} для заказа {msg_data.get('order_id')}")

                # Отправляем уведомления участникам заказа
                order_id = msg_data.get('order_id')
                message_text = msg_data.get('text', '')

                if order_id and message_text:
                    await self.notify_order_participants(order_id, message_text)
                    self.processed_messages.add(msg_id)
                    new_notifications_sent += 1

            # Обновляем время последней проверки только если были новые сообщения
            if new_notifications_sent > 0:
                self.last_check = newest_message_time
                self.save_last_check_time()
                print(f"Отправлено {new_notifications_sent} уведомлений от администратора")
                print(f"Обновлено время последней проверки: {self.last_check}")

        except Exception as e:
            print(f"Ошибка при проверке сообщений администратора: {e}")
            import traceback
            traceback.print_exc()

    async def notify_order_participants(self, order_id, admin_message):
        """Отправляет уведомления участникам заказа о сообщении от администратора"""
        try:
            # Получаем информацию о заказе
            order = self.firebase.get_order_by_id(order_id)
            if not order:
                return

            order_title = order.get('title', 'Без названия')
            notification_text = (
                f"📨 Новое сообщение от администратора\n\n"
                f"Заказ: {order_title}\n"
                f"Сообщение: {admin_message}\n\n"
                f"Откройте чат заказа для ответа."
            )

            # Уведомляем заказчика
            customer_info = order.get('customer', {})
            customer_chat_id = None

            if customer_info.get('username'):
                customer_chat_id = self.firebase.get_user_chat_id_by_username(customer_info['username'])

            if customer_chat_id:
                try:
                    await self.application.bot.send_message(
                        chat_id=customer_chat_id,
                        text=notification_text
                    )
                    print(f"Уведомление отправлено заказчику {customer_info.get('username')}")
                except Exception as e:
                    print(f"Ошибка отправки уведомления заказчику: {e}")

            # Уведомляем исполнителя
            executor_info = order.get('executor', {})
            executor_chat_id = None

            if executor_info.get('username'):
                executor_chat_id = self.firebase.get_user_chat_id_by_username(executor_info['username'])

            if executor_chat_id and executor_chat_id != customer_chat_id:
                try:
                    await self.application.bot.send_message(
                        chat_id=executor_chat_id,
                        text=notification_text
                    )
                    print(f"Уведомление отправлено исполнителю {executor_info.get('username')}")
                except Exception as e:
                    print(f"Ошибка отправки уведомления исполнителю: {e}")

        except Exception as e:
            print(f"Ошибка при отправке уведомлений для заказа {order_id}: {e}")


async def start_background_tasks(firebase_manager, application):
    """Запускает фоновые задачи"""
    print("Инициализация фоновых задач...")

    # Создаем сервис уведомлений от администратора
    admin_notification_service = AdminNotificationService(firebase_manager, application)

    # Запускаем мониторинг в фоновом режиме
    task = asyncio.create_task(admin_notification_service.start_monitoring())
    print("Задача мониторинга создана")

    return admin_notification_service


def main() -> None:
    """Основная функция запуска бота"""
    print("Запуск бота с полной функциональностью...")
    
    setup_logging()

    # Инициализация Firebase
    firebase_manager = setup_firebase()

    # Создание приложения
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Передача firebase_manager в context
    application.bot_data['firebase'] = firebase_manager

    # Добавление обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.COMMAND, handle_unknown_command))

    print("Бот запускается с поддержкой уведомлений от администратора...")

    # ИСПРАВЛЕНО: Упрощенная версия запуска для Railway
    try:
        # Создаем event loop для Railway
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def init_and_run():
            # Запускаем фоновые задачи
            admin_service = await start_background_tasks(firebase_manager, application)
            
            print("Бот запущен и готов к работе!")
            print("Система чатов и уведомлений активна!")
            
            # Запускаем основной polling (синхронный способ)
            application.run_polling()

        # Используем run_until_complete для стабильности
        loop.run_until_complete(init_and_run())
        
    except Exception as e:
        print(f"Ошибка запуска бота: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback - запуск без фоновых задач
        print("Попытка запуска в упрощенном режиме...")
        application.run_polling()


if __name__ == '__main__':
    main()
