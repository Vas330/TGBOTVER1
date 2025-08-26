# main.py - версия с защищенным Firebase
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters

from config import BOT_TOKEN, LOGGING_FORMAT, LOGGING_LEVEL, FIREBASE_KEY_PATH, USE_FIREBASE


def setup_logging():
    """Настройка логирования"""
    level = getattr(logging, LOGGING_LEVEL.upper(), logging.INFO)
    logging.basicConfig(format=LOGGING_FORMAT, level=level)


def setup_firebase():
    """Безопасная инициализация Firebase"""
    if not USE_FIREBASE or not FIREBASE_KEY_PATH:
        print("Firebase отключен - бот будет работать без базы данных")
        return None
        
    try:
        from firebase_manager import FirebaseManager
        firebase_manager = FirebaseManager(FIREBASE_KEY_PATH)
        print("Firebase успешно подключен!")
        return firebase_manager
    except Exception as e:
        print(f"Ошибка Firebase (бот будет работать без БД): {e}")
        return None


def setup_handlers(application, firebase_manager):
    """Настройка обработчиков"""
    # Передаем Firebase в bot_data (может быть None)
    application.bot_data['firebase'] = firebase_manager
    
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


def main():
    """Основная функция"""
    print("==========================================")
    print("Запуск бота с защищенным Firebase...")
    print("==========================================")
    
    try:
        # Настройка логирования
        setup_logging()
        
        # Проверка токена
        if not BOT_TOKEN:
            raise ValueError("BOT_TOKEN не найден!")
            
        print(f"BOT_TOKEN найден: {BOT_TOKEN[:20]}...")
        
        # Безопасная инициализация Firebase
        firebase_manager = setup_firebase()
        
        # Создание приложения
        application = ApplicationBuilder().token(BOT_TOKEN).build()
        
        # Настройка обработчиков
        setup_handlers(application, firebase_manager)
        
        if firebase_manager:
            print("Бот запущен с базой данных Firebase")
        else:
            print("Бот запущен БЕЗ базы данных (ограниченная функциональность)")
            
        print("Запуск polling...")
        
        # Запуск бота
        application.run_polling()
        
    except KeyboardInterrupt:
        print("Бот остановлен пользователем")
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
