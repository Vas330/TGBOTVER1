# handlers_contractor.py - обновленная версия с кнопкой сдачи заказа
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime


async def entrepreneur_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Меню исполнителя с Firebase"""
    firebase = context.bot_data['firebase']
    user_id = update.callback_query.from_user.id
    logged_in_user = firebase.get_entrepreneur_by_chat_id(user_id)

    keyboard = []

    if logged_in_user:
        balance = firebase.get_balance(logged_in_user)
        keyboard.append([InlineKeyboardButton("📋 Мои заказы", callback_data='my_orders')])
        keyboard.append([InlineKeyboardButton("👤 Личный кабинет", callback_data='personal_cabinet')])
        keyboard.append([InlineKeyboardButton("🚪 Выйти", callback_data='logout')])

        context.user_data['contractor_login'] = logged_in_user
        message_text = f'Добро пожаловать в систему, {logged_in_user}!\nВаш баланс: {balance} руб.\n\nВыберите действие:'
    else:
        keyboard.append([InlineKeyboardButton("🔑 Войти", callback_data='login')])
        message_text = 'Выберите действие (Исполнитель):'

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(message_text, reply_markup=reply_markup)


async def login_entrepreneur(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Авторизация исполнителя"""
    firebase = context.bot_data['firebase']
    await update.callback_query.edit_message_text("Введите логин:")
    firebase.set_user_state(update.callback_query.from_user.id, 'login')


