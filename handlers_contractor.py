# handlers_contractor.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from state_manager import user_state


async def entrepreneur_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Меню исполнителя"""
    user_id = update.callback_query.from_user.id
    logged_in_user = user_state.get_entrepreneur_by_chat_id(user_id)

    keyboard = []

    if logged_in_user:
        # Пользователь авторизован
        keyboard.append([InlineKeyboardButton("Мои заказы", callback_data='my_orders')])
        keyboard.append([InlineKeyboardButton("Выйти", callback_data='logout')])
        context.user_data['contractor_login'] = logged_in_user
        balance = user_state.get_entrepreneur_balance(logged_in_user)
        message_text = f'Добро пожаловать, {logged_in_user}!\nВаш баланс: {balance} руб.\nВыберите действие:'
    else:
        # Пользователь не авторизован
        keyboard.append([InlineKeyboardButton("Войти", callback_data='login')])
        message_text = 'Выберите действие (Исполнитель):'

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(message_text, reply_markup=reply_markup)


async def add_service(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Добавление услуги"""
    await update.callback_query.edit_message_text(
        "Введите название услуги, описание и цену."
    )


async def my_portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Портфолио исполнителя"""
    portfolio = "Ваши услуги:\n1. Веб-разработка\n2. Дизайн сайтов\n3. SEO-оптимизация"
    await update.callback_query.edit_message_text(portfolio)


async def login_entrepreneur(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начало процесса входа"""
    await update.callback_query.edit_message_text("Введите логин:")
    user_state.set_state(update.callback_query.from_user.id, 'login')


async def my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показ заказов исполнителя"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    contractor_login = user_state.get_entrepreneur_by_chat_id(user_id)

    if contractor_login:
        orders = user_state.get_orders(contractor_login)
        balance = user_state.get_entrepreneur_balance(contractor_login)

        if orders:
            await query.edit_message_text(
                f"У вас {len(orders)} заказ(а/ов):\nВаш баланс: {balance} руб."
            )
            for i, order in enumerate(orders, start=1):
                if isinstance(order, dict):
                    # Новый формат заказа с дополнительной информацией
                    status = "✅ Принят" if order.get('accepted', False) else "⏳ Ожидает"
                    client = order.get('client_login', 'Не указан')

                    order_text = f"📋 Заказ {i}:\n{order.get('description', 'Описание отсутствует')}"
                    order_text += f"\n👤 Заказчик: {client}"
                    order_text += f"\n📊 Статус: {status}"

                    # Показываем таймер, если он активен
                    if order.get('timer_active', False) and 'timer_end' in order:
                        from datetime import datetime
                        from utils import format_time_remaining

                        end_time = datetime.fromisoformat(order['timer_end']) if isinstance(order['timer_end'],
                                                                                            str) else order['timer_end']
                        timer_info = format_time_remaining(end_time)
                        order_text += f"\n{timer_info}"

                    await query.message.reply_text(order_text)
                else:
                    # Старый формат заказа (строка)
                    await query.message.reply_text(f"Заказ {i}:\n{order}")
        else:
            await query.edit_message_text(f"У вас нет заказов.\nВаш баланс: {balance} руб.")
    else:
        await query.edit_message_text("Пожалуйста, войдите в систему сначала.")


async def logout_entrepreneur(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Выход из аккаунта"""
    user_id = update.callback_query.from_user.id
    contractor_login = user_state.get_entrepreneur_by_chat_id(user_id)

    if contractor_login:
        # Убираем chat_id из данных исполнителя
        user_state.remove_entrepreneur_chat_id(contractor_login)

        # Очищаем данные пользователя из контекста
        if 'contractor_login' in context.user_data:
            del context.user_data['contractor_login']

        # Показываем меню исполнителя после выхода
        keyboard = [
            [InlineKeyboardButton("Добавить услугу", callback_data='add_service')],
            [InlineKeyboardButton("Мое портфолио", callback_data='my_portfolio')],
            [InlineKeyboardButton("Войти", callback_data='login')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(
            "Вы успешно вышли из аккаунта.\nВыберите действие (Исполнитель):",
            reply_markup=reply_markup
        )
    else:
        await update.callback_query.edit_message_text("Ошибка при выходе из аккаунта.")


async def handle_login_process(update: Update, context: ContextTypes.DEFAULT_TYPE, state: str) -> bool:
    """
    Обрабатывает процесс входа исполнителя.
    Возвращает True, если сообщение было обработано этим хендлером.
    """
    user_id = update.message.from_user.id

    if state == 'login':
        context.user_data['login'] = update.message.text
        await update.message.reply_text("Введите пароль:")
        user_state.set_state(user_id, 'password')
        return True

    elif state == 'password':
        login = context.user_data.get('login')
        password = update.message.text

        if login and user_state.check_entrepreneur(login, password):
            # Успешный вход
            user_state.set_entrepreneur_chat_id(login, user_id)
            balance = user_state.get_entrepreneur_balance(login)

            keyboard = [
                [InlineKeyboardButton("Добавить услугу", callback_data='add_service')],
                [InlineKeyboardButton("Мое портфолио", callback_data='my_portfolio')],
                [InlineKeyboardButton("Мои заказы", callback_data='my_orders')],
                [InlineKeyboardButton("Выйти", callback_data='logout')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"Добро пожаловать в систему, {login}!\nВаш баланс: {balance} руб.\nВыберите действие:",
                reply_markup=reply_markup
            )
            context.user_data['contractor_login'] = login
        else:
            await update.message.reply_text("Данные неверные. Попробуйте снова.")

        user_state.set_state(user_id, None)
        return True

    return False