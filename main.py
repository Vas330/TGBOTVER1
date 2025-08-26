# main.py - версия без Firebase для диагностики
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters

from config import BOT_TOKEN, LOGGING_FORMAT, LOGGING_LEVEL


def setup_logging() -> None:
    """Настройка логирования"""
    level = getattr(logging, LOGGING_LEVEL.upper(), logging.INFO)
    logging.basicConfig(format=LOGGING_FORMAT, level=level)


async def simple_start(update, context):
    """Простой обработчик /start без Firebase"""
    welcome_text = """Добро пожаловать в Алтреза!

Мы — команда профессионалов, которая поможет вам:
• Создать эффективный сайт
• Разработать видео-контент
• Повысить продажи и узнаваемость

Выберите свою роль:"""

    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    keyboard = [
        [InlineKeyboardButton("Я заказчик", callback_data='client')],
        [InlineKeyboardButton("Я исполнитель", callback_data='entrepreneur')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(welcome_text, reply_markup=reply_markup)


async def simple_button(update, context):
    """Простой обработчик кнопок без Firebase"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'client':
        await query.edit_message_text("Вы выбрали роль заказчика!\nФункциональность временно недоступна.")
    elif query.data == 'entrepreneur':
        await query.edit_message_text("Вы выбрали роль исполнителя!\nФункциональность временно недоступна.")
    else:
        await query.edit_message_text(f"Получена команда: {query.data}")


async def simple_text(update, context):
    """Простой обработчик текста без Firebase"""
    text = update.message.text
    await update.message.reply_text(f"Получено сообщение: {text}\nBот работает!")


def main() -> None:
    """Основная функция запуска бота БЕЗ Firebase"""
    print("==========================================")
    print("ДИАГНОСТИЧЕСКИЙ ЗАПУСК БОТА")
    print("Firebase ОТКЛЮЧЕН")
    print("==========================================")
    
    setup_logging()

    # Проверяем токен
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN не найден!")
        
    print(f"BOT_TOKEN: {BOT_TOKEN[:20]}...")

    # Создание приложения
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Простые обработчики БЕЗ Firebase
    application.add_handler(CommandHandler("start", simple_start))
    application.add_handler(CallbackQueryHandler(simple_button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, simple_text))

    print("Простые обработчики добавлены")
    print("Запуск polling...")

    # Запуск бота
    application.run_polling()


if __name__ == '__main__':
    main()
