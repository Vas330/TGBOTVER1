# handlers_client.py - полная версия с чатом и обновленным меню
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime


async def client_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Меню заказчика с Firebase"""
    firebase = context.bot_data['firebase']
    user_id = update.callback_query.from_user.id
    logged_in_user = firebase.get_client_by_chat_id(user_id)

    keyboard = []

    if logged_in_user:
        # Пользователь авторизован
        keyboard.append([InlineKeyboardButton("📝 Создать заказ", callback_data='create_order')])
        keyboard.append([InlineKeyboardButton("📋 Мои заказы", callback_data='my_client_orders')])
        keyboard.append([InlineKeyboardButton("🎯 Наши услуги", callback_data='our_services')])
        keyboard.append([InlineKeyboardButton("🎨 Наши работы", callback_data='our_works')])
        keyboard.append([InlineKeyboardButton("🚪 Выйти", callback_data='client_logout')])

        context.user_data['client_login'] = logged_in_user
        message_text = f'Добро пожаловать, {logged_in_user}!\nВыберите действие:'
    else:
        # Пользователь не авторизован
        keyboard.append([InlineKeyboardButton("🔑 Войти", callback_data='client_login')])
        keyboard.append([InlineKeyboardButton("📝 Регистрация", callback_data='client_register')])
        keyboard.append([InlineKeyboardButton("🎯 Наши услуги", callback_data='our_services')])
        keyboard.append([InlineKeyboardButton("🎨 Наши работы", callback_data='our_works')])
        keyboard.append([InlineKeyboardButton("💬 Консультация", callback_data='consultation')])

        message_text = 'Выберите действие (Заказчик):'

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(message_text, reply_markup=reply_markup)


async def show_portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показ портфолио с Firebase"""
    firebase = context.bot_data['firebase']
    portfolio_items = firebase.get_portfolio()

    if portfolio_items:
        for item in portfolio_items:
            caption = f"{item.get('title', 'Без названия')}\n{item.get('description', 'Описание отсутствует')}"
            if item.get('photo_type') == 'file_id':
                await update.callback_query.message.reply_photo(item['photo'], caption=caption)
            else:
                await update.callback_query.message.reply_text(f"Фото: {item.get('photo', 'Отсутствует')}\n{caption}")
    else:
        await update.callback_query.edit_message_text("Портфолио пусто.")


async def create_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начало создания заказа с Firebase"""
    firebase = context.bot_data['firebase']
    user_id = update.callback_query.from_user.id
    client_login = firebase.get_client_by_chat_id(user_id)

    if client_login:
        await update.callback_query.edit_message_text(
            "Расскажите подробно, что вам нужно.\n"
            "Например: нужен лендинг для продажи курсов, адаптивный дизайн, интеграция с платежкой."
        )
        firebase.set_user_state(user_id, 'order_description')
    else:
        await update.callback_query.edit_message_text("Для создания заказа необходимо войти в аккаунт.")


async def consultation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Консультация"""
    await update.callback_query.edit_message_text(
        "Бесплатная консультация!\n\n"
        "Оставьте заявку, и наш менеджер свяжется с вами в течение часа:\n"
        "@YourManagerUsername"
    )


