# handlers_common.py - с защитой от отсутствующего Firebase
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import ADMIN_ID


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start с защитой от None Firebase"""
    firebase = context.bot_data.get('firebase')
    user_id = update.message.from_user.id
    
    print(f"DEBUG: /start от пользователя {user_id}")
    print(f"DEBUG: Firebase доступен: {firebase is not None}")

    # Если Firebase недоступен, показываем главное меню
    if not firebase:
        await show_main_menu(update)
        return

    try:
        # Проверяем роли пользователя только если Firebase работает
        client_login = firebase.get_client_by_chat_id(user_id)
        contractor_login = firebase.get_entrepreneur_by_chat_id(user_id)
        
        print(f"DEBUG: client_login={client_login}, contractor_login={contractor_login}")

        if client_login and contractor_login:
            # Пользователь в обеих ролях
            await show_role_selection_menu(update, client_login, contractor_login)
            
        elif client_login:
            # Авторизованный клиент
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
            # Авторизованный исполнитель
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
            # Неавторизованный пользователь
            await show_main_menu(update)
            
    except Exception as e:
        print(f"Ошибка в /start: {e}")
        # При любой ошибке показываем главное меню
        await show_main_menu(update)


async def show_main_menu(update: Update) -> None:
    """Показывает главное меню выбора роли"""
    firebase = update.get_bot().bot_data.get('firebase') if hasattr(update, 'get_bot') else None
    
    if not firebase:
        welcome_text = """🎯 Добро пожаловать в Алтреза!

⚠️ База данных временно недоступна
Полная функциональность ограничена

Мы — команда профессионалов, которая поможет вам:
• Создать эффективный сайт
• Разработать видео-контент
• Повысить продажи и узнаваемость

Выберите свою роль:"""
    else:
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


async def show_role_selection_menu(update: Update, client_login: str, contractor_login: str) -> None:
    """Показывает меню выбора роли для пользователей с двумя ролями"""
    text = f"""👤 Добро пожаловать!

Вы зарегистрированы в системе в двух ролях:
• Заказчик: {client_login}
• Исполнитель: {contractor_login}

В какой роли хотите работать?"""

    keyboard = [
        [InlineKeyboardButton("👤 Войти как заказчик", callback_data='client')],
        [InlineKeyboardButton("🔧 Войти как исполнитель", callback_data='entrepreneur')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(text, reply_markup=reply_markup)


async def handle_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды админ"""
    user_id = update.message.from_user.id

    if user_id != ADMIN_ID:
        await update.message.reply_text("У вас нет прав администратора.")
        return

    firebase = context.bot_data.get('firebase')
    
    if not firebase:
        admin_text = """👑 ПАНЕЛЬ АДМИНИСТРАТОРА

⚠️ База данных недоступна
Функции администратора ограничены

Для полной функциональности настройте Firebase."""
        
        await update.message.reply_text(admin_text)
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
    firebase = context.bot_data.get('firebase')
    user_id = update.message.from_user.id
    
    # Очищаем состояние пользователя если Firebase доступен
    if firebase:
        try:
            firebase.clear_user_state(user_id)
        except:
            pass
    
    await update.message.reply_text(
        "Неизвестная команда. Используйте /start для начала работы с ботом."
    )
