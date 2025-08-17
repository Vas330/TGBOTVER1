# handlers_common.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import ADMIN_ID


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    keyboard = [
        [InlineKeyboardButton("Я Заказчик", callback_data='client')],
        [InlineKeyboardButton("Я Исполнитель", callback_data='entrepreneur')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        'Добро пожаловать в нашего бота! Выберите роль:',
        reply_markup=reply_markup
    )


async def handle_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды 'админ'"""
    user_id = update.message.from_user.id

    if user_id == ADMIN_ID:
        keyboard = [
            [InlineKeyboardButton("Зарегистрировать исполнителя", callback_data='register_entrepreneur')],
            [InlineKeyboardButton("Все исполнители", callback_data='all_entrepreneurs')],
            [InlineKeyboardButton("Управление портфолио", callback_data='portfolio_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Добро пожаловать, Администратор!", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Вы не являетесь администратором.")