async def client_login(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Авторизация клиента"""
    firebase = context.bot_data['firebase']
    await update.callback_query.edit_message_text("Введите логин:")
    firebase.set_user_state(update.callback_query.from_user.id, 'client_login_username')


async def client_register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Регистрация клиента"""
    firebase = context.bot_data['firebase']
    await update.callback_query.edit_message_text("Введите логин для регистрации:")
    firebase.set_user_state(update.callback_query.from_user.id, 'client_register_username')


async def client_logout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Выход клиента"""
    firebase = context.bot_data['firebase']
    user_id = update.callback_query.from_user.id
    client_login = firebase.get_client_by_chat_id(user_id)

    if client_login:
        firebase.set_client_chat_id(client_login, None)

        if 'client_login' in context.user_data:
            del context.user_data['client_login']

        # Показываем меню заказчика после выхода
        keyboard = [
            [InlineKeyboardButton("🔑 Войти", callback_data='client_login')],
            [InlineKeyboardButton("📝 Регистрация", callback_data='client_register')],
            [InlineKeyboardButton("🎯 Наши услуги", callback_data='our_services')],
            [InlineKeyboardButton("🎨 Наши работы", callback_data='our_works')],
            [InlineKeyboardButton("💬 Консультация", callback_data='consultation')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(
            "Вы успешно вышли из аккаунта.\nВыберите действие (Заказчик):",
            reply_markup=reply_markup
        )
    else:
        await update.callback_query.edit_message_text("Ошибка при выходе из аккаунта.")


async def my_client_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показ заказов клиента с Firebase и правильными кнопками"""
    firebase = context.bot_data['firebase']
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    client_login = firebase.get_client_by_chat_id(user_id)

    if client_login:
        orders = firebase.get_orders_by_customer(client_login)

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
                    'payment_confirmed': ('Оплата подтверждена', '💰'),
                    'accepted_waiting_payment': ('Принят, ожидает оплаты', '🕐')
                }

                status_text, status_icon = status_map.get(status, ('Неизвестно', '❓'))

                executor = order.get('executor', {}).get('username', 'Не назначен')
                amount = order.get('amount', 0)

                order_text = f"{status_icon} Заказ {i}: {order.get('title', 'Без названия')}\n"
                order_text += f"Описание: {order.get('description', 'Описание отсутствует')[:100]}...\n"
                order_text += f"Исполнитель: {executor}\n"
                order_text += f"Бюджет: {amount} руб.\n"
                order_text += f"Статус: {status_text}"

                # Создаем кнопки для каждого заказа в зависимости от статуса
                keyboard = []

                # Кнопка чата показывается для заказов в работе или на проверке
                if status in ['in_work', 'on_review']:
                    keyboard.append(
                        [InlineKeyboardButton("💬 Открыть чат", callback_data=f'open_client_chat_{order["id"]}')])

                # Кнопки для заказа на проверке
                if status == 'on_review':
                    keyboard.append([
                        InlineKeyboardButton("✅ Принять работу", callback_data=f'accept_work_{order["id"]}'),
                        InlineKeyboardButton("🔄 На доработку", callback_data=f'request_revision_{order["id"]}')
                    ])

                # Кнопка деталей заказа
                keyboard.append([InlineKeyboardButton("📋 Детали", callback_data=f'client_order_{order["id"]}')])

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


