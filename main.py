# main.py
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from config import BOT_TOKEN, LOGGING_FORMAT, LOGGING_LEVEL
from handlers_common import start
from button_handler import button
from text_handler import handle_text, handle_photo

def setup_logging() -> None:
    """Настройка логирования"""
    level = getattr(logging, LOGGING_LEVEL.upper(), logging.INFO)
    logging.basicConfig(format=LOGGING_FORMAT, level=level)

def main() -> None:
    """Основная функция запуска бота"""
    setup_logging()
    
    # Создание приложения
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Добавление обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))  # Обработчик фото
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # Запуск бота
    print("Бот запускается...")
    application.run_polling()

if __name__ == '__main__':
    main()