async def logout_entrepreneur(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Выход исполнителя"""
    firebase = context.bot_data['firebase']
    user_id = update.callback_query.from_user.id
    contractor_login = firebase.get_entrepreneur_by_chat_id(user_id)

    if contractor_login:
        firebase.set_entrepreneur_chat_id(contractor_login, None)

        if 'contractor_login' in context.user_data:
            del context.user_data['contractor_login']

        keyboard = [[InlineKeyboardButton("🔑 Войти", callback_data='login')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(
            "Вы успешно вышли из системы.\nВыберите действие (Исполнитель):",
            reply_markup=reply_markup
        )
    else:
        await update.callback_query.edit_message_text("Ошибка при выходе из системы.")


async def my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показ заказов исполнителя с правильными кнопками"""
    firebase = context.bot_data['firebase']
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    contractor_login = firebase.get_entrepreneur_by_chat_id(user_id)

    if contractor_login:
        orders = firebase.get_orders_by_executor(contractor_login)

        if orders:
            await query.edit_message_text(f"У вас {len(orders)} заказ(а/ов):")

            for i, order in enumerate(orders, start=1):
                status = order.get('status', 'unknown')

                status_map = {
                    'completed': ('Завершен', '✅'),
                    'on_review': ('На проверке', '🔍'),
                    'in_work': ('В работе', '🔄'),
                    'cancelled': ('Отменен', '❌'),
                    'dispute': ('Спор', '⚠️'),
                    'pending': ('Ожидает принятия', '📋'),
                    'waiting_payment': ('Ожидает оплаты', '💳'),
                    'payment_confirmed': ('Оплата подтверждена', '💰')
                }

                status_text, status_icon = status_map.get(status, ('Неизвестно', '❓'))

                customer = order.get('customer', {}).get('username', 'Неизвестен')
                amount = order.get('amount', 0)

                order_text = f"{status_icon} Заказ {i}: {order.get('title', 'Без названия')}\n"
                order_text += f"Описание: {order.get('description', 'Описание отсутствует')[:100]}...\n"
                order_text += f"Заказчик: {customer}\n"
                order_text += f"Бюджет: {amount} руб.\n"
                order_text += f"Статус: {status_text}"

                # Создаем кнопки для каждого заказа в зависимости от статуса
                keyboard = []

                # Кнопка чата для заказов в работе или на проверке
                if status in ['in_work', 'on_review']:
                    keyboard.append(
                        [InlineKeyboardButton("💬 Открыть чат", callback_data=f'open_contractor_chat_{order["id"]}')])

                # Кнопка сдачи заказа для заказов в работе
                if status == 'in_work':
                    keyboard.append([
                        InlineKeyboardButton("🎯 Сдать заказ на проверку", callback_data=f'submit_work_{order["id"]}')
                    ])

                # Кнопка деталей заказа
                keyboard.append([InlineKeyboardButton("📋 Детали", callback_data=f'contractor_order_{order["id"]}')])

                # Отправляем сообщение с кнопками
                if keyboard:
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await query.message.reply_text(order_text, reply_markup=reply_markup)
                else:
                    await query.message.reply_text(order_text)

        else:
            await query.edit_message_text("У вас нет заказов.")
    else:
        await query.edit_message_text("Пожалуйста, войдите в систему сначала.")


async def show_contractor_order_details(update: Update, context: ContextTypes.DEFAULT_TYPE, order_id: str) -> None:
    """Показывает детали заказа исполнителя с кнопками в зависимости от статуса"""
    firebase = context.bot_data['firebase']
    user_id = update.callback_query.from_user.id
    contractor_login = firebase.get_entrepreneur_by_chat_id(user_id)

    if not contractor_login:
        await update.callback_query.edit_message_text("Необходимо войти в систему.")
        return

    order = firebase.get_order_by_id(order_id)
    if not order:
        await update.callback_query.edit_message_text("Заказ не найден.")
        return

    # Проверяем, что это заказ исполнителя
    if order.get('executor', {}).get('username') != contractor_login:
        await update.callback_query.edit_message_text("У вас нет доступа к этому заказу.")
        return

    status = order.get('status', 'unknown')
    status_map = {
        'in_work': 'В работе',
        'on_review': 'На проверке',
        'completed': 'Завершен',
        'cancelled': 'Отменен',
        'dispute': 'Спор',
        'pending': 'Ожидает принятия',
        'waiting_payment': 'Ожидает оплаты',
        'payment_confirmed': 'Оплата подтверждена'
    }

    status_text = status_map.get(status, 'Неизвестно')
    customer_name = order.get('customer', {}).get('username', 'Неизвестен')

    details_text = f"ДЕТАЛИ ЗАКАЗА\n"
    details_text += f"━━━━━━━━━━━━━━━━━\n\n"
    details_text += f"Название: {order.get('title', 'Без названия')}\n"
    details_text += f"Описание: {order.get('description', 'Описание отсутствует')}\n"
    details_text += f"Заказчик: {customer_name}\n"
    details_text += f"Бюджет: {order.get('amount', 0)} руб.\n"
    details_text += f"Статус: {status_text}\n"

    keyboard = []

    # Кнопка чата для заказов в работе или на проверке
    if status in ['in_work', 'on_review']:
        keyboard.append([InlineKeyboardButton("💬 Открыть чат", callback_data=f'open_contractor_chat_{order_id}')])

    # Кнопка сдачи заказа для заказов в работе
    if status == 'in_work':
        keyboard.append([
            InlineKeyboardButton("🎯 Сдать заказ на проверку", callback_data=f'submit_work_{order_id}')
        ])

    keyboard.append([InlineKeyboardButton("◀️ К моим заказам", callback_data='my_orders')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(details_text, reply_markup=reply_markup)


async def open_contractor_chat(update: Update, context: ContextTypes.DEFAULT_TYPE, order_id: str) -> None:
    """Открывает чат для исполнителя"""
    firebase = context.bot_data['firebase']
    user_id = update.callback_query.from_user.id
    contractor_login = firebase.get_entrepreneur_by_chat_id(user_id)

    if not contractor_login:
        await update.callback_query.edit_message_text("Необходимо войти в систему.")
        return

    order = firebase.get_order_by_id(order_id)
    if not order:
        await update.callback_query.edit_message_text("Заказ не найден.")
        return

    # Проверяем права доступа
    if order.get('executor', {}).get('username') != contractor_login:
        await update.callback_query.edit_message_text("У вас нет доступа к этому заказу.")
        return

    customer_name = order.get('customer', {}).get('username', 'Неизвестен')

    # Получаем сообщения из чата
    messages = firebase.get_messages_by_order(order_id)

    chat_text = f"ЧАТ ПО ЗАКАЗУ\n"
    chat_text += f"━━━━━━━━━━━━━━━━━\n"
    chat_text += f"Заказ: {order.get('title', 'Без названия')}\n"
    chat_text += f"Заказчик: {customer_name}\n\n"

    if messages:
        chat_text += "Последние сообщения:\n"
        chat_text += "─────────────────\n"

        for msg in messages[-10:]:  # Показываем последние 10 сообщений
            role_text = "Заказчик" if msg.get('user_role') == 'customer' else "Вы"
            if msg.get('user_role') == 'admin':
                role_text = "Администратор"

            chat_text += f"{role_text}: {msg.get('text', '')}\n\n"
    else:
        chat_text += "Сообщений пока нет\n\n"

    chat_text += "Для отправки сообщения просто напишите текст."

    # Устанавливаем состояние чата
    firebase.set_user_state(user_id, f'in_contractor_chat_{order_id}')

    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data=f'open_contractor_chat_{order_id}')],
        [InlineKeyboardButton("◀️ К деталям заказа", callback_data=f'contractor_order_{order_id}')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(chat_text, reply_markup=reply_markup)


async def submit_work(update: Update, context: ContextTypes.DEFAULT_TYPE, order_id: str) -> None:
    """Сдача заказа на проверку исполнителем"""
    firebase = context.bot_data['firebase']
    user_id = update.callback_query.from_user.id
    contractor_login = firebase.get_entrepreneur_by_chat_id(user_id)

    if not contractor_login:
        await update.callback_query.edit_message_text("Необходимо войти в систему.")
        return

    order = firebase.get_order_by_id(order_id)
    if not order or order.get('executor', {}).get('username') != contractor_login:
        await update.callback_query.edit_message_text("У вас нет доступа к этому заказу.")
        return

    # Обновляем статус заказа
    firebase.update_order(order_id, {
        'status': 'on_review',
        'submitted_for_review': True,
        'submitted_at': datetime.now()
    })

    # Уведомляем клиента
    customer_username = order.get('customer', {}).get('username')
    if customer_username:
        customer_chat_id = firebase.get_user_chat_id_by_username(customer_username)
        if customer_chat_id:
            keyboard = [
                [InlineKeyboardButton("✅ Принять работу", callback_data=f'accept_work_{order_id}')],
                [InlineKeyboardButton("🔄 На доработку", callback_data=f'request_revision_{order_id}')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            try:
                await context.bot.send_message(
                    chat_id=customer_chat_id,
                    text=f"🎯 ЗАКАЗ ГОТОВ К ПРОВЕРКЕ!\n\n"
                         f"📋 Заказ: {order.get('title', 'Без названия')}\n"
                         f"👤 Исполнитель: {contractor_login}\n"
                         f"💰 Сумма: {order.get('amount', 0)} руб.\n\n"
                         f"Исполнитель завершил работу над заказом.\n"
                         f"Проверьте результат и примите решение:",
                    reply_markup=reply_markup
                )
                print(f"Уведомление о завершении работы отправлено клиенту {customer_username}")
            except Exception as e:
                print(f"Ошибка уведомления клиента: {e}")

    await update.callback_query.edit_message_text(
        "🎯 ЗАКАЗ СДАН НА ПРОВЕРКУ!\n\n"
        f"Заказ: {order.get('title', 'Без названия')}\n\n"
        "Клиент получил уведомление о готовности работы.\n"
        "Ожидайте решения клиента о приемке."
    )


async def personal_cabinet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Личный кабинет исполнителя"""
    firebase = context.bot_data['firebase']
    user_id = update.callback_query.from_user.id
    contractor_login = firebase.get_entrepreneur_by_chat_id(user_id)

    if contractor_login:
        balance = firebase.get_balance(contractor_login)
        rating = firebase.get_rating(contractor_login)

        cabinet_text = f"👤 ЛИЧНЫЙ КАБИНЕТ\n"
        cabinet_text += f"━━━━━━━━━━━━━━━━━\n\n"
        cabinet_text += f"📝 Логин: {contractor_login}\n"
        cabinet_text += f"💰 Баланс: {balance} руб.\n"
        cabinet_text += f"⭐ Рейтинг: {rating}/10\n"

        keyboard = []

        # Кнопки вывода средств в зависимости от баланса
        if balance >= 1000:
            keyboard.append([
                InlineKeyboardButton("💸 Вывести 500₽", callback_data=f'withdraw_amount_{contractor_login}_500'),
                InlineKeyboardButton("💸 Вывести 1000₽", callback_data=f'withdraw_amount_{contractor_login}_1000')
            ])
            if balance >= 2000:
                keyboard.append(
                    [InlineKeyboardButton("💸 Вывести 2000₽", callback_data=f'withdraw_amount_{contractor_login}_2000')])

            keyboard.append(
                [InlineKeyboardButton("💸 Другая сумма", callback_data=f'withdraw_custom_{contractor_login}')])
        else:
            keyboard.append([InlineKeyboardButton("💸 Недостаточно средств", callback_data='withdraw_unavailable')])

        keyboard.append([InlineKeyboardButton("◀️ Назад к меню", callback_data='entrepreneur')])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(cabinet_text, reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text("Необходимо войти в систему.")


async def withdraw_money(update: Update, context: ContextTypes.DEFAULT_TYPE, contractor_login: str) -> None:
    """Меню вывода средств"""
    firebase = context.bot_data['firebase']
    balance = firebase.get_balance(contractor_login)

    withdraw_text = f"💸 ВЫВОД СРЕДСТВ\n"
    withdraw_text += f"━━━━━━━━━━━━━━━━━\n\n"
    withdraw_text += f"Доступно: {balance} руб.\n\n"
    withdraw_text += f"Выберите сумму для вывода:"

    keyboard = []

    if balance >= 1000:
        keyboard.append([
            InlineKeyboardButton("500 руб.", callback_data=f'withdraw_amount_{contractor_login}_500'),
            InlineKeyboardButton("1000 руб.", callback_data=f'withdraw_amount_{contractor_login}_1000')
        ])
        if balance >= 2000:
            keyboard.append(
                [InlineKeyboardButton("2000 руб.", callback_data=f'withdraw_amount_{contractor_login}_2000')])

        keyboard.append([InlineKeyboardButton("💸 Другая сумма", callback_data=f'withdraw_custom_{contractor_login}')])
    else:
        keyboard.append([InlineKeyboardButton("💸 Недостаточно средств", callback_data='withdraw_unavailable')])

    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data='personal_cabinet')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(withdraw_text, reply_markup=reply_markup)


async def process_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE, contractor_login: str,
                             amount: float) -> None:
    """Обработка вывода средств"""
    firebase = context.bot_data['firebase']
    current_balance = firebase.get_balance(contractor_login)

    if amount <= current_balance:
        firebase.update_balance(contractor_login, -amount)

        await update.callback_query.edit_message_text(
            f"✅ ВЫВОД ВЫПОЛНЕН\n\n"
            f"Сумма: {amount} руб.\n"
            f"Новый баланс: {current_balance - amount} руб.\n\n"
            f"Средства поступят на вашу карту в течение 1-3 рабочих дней."
        )
    else:
        await update.callback_query.edit_message_text(
            f"❌ НЕДОСТАТОЧНО СРЕДСТВ\n\n"
            f"Запрошено: {amount} руб.\n"
            f"Доступно: {current_balance} руб."
        )


async def withdraw_custom_amount(update: Update, context: ContextTypes.DEFAULT_TYPE, contractor_login: str) -> None:
    """Запрос произвольной суммы для вывода"""
    firebase = context.bot_data['firebase']
    balance = firebase.get_balance(contractor_login)

    await update.callback_query.edit_message_text(
        f"💸 ПРОИЗВОЛЬНАЯ СУММА\n\n"
        f"Доступно: {balance} руб.\n\n"
        f"Введите сумму для вывода (минимум 100 руб.):"
    )

    firebase.set_user_state(update.callback_query.from_user.id, f'withdraw_amount_input_{contractor_login}')


async def order_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Детали заказа (заглушка)"""
    await update.callback_query.edit_message_text("Функция в разработке...")