async def show_client_order_details(update: Update, context: ContextTypes.DEFAULT_TYPE, order_id: str) -> None:
    """Показывает детали заказа клиента с кнопками в зависимости от статуса"""
    firebase = context.bot_data['firebase']
    user_id = update.callback_query.from_user.id
    client_login = firebase.get_client_by_chat_id(user_id)

    if not client_login:
        await update.callback_query.edit_message_text("Необходимо войти в систему.")
        return

    order = firebase.get_order_by_id(order_id)
    if not order:
        await update.callback_query.edit_message_text("Заказ не найден.")
        return

    # Проверяем, что это заказ клиента
    if order.get('customer', {}).get('username') != client_login:
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
    executor_name = order.get('executor', {}).get('username', 'Не назначен')

    details_text = f"ДЕТАЛИ ЗАКАЗА\n"
    details_text += f"━━━━━━━━━━━━━━━━━\n\n"
    details_text += f"Название: {order.get('title', 'Без названия')}\n"
    details_text += f"Описание: {order.get('description', 'Описание отсутствует')}\n"
    details_text += f"Исполнитель: {executor_name}\n"
    details_text += f"Бюджет: {order.get('amount', 0)} руб.\n"
    details_text += f"Статус: {status_text}\n"

    keyboard = []

    # Кнопка чата для заказов в работе или на проверке
    if status in ['in_work', 'on_review']:
        keyboard.append([InlineKeyboardButton("💬 Открыть чат", callback_data=f'open_client_chat_{order_id}')])

    # Кнопки для заказа на проверке
    if status == 'on_review':
        keyboard.append([
            InlineKeyboardButton("✅ Принять работу", callback_data=f'accept_work_{order_id}'),
            InlineKeyboardButton("🔄 На доработку", callback_data=f'request_revision_{order_id}')
        ])

    keyboard.append([InlineKeyboardButton("◀️ К моим заказам", callback_data='my_client_orders')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(details_text, reply_markup=reply_markup)


async def open_client_chat(update: Update, context: ContextTypes.DEFAULT_TYPE, order_id: str) -> None:
    """Открывает чат для клиента"""
    firebase = context.bot_data['firebase']
    user_id = update.callback_query.from_user.id
    client_login = firebase.get_client_by_chat_id(user_id)

    if not client_login:
        await update.callback_query.edit_message_text("Необходимо войти в систему.")
        return

    order = firebase.get_order_by_id(order_id)
    if not order:
        await update.callback_query.edit_message_text("Заказ не найден.")
        return

    # Проверяем права доступа
    if order.get('customer', {}).get('username') != client_login:
        await update.callback_query.edit_message_text("У вас нет доступа к этому заказу.")
        return

    executor_name = order.get('executor', {}).get('username', 'Не назначен')

    # Получаем сообщения из чата
    messages = firebase.get_messages_by_order(order_id)

    chat_text = f"ЧАТ ПО ЗАКАЗУ\n"
    chat_text += f"━━━━━━━━━━━━━━━━━\n"
    chat_text += f"Заказ: {order.get('title', 'Без названия')}\n"
    chat_text += f"Исполнитель: {executor_name}\n\n"

    if messages:
        chat_text += "Последние сообщения:\n"
        chat_text += "─────────────────\n"

        for msg in messages[-10:]:  # Показываем последние 10 сообщений
            role_text = "Вы" if msg.get('user_role') == 'customer' else "Исполнитель"
            if msg.get('user_role') == 'admin':
                role_text = "Администратор"

            chat_text += f"{role_text}: {msg.get('text', '')}\n\n"
    else:
        chat_text += "Сообщений пока нет\n\n"

    chat_text += "Для отправки сообщения просто напишите текст."

    # Устанавливаем состояние чата
    firebase.set_user_state(user_id, f'in_client_chat_{order_id}')

    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data=f'open_client_chat_{order_id}')],
        [InlineKeyboardButton("◀️ К деталям заказа", callback_data=f'client_order_{order_id}')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(chat_text, reply_markup=reply_markup)


async def accept_work(update: Update, context: ContextTypes.DEFAULT_TYPE, order_id: str) -> None:
    """Принятие работы клиентом"""
    firebase = context.bot_data['firebase']
    user_id = update.callback_query.from_user.id
    client_login = firebase.get_client_by_chat_id(user_id)

    if not client_login:
        await update.callback_query.edit_message_text("Необходимо войти в систему.")
        return

    order = firebase.get_order_by_id(order_id)
    if not order or order.get('customer', {}).get('username') != client_login:
        await update.callback_query.edit_message_text("У вас нет доступа к этому заказу.")
        return

    # Обновляем статус заказа
    firebase.update_order(order_id, {
        'status': 'completed',
        'completed_at': datetime.now(),
        'client_accepted': True
    })

    # Переводим деньги исполнителю
    executor_username = order.get('executor', {}).get('username')
    if executor_username:
        order_amount = order.get('amount', 0)
        firebase.update_balance(executor_username, order_amount)

        # Уведомляем исполнителя
        executor_chat_id = firebase.get_user_chat_id_by_username(executor_username)
        if executor_chat_id:
            try:
                await context.bot.send_message(
                    chat_id=executor_chat_id,
                    text=f"🎉 ЗАКАЗ ПРИНЯТ КЛИЕНТОМ!\n\n"
                         f"📋 Заказ: {order.get('title', 'Без названия')}\n"
                         f"💰 Вы получили: {order_amount} руб.\n\n"
                         f"Спасибо за отличную работу!"
                )
            except Exception as e:
                print(f"Ошибка уведомления исполнителя: {e}")

    await update.callback_query.edit_message_text(
        "✅ РАБОТА ПРИНЯТА!\n\n"
        f"Заказ: {order.get('title', 'Без названия')}\n"
        f"Исполнитель получил оплату: {order.get('amount', 0)} руб.\n\n"
        "Спасибо за работу с нами!"
    )


async def request_revision(update: Update, context: ContextTypes.DEFAULT_TYPE, order_id: str) -> None:
    """Отправка заказа на доработку"""
    firebase = context.bot_data['firebase']
    user_id = update.callback_query.from_user.id
    client_login = firebase.get_client_by_chat_id(user_id)

    if not client_login:
        await update.callback_query.edit_message_text("Необходимо войти в систему.")
        return

    order = firebase.get_order_by_id(order_id)
    if not order or order.get('customer', {}).get('username') != client_login:
        await update.callback_query.edit_message_text("У вас нет доступа к этому заказу.")
        return

    # Обновляем статус заказа
    firebase.update_order(order_id, {
        'status': 'in_work',
        'revision_requested_at': datetime.now(),
        'revision_count': order.get('revision_count', 0) + 1
    })

    # Уведомляем исполнителя
    executor_username = order.get('executor', {}).get('username')
    if executor_username:
        executor_chat_id = firebase.get_user_chat_id_by_username(executor_username)
        if executor_chat_id:
            # Создаем кнопки для исполнителя
            keyboard = [
                [InlineKeyboardButton("💬 Открыть чат с клиентом", callback_data=f'open_contractor_chat_{order_id}')],
                [InlineKeyboardButton("🎯 Сдать заказ на проверку", callback_data=f'submit_work_{order_id}')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            try:
                await context.bot.send_message(
                    chat_id=executor_chat_id,
                    text=f"🔄 ЗАКАЗ ОТПРАВЛЕН НА ДОРАБОТКУ\n\n"
                         f"📋 Заказ: {order.get('title', 'Без названия')}\n"
                         f"👤 Клиент: {client_login}\n\n"
                         f"Клиент просит внести изменения в работу.\n"
                         f"Свяжитесь с ним через чат для уточнения деталей.",
                    reply_markup=reply_markup
                )
            except Exception as e:
                print(f"Ошибка уведомления исполнителя: {e}")

    await update.callback_query.edit_message_text(
        "🔄 ЗАКАЗ ОТПРАВЛЕН НА ДОРАБОТКУ\n\n"
        f"Заказ: {order.get('title', 'Без названия')}\n\n"
        "Исполнитель получил уведомление о необходимости доработки.\n"
        "Вы можете обсудить детали в чате заказа."
    )


async def our_works(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показ наших работ по категориям с Firebase"""
    firebase = context.bot_data['firebase']

    works_text = "🎨 НАШИ РАБОТЫ\n\n"
    works_text += "Посмотрите примеры наших проектов по направлениям:"

    keyboard = [
        [InlineKeyboardButton("🌐 Сайты", callback_data='category_sites')],
        [InlineKeyboardButton("🎬 Видео", callback_data='category_video')],
        [InlineKeyboardButton("◀️ Назад", callback_data='client')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(works_text, reply_markup=reply_markup)


async def category_sites(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показ работ категории 'Сайты'"""
    firebase = context.bot_data['firebase']

    sites_text = "🌐 НАШИ САЙТЫ\n\n"
    sites_text += "Выберите тип проекта:"

    keyboard = [
        [InlineKeyboardButton("📄 Лендинги", callback_data='subcategory_landing')],
        [InlineKeyboardButton("🛒 Интернет-магазины", callback_data='subcategory_shop')],
        [InlineKeyboardButton("🏢 Корпоративные сайты", callback_data='subcategory_corporate')],
        [InlineKeyboardButton("◀️ К работам", callback_data='our_works')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(sites_text, reply_markup=reply_markup)


async def category_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показ работ категории 'Видео'"""
    firebase = context.bot_data['firebase']

    video_text = "🎬 НАШИ ВИДЕО\n\n"
    video_text += "Выберите тип проекта:"

    keyboard = [
        [InlineKeyboardButton("📺 Рекламные ролики", callback_data='subcategory_ads')],
        [InlineKeyboardButton("📱 Креативы для соцсетей", callback_data='subcategory_social')],
        [InlineKeyboardButton("🎨 Анимация", callback_data='subcategory_animation')],
        [InlineKeyboardButton("◀️ К работам", callback_data='our_works')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(video_text, reply_markup=reply_markup)


async def show_subcategory_works(update: Update, context: ContextTypes.DEFAULT_TYPE, subcategory: str) -> None:
    """Показ работ подкатегории"""
    firebase = context.bot_data['firebase']
    works = firebase.get_works_by_subcategory(subcategory)

    subcategory_names = {
        'landing': 'Лендинги',
        'shop': 'Интернет-магазины',
        'corporate': 'Корпоративные сайты',
        'ads': 'Рекламные ролики',
        'social': 'Креативы для соцсетей',
        'animation': 'Анимация'
    }

    category_name = subcategory_names.get(subcategory, 'Работы')

    if works:
        works_text = f"{category_name.upper()}\n\n"
        works_text += f"Найдено проектов: {len(works)}"

        keyboard = []
        for i, work in enumerate(works):
            keyboard.append([InlineKeyboardButton(
                f"{i + 1}. {work.get('title', 'Без названия')}",
                callback_data=f'portfolio_item_{subcategory}_{i}'
            )])

        # Определяем кнопку "Назад" в зависимости от категории
        if subcategory in ['landing', 'shop', 'corporate']:
            keyboard.append([InlineKeyboardButton("◀️ К сайтам", callback_data='category_sites')])
        else:
            keyboard.append([InlineKeyboardButton("◀️ К видео", callback_data='category_video')])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(works_text, reply_markup=reply_markup)
    else:
        back_callback = 'category_sites' if subcategory in ['landing', 'shop', 'corporate'] else 'category_video'

        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data=back_callback)]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            f"{category_name}\n\nВ этой категории пока нет работ.",
            reply_markup=reply_markup
        )


async def show_portfolio_item(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str, index: int) -> None:
    """Показ конкретного элемента портфолио"""
    firebase = context.bot_data['firebase']
    works = firebase.get_works_by_subcategory(category)

    if works and index < len(works):
        work = works[index]

        caption = f"📋 {work.get('title', 'Без названия')}\n"
        caption += f"📝 {work.get('description', 'Описание отсутствует')}\n"

        if work.get('url'):
            caption += f"🔗 Ссылка: {work['url']}\n"

        if work.get('price'):
            caption += f"💰 Стоимость: {work['price']} руб."

        keyboard = [[InlineKeyboardButton("◀️ Назад к списку", callback_data=f'subcategory_{category}')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Отправляем фото или текст
        if work.get('photo') and work.get('photo_type') == 'file_id':
            await update.callback_query.message.reply_photo(
                work['photo'],
                caption=caption,
                reply_markup=reply_markup
            )
        else:
            await update.callback_query.edit_message_text(caption, reply_markup=reply_markup)
    else:
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data=f'subcategory_{category}')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text("Работа не найдена.", reply_markup=reply_markup)


async def handle_order_response(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str,
                                customer_id: int) -> None:
    """Обработка ответа исполнителя на заказ"""
    firebase = context.bot_data['firebase']
    query = update.callback_query
    contractor_user_id = query.from_user.id
    contractor_login = firebase.get_entrepreneur_by_chat_id(contractor_user_id)

    if not contractor_login:
        await query.edit_message_text("Ошибка: необходимо войти в систему.")
        return

    if action == 'accept':
        # Ищем последний заказ для данного клиента с данным исполнителем
        orders_ref = firebase.db.collection('orders')

        # Получаем клиента по customer_id
        customer_login = firebase.get_client_by_chat_id(customer_id)
        if not customer_login:
            await query.edit_message_text("Ошибка: клиент не найден.")
            return

        # Ищем заказы клиента со статусом pending
        query_orders = orders_ref.where('customer.username', '==', customer_login).where('status', '==',
                                                                                         'pending').where(
            'executor.username', '==', contractor_login)
        orders = query_orders.get()

        if orders:
            # Берем первый найденный заказ
            order_doc = orders[0]
            order_id = order_doc.id

            # Обновляем заказ в Firebase
            firebase.update_order(order_id, {
                'accepted': True,
                'status': 'accepted_waiting_payment',
                'executor': {
                    'id': str(contractor_user_id),
                    'username': contractor_login
                },
                'accepted_at': datetime.now()
            })

            await query.edit_message_text("Заказ принят! Отправляем клиенту QR-код для оплаты...")

            # Отправляем QR-код для оплаты
            from payment_handlers import send_payment_request
            await send_payment_request(update, context, order_id)

            # Уведомляем клиента
            try:
                await context.bot.send_message(
                    chat_id=customer_id,
                    text=f"🎉 Отлично! Исполнитель {contractor_login} принял ваш заказ.\n\n"
                         f"Для начала работы необходимо произвести оплату.\n"
                         f"QR-код для оплаты отправлен вам отдельным сообщением."
                )
            except Exception as e:
                print(f"Ошибка уведомления клиента: {e}")

        else:
            await query.edit_message_text("Ошибка: подходящий заказ не найден.")

    elif action == 'decline':
        await query.edit_message_text("Заказ отклонен.")

        try:
            await context.bot.send_message(
                chat_id=customer_id,
                text="К сожалению, исполнитель не может взять ваш заказ. Мы найдем другого специалиста."
            )
        except Exception as e:
            print(f"Ошибка уведомления клиента: {e}")


async def open_chat(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: str) -> None:
    """Универсальная функция открытия чата"""
    await update.callback_query.edit_message_text(
        f"Чат {chat_id}\n\nЗдесь будут отображаться сообщения..."
    )


async def process_order_acceptance(update: Update, context: ContextTypes.DEFAULT_TYPE, order_name: str,
                                   customer_id: int) -> None:
    """Обработка принятия заказа после ввода названия"""
    firebase = context.bot_data['firebase']
    user_id = update.message.from_user.id
    contractor_login = firebase.get_entrepreneur_by_chat_id(user_id)

    if not contractor_login:
        await update.message.reply_text("Ошибка: необходимо войти в систему.")
        return

    # Создаем заказ с названием
    order_data = {
        'title': order_name,
        'description': context.user_data.get('order_description', 'Описание отсутствует'),
        'customer': {'id': str(customer_id)},
        'executor': {
            'id': str(user_id),
            'username': contractor_login
        },
        'amount': context.user_data.get('order_amount', 0),
        'status': 'in_work',
        'accepted': True,
        'created_date': datetime.now()
    }

    order_id = firebase.create_order(order_data)

    await update.message.reply_text(f"Заказ '{order_name}' принят и создан!")

    # Уведомляем клиента
    try:
        await context.bot.send_message(
            chat_id=customer_id,
            text=f"Исполнитель {contractor_login} принял ваш заказ '{order_name}' и приступает к работе!"
        )
    except Exception as e:
        print(f"Ошибка уведомления клиента: {e}")