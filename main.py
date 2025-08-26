# main.py - полная исправленная версия с обработкой конфликтов
import logging
import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram.error import Conflict, NetworkError

from config import BOT_TOKEN, LOGGING_FORMAT, LOGGING_LEVEL, FIREBASE_KEY_PATH, USE_FIREBASE


def setup_logging():
    """Настройка логирования"""
    level = getattr(logging, LOGGING_LEVEL.upper(), logging.INFO)
    logging.basicConfig(format=LOGGING_FORMAT, level=level)
    # Отключаем лишние логи httpx
    logging.getLogger("httpx").setLevel(logging.WARNING)


def setup_firebase():
    """Безопасная инициализация Firebase"""
    if not USE_FIREBASE or not FIREBASE_KEY_PATH:
        print("Firebase отключен")
        return None
        
    try:
        from firebase_manager import FirebaseManager
        firebase_manager = FirebaseManager(FIREBASE_KEY_PATH)
        print("Firebase успешно подключен!")
        return firebase_manager
    except Exception as e:
        print(f"Ошибка Firebase (работаем без БД): {e}")
        return None


async def clear_webhooks(bot):
    """Очистка webhook для решения конфликтов"""
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        print("Webhook очищен")
        await asyncio.sleep(1)  # Даем время на обработку
    except Exception as e:
        print(f"Не удалось очистить webhook: {e}")


def setup_handlers(application, firebase_manager):
    """Настройка всех обработчиков"""
    application.bot_data['firebase'] = firebase_manager
    
    try:
        # Импортируем обработчики
        from handlers_common import start, handle_unknown_command
        from button_handler import button
        from text_handler import handle_text, handle_photo
        
        # Добавляем обработчики
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CallbackQueryHandler(button))
        application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
        application.add_handler(MessageHandler(filters.COMMAND, handle_unknown_command))
        
        print("Все обработчики настроены")
        
    except ImportError as e:
        print(f"ОШИБКА импорта обработчиков: {e}")
        print("Настраиваем базовые обработчики...")
        
        # Базовые обработчики если импорт не работает
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        async def fallback_start(update, context):
            keyboard = [
                [InlineKeyboardButton("Заказчик", callback_data='client')],
                [InlineKeyboardButton("Исполнитель", callback_data='entrepreneur')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("Добро пожаловать! Выберите роль:", reply_markup=reply_markup)
        
        async def fallback_button(update, context):
            query = update.callback_query
            await query.answer()
            await query.edit_message_text(f"Выбрана роль: {query.data}")
            
        application.add_handler(CommandHandler("start", fallback_start))
        application.add_handler(CallbackQueryHandler(fallback_button))
        print("Базовые обработчики настроены")


def main():
    """Основная функция с обработкой конфликтов"""
    print("==========================================")
    print("Запуск бота (исправленная версия)")
    print("==========================================")
    
    try:
        # Настройка логирования
        setup_logging()
        
        # Проверка токена
        if not BOT_TOKEN:
            raise ValueError("BOT_TOKEN не найден!")
            
        print(f"BOT_TOKEN: {BOT_TOKEN[:20]}...")
        
        # Firebase
        firebase_manager = setup_firebase()
        
        # Создание приложения с обработкой ошибок
        application = ApplicationBuilder().token(BOT_TOKEN).build()
        
        # Настройка обработчиков
        setup_handlers(application, firebase_manager)
        
        print("Попытка запуска бота...")
        
        # Асинхронный запуск с обработкой конфликтов
        async def run_bot_with_retries():
            max_retries = 3
            retry_delay = 5
            
            for attempt in range(max_retries):
                try:
                    print(f"Попытка запуска #{attempt + 1}")
                    
                    # Очищаем webhook для устранения конфликтов
                    await clear_webhooks(application.bot)
                    
                    # Запускаем polling
                    async with application:
                        await application.start()
                        print("Бот успешно запущен!")
                        
                        if firebase_manager:
                            print("База данных: Firebase подключен")
                        else:
                            print("База данных: отключена")
                            
                        await application.updater.start_polling(
                            drop_pending_updates=True,
                            allowed_updates=['message', 'callback_query']
                        )
                        
                        print("Polling активен - бот готов к работе!")
                        
                        # Держим бот работающим
                        await asyncio.Event().wait()
                        
                except Conflict as e:
                    print(f"Конфликт экземпляров (попытка {attempt + 1}): {e}")
                    if attempt < max_retries - 1:
                        print(f"Ожидание {retry_delay} сек. перед повторной попыткой...")
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # Увеличиваем задержку
                    else:
                        print("Все попытки исчерпаны. Проверьте что нет других экземпляров бота!")
                        raise
                        
                except Exception as e:
                    print(f"Ошибка при запуске (попытка {attempt + 1}): {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay)
                    else:
                        raise
        
        # Запуск с обработкой ошибок
        try:
            asyncio.run(run_bot_with_retries())
        except KeyboardInterrupt:
            print("Бот остановлен пользователем")
        except Exception as e:
            print(f"Критическая ошибка: {e}")
            print("Попытка запуска в упрощенном режиме...")
            
            # Fallback - синхронный запуск
            application.run_polling(drop_pending_updates=True)
            
    except Exception as e:
        print(f"Не удалось запустить бота: {e}")
        import traceback
        traceback.print_exc()
        
        print("\n" + "="*50)
        print("ДИАГНОСТИКА ПРОБЛЕМ:")
        print("1. Остановите все другие экземпляры бота")
        print("2. Проверьте что BOT_TOKEN правильный")
        print("3. Убедитесь что нет webhook настроек")
        print("="*50)


if __name__ == '__main__':
    main()
