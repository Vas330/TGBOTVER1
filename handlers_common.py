# handlers_common.py - общие обработчики
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import ADMIN_ID


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    firebase = context.bot_data['firebase']
    user_id = update.message.from_user.id

    # Проверяем, авторизован ли пользователь как клиент или исполнитель
    client_login = firebase.get_client_by_chat_id(user_id)
    contractor_login = firebase.get_entrepreneur_by_chat_id(user_id)

    if client_login:
        # Пользователь уже авторизован как клиент
        keyboard = [
            [InlineKeyboardButton("📝 Создать заказ", callback_data='create_order')],
            [InlineKeyboardButton("📋 Мои заказы", callback_data='my_client_orders')],
            [InlineKeyboardButton("🎯 Наши услуги", callback_data='our_services')],
            [InlineKeyboardButton("🎨 Наши работы", callback_data='our_works')],
            [InlineKeyboardButton("🚪 Выйти", callback_data='client_logout')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f'Добро пожаловать обратно, {client_login}!\nВыберите действие:',
            reply_markup=reply_markup
        )
    elif contractor_login:
        # Пользователь уже авторизован как исполнитель
        balance = firebase.get_balance(contractor_login)
        keyboard = [
            [InlineKeyboardButton("📋 Мои заказы", callback_data='my_orders')],
            [InlineKeyboardButton("👤 Личный кабинет", callback_data='personal_cabinet')],
            [InlineKeyboardButton("🚪 Выйти", callback_data='logout')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f'Добро пожаловать обратно, {contractor_login}!\nВаш баланс: {balance} руб.\nВыберите действие:',
            reply_markup=reply_markup
        )
    else:
        # Пользователь не авторизован - показываем главное меню
        welcome_text = """🎯 Добро пожаловать в Алтреза!

Мы — команда профессионалов, которая поможет вам:
• Создать эффективный сайт
• Разработать видео-контент
• Повысить продажи и узнаваемость

Выберите свою роль:"""

        keyboard = [
            [InlineKeyboardButton("👤 Я заказчик", callback_data='client')],
            [InlineKeyboardButton("🔧 Я исполнитель", callback_data='entrepreneur')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(welcome_text, reply_markup=reply_markup)


async def handle_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды админ"""
    user_id = update.message.from_user.id

    # Проверяем, является ли пользователь администратором
    if user_id != ADMIN_ID:
        await update.message.reply_text("У вас нет прав администратора.")
        return

    admin_text = """👑 ПАНЕЛЬ АДМИНИСТРАТОРА

Добро пожаловать в админ-панель!
Доступные функции:"""

    keyboard = [
        [InlineKeyboardButton("➕ Регистрация исполнителя", callback_data='register_entrepreneur')],
        [InlineKeyboardButton("👥 Все исполнители", callback_data='all_entrepreneurs')],
        [InlineKeyboardButton("📂 Управление портфолио", callback_data='portfolio_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(admin_text, reply_markup=reply_markup)


async def handle_unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик неизвестных команд"""
    await update.message.reply_text(
        "Неизвестная команда. Используйте /start для начала работы с ботом."
    )