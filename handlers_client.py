# handlers_client.py
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from state_manager import user_state
from utils import format_order_info, is_valid_number, parse_number, calculate_end_time, format_time_remaining


async def client_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Меню заказчика - проверяем авторизацию"""
    user_id = update.callback_query.from_user.id
    logged_in_client = user_state.get_client_by_chat_id(user_id)

    if logged_in_client:
        # Авторизованный клиент - показываем кнопки "Создать заказ", "Наши работы" и "Выйти"
        keyboard = [
            [InlineKeyboardButton("Создать заказ", callback_data='create_order')],
            [InlineKeyboardButton("Наши работы", callback_data='our_works')],
            [InlineKeyboardButton("Выйти", callback_data='client_logout')]
        ]
        context.user_data['client_login'] = logged_in_client
        message_text = f'Добро пожаловать, {logged_in_client}!'
    else:
        # Неавторизованный клиент - показываем 4 кнопки
        keyboard = [
            [InlineKeyboardButton("Войти", callback_data='client_login')],
            [InlineKeyboardButton("Зарегистрироваться", callback_data='client_register')],
            [InlineKeyboardButton("Наши работы", callback_data='our_works')],
            [InlineKeyboardButton("Мне нужна консультация", callback_data='consultation')]
        ]
        message_text = 'Выберите действие (Заказчик):'

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(message_text, reply_markup=reply_markup)


async def show_portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показ портфолио услуг"""
    portfolio = "Наши услуги:\n1. Веб-разработка\n2. Дизайн сайтов\n3. SEO-оптимизация"
    await update.callback_query.edit_message_text(portfolio)


async def create_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начало создания заказа (только для авторизованных клиентов)"""
    user_id = update.callback_query.from_user.id
    client_login = user_state.get_client_by_chat_id(user_id)

    if not client_login:
        await update.callback_query.edit_message_text(
            "Для создания заказа необходимо войти в аккаунт."
        )
        return

    await update.callback_query.edit_message_text("Опишите ваш заказ:")
    user_state.set_state(user_id, 'order_description')


async def consultation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Запрос консультации"""
    await update.callback_query.edit_message_text(
        "Запрос на консультацию принят! Специалист скоро с вами свяжется."
    )


async def client_login(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начало процесса входа клиента"""
    await update.callback_query.edit_message_text("Введите ваш логин:")
    user_state.set_state(update.callback_query.from_user.id, 'client_login_username')


async def client_register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начало процесса регистрации клиента"""
    await update.callback_query.edit_message_text("Введите желаемый логин:")
    user_state.set_state(update.callback_query.from_user.id, 'client_register_username')


async def client_logout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Выход из аккаунта клиента"""
    user_id = update.callback_query.from_user.id
    client_login = user_state.get_client_by_chat_id(user_id)

    if client_login:
        user_state.remove_client_chat_id(client_login)

        if 'client_login' in context.user_data:
            del context.user_data['client_login']

        keyboard = [
            [InlineKeyboardButton("Войти", callback_data='client_login')],
            [InlineKeyboardButton("Зарегистрироваться", callback_data='client_register')],
            [InlineKeyboardButton("Мне нужна консультация", callback_data='consultation')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(
            "Вы успешно вышли из аккаунта.\nВыберите действие (Заказчик):",
            reply_markup=reply_markup
        )
    else:
        await update.callback_query.edit_message_text("Ошибка при выходе из аккаунта.")


async def my_client_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показ заказов клиента"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    client_login = user_state.get_client_by_chat_id(user_id)

    if client_login:
        orders = user_state.get_client_orders(client_login)

        if orders:
            await query.edit_message_text(f"Ваши заказы ({len(orders)}):")

            for i, order in enumerate(orders, start=1):
                status = "✅ Принят" if order.get('accepted', False) else "⏳ Ожидает"
                contractor = order.get('contractor_login', 'Не назначен')

                order_text = f"📋 Заказ {i}:\n{order.get('description', 'Описание отсутствует')}"
                order_text += f"\n👨‍💼 Исполнитель: {contractor}"
                order_text += f"\n📊 Статус: {status}"

                if order.get('timer_active', False) and 'timer_end' in order:
                    end_time = datetime.fromisoformat(order['timer_end']) if isinstance(order['timer_end'], str) else \
                        order['timer_end']
                    timer_info = format_time_remaining(end_time)
                    order_text += f"\n{timer_info}"

                await query.message.reply_text(order_text)
        else:
            await query.edit_message_text("У вас пока нет заказов.")
    else:
        await query.edit_message_text("Пожалуйста, войдите в систему.")


async def our_works(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показ категорий наших работ"""
    keyboard = [
        [InlineKeyboardButton("🌐 Сайты", callback_data='category_sites')],
        [InlineKeyboardButton("🎬 Видео", callback_data='category_video')],
        [InlineKeyboardButton("← Назад", callback_data='client')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        "Выберите категорию:",
        reply_markup=reply_markup
    )


async def category_sites(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показ проектов в категории сайтов"""
    portfolio_items = user_state.get_portfolio_items('sites')
    print(f"DEBUG: Загружено сайтов из портфолио: {len(portfolio_items)}")

    for i, item in enumerate(portfolio_items):
        print(
            f"DEBUG: Сайт {i + 1}: title='{item.get('title', 'Без названия')}', description='{item.get('description', 'Без описания')[:50]}...', images={len(item.get('images', []))}, links={len(item.get('links', []))}")

    keyboard = []

    # Добавляем кнопки для каждого проекта
    for i, item in enumerate(portfolio_items):
        button_title = item['title']
        print(f"DEBUG: Создаем кнопку для сайта: {button_title}")
        keyboard.append([InlineKeyboardButton(button_title, callback_data=f'portfolio_item_sites_{i}')])

    # Если нет проектов, показываем стандартные подкатегории
    if not portfolio_items:
        print("DEBUG: Нет сохраненных сайтов, показываем стандартные категории")
        keyboard = [
            [InlineKeyboardButton("📄 Лендинги", callback_data='subcategory_landing')],
            [InlineKeyboardButton("🛒 Интернет магазины", callback_data='subcategory_shop')],
            [InlineKeyboardButton("🎨 Сайты на Тильда", callback_data='subcategory_tilda')],
            [InlineKeyboardButton("⚙️ Сайты на WordPress", callback_data='subcategory_wordpress')]
        ]

    keyboard.append([InlineKeyboardButton("← Назад", callback_data='our_works')])
    reply_markup = InlineKeyboardMarkup(keyboard)

    message_text = "Наши сайты:" if portfolio_items else "Выберите тип сайта:"
    print(f"DEBUG: Отправляем сообщение: {message_text}")
    await update.callback_query.edit_message_text(message_text, reply_markup=reply_markup)


async def category_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показ проектов в категории видео"""
    portfolio_items = user_state.get_portfolio_items('video')

    keyboard = []

    # Добавляем кнопки для каждого проекта
    for i, item in enumerate(portfolio_items):
        keyboard.append([InlineKeyboardButton(item['title'], callback_data=f'portfolio_item_video_{i}')])

    # Если нет проектов, показываем стандартные подкатегории
    if not portfolio_items:
        keyboard = [
            [InlineKeyboardButton("📺 Видео реклама", callback_data='subcategory_ads')],
            [InlineKeyboardButton("🎭 Креативы", callback_data='subcategory_creative')],
            [InlineKeyboardButton("✨ Анимации", callback_data='subcategory_animation')],
            [InlineKeyboardButton("🎬 Моушен графика", callback_data='subcategory_motion')],
            [InlineKeyboardButton("🎮 3D видео", callback_data='subcategory_3d')]
        ]

    keyboard.append([InlineKeyboardButton("← Назад", callback_data='our_works')])
    reply_markup = InlineKeyboardMarkup(keyboard)

    message_text = "Наши видео:" if portfolio_items else "Выберите тип видео:"
    await update.callback_query.edit_message_text(message_text, reply_markup=reply_markup)


async def show_portfolio_item(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str, index: int) -> None:
    """Показ конкретного элемента портфолио - ПОЛНОСТЬЮ ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    portfolio_items = user_state.get_portfolio_items(category)

    if 0 <= index < len(portfolio_items):
        item = portfolio_items[index]

        # ИСПРАВЛЕННАЯ кнопка "Назад" - используем новые callback_data
        back_callback = f'back_to_{category}' if category in ['sites', 'video'] else 'back_to_our_works'

        keyboard = [
            [InlineKeyboardButton("← Назад", callback_data=back_callback)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if item.get('images') and len(item['images']) > 0:
            # Формируем подпись: НАЗВАНИЕ БОЛЬШИМИ БУКВАМИ + описание
            caption = f"🔥 {item['title'].upper()}\n"
            caption += "━━━━━━━━━━━━━━━━━\n\n"
            caption += f"{item['description']}"

            # Добавляем ссылки если есть
            if item.get('links'):
                caption += "\n\n🔗 Ссылки:"
                for link in item['links']:
                    caption += f"\n• {link}"

            try:
                image = item['images'][0]

                # ИСПРАВЛЕНИЕ: Отправляем фото и удаляем исходное сообщение
                await context.bot.send_photo(
                    chat_id=update.callback_query.from_user.id,
                    photo=image,
                    caption=caption,
                    reply_markup=reply_markup
                )

                # Удаляем исходное сообщение со списком
                await update.callback_query.delete_message()

            except Exception as e:
                print(f"Ошибка при отправке изображения: {e}")
                # Если не удалось отправить фото, редактируем сообщение на текст
                text = f"🔥 {item['title'].upper()}\n━━━━━━━━━━━━━━━━━\n\n{item['description']}"
                if item.get('links'):
                    text += "\n\n🔗 Ссылки:"
                    for link in item['links']:
                        text += f"\n• {link}"

                await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
        else:
            # Если нет картинки, показываем только текст
            text = f"🔥 {item['title'].upper()}\n━━━━━━━━━━━━━━━━━\n\n{item['description']}"
            if item.get('links'):
                text += "\n\n🔗 Ссылки:"
                for link in item['links']:
                    text += f"\n• {link}"

            await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text("Проект не найден.")


async def show_subcategory_works(update: Update, context: ContextTypes.DEFAULT_TYPE, subcategory: str) -> None:
    """Показ работ в подкатегории (старая версия для совместимости)"""

    # Определяем название подкатегории
    subcategory_names = {
        'landing': '📄 Лендинги',
        'shop': '🛒 Интернет магазины',
        'tilda': '🎨 Сайты на Тильда',
        'wordpress': '⚙️ Сайты на WordPress',
        'ads': '📺 Видео реклама',
        'creative': '🎭 Креативы',
        'animation': '✨ Анимации',
        'motion': '🎬 Моушен графика',
        '3d': '🎮 3D видео'
    }

    category_name = subcategory_names.get(subcategory, subcategory)

    # Определяем к какой основной категории относится
    sites_subcategories = ['landing', 'shop', 'tilda', 'wordpress']
    back_callback = 'back_to_sites' if subcategory in sites_subcategories else 'back_to_video'

    keyboard = [
        [InlineKeyboardButton("← Назад", callback_data=back_callback)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Здесь можно добавить реальные примеры работ
    works_text = f"{category_name}\n\nПримеры наших работ:\n• Проект 1\n• Проект 2\n• Проект 3"

    await update.callback_query.edit_message_text(
        works_text,
        reply_markup=reply_markup
    )


async def handle_order_creation(update: Update, context: ContextTypes.DEFAULT_TYPE, state: str) -> bool:
    """Обрабатывает создание заказа"""
    user_id = update.message.from_user.id
    client_login = user_state.get_client_by_chat_id(user_id)

    if not client_login:
        await update.message.reply_text("Ошибка: необходимо войти в аккаунт.")
        user_state.set_state(user_id, None)
        return True

    if state == 'order_description':
        context.user_data['order_description'] = update.message.text
        context.user_data['client_login'] = client_login
        await update.message.reply_text("1. Какие у нас есть сроки?")
        user_state.set_state(user_id, 'order_deadline')
        return True

    elif state == 'order_deadline':
        context.user_data['deadline'] = update.message.text
        await update.message.reply_text(
            "2. Какой у вас ориентировочный бюджет? (Введите число, например 15 000)"
        )
        user_state.set_state(user_id, 'order_budget')
        return True

    elif state == 'order_budget':
        if is_valid_number(update.message.text):
            budget = parse_number(update.message.text)
            context.user_data['budget'] = update.message.text
            context.user_data['order_amount'] = budget

            await update.message.reply_text(
                "Спасибо за предоставленную информацию. Мы скоро свяжемся с вами."
            )

            top_entrepreneur = user_state.get_top_entrepreneur()
            if top_entrepreneur:
                top_entrepreneur_data = user_state.entrepreneurs[top_entrepreneur]
                top_entrepreneur_chat_id = top_entrepreneur_data.get('chat_id')

                if top_entrepreneur_chat_id:
                    order_info_text = format_order_info(
                        context.user_data.get('order_description', 'Не указано'),
                        context.user_data.get('deadline', 'Не указано'),
                        context.user_data['budget'],
                        client_login
                    )

                    keyboard = [
                        [InlineKeyboardButton("Принять заказ", callback_data=f'accept_order_{user_id}')],
                        [InlineKeyboardButton("Отказаться", callback_data=f'decline_order_{user_id}')]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)

                    await context.bot.send_message(
                        chat_id=top_entrepreneur_chat_id,
                        text=order_info_text,
                        reply_markup=reply_markup
                    )

                    order_obj = {
                        'description': order_info_text,
                        'client_login': client_login,
                        'client_chat_id': user_id,
                        'budget': budget,
                        'deadline_text': context.user_data.get('deadline', 'Не указано'),
                        'created_at': datetime.now(),
                        'accepted': False,
                        'timer_active': False
                    }

                    user_state.add_order(top_entrepreneur, order_obj)

                    end_time = calculate_end_time(context.user_data.get('deadline', ''))
                    if end_time:
                        orders_list = user_state.get_orders(top_entrepreneur)
                        if orders_list:
                            order_index = len(orders_list) - 1
                            user_state.update_order_timer(top_entrepreneur, order_index, end_time)
                            await update.message.reply_text(
                                f"⏱ Таймер заказа запущен! Срок выполнения: {format_time_remaining(end_time)}"
                            )
                else:
                    await update.message.reply_text(
                        "К сожалению, исполнитель с наивысшим рейтингом сейчас недоступен."
                    )
            else:
                await update.message.reply_text(
                    "К сожалению, в системе нет доступных исполнителей."
                )

            user_state.set_state(user_id, None)
        else:
            await update.message.reply_text(
                "Просим вас написать число. Это поможет нам подобрать лучшее решение для вашей ситуации."
            )
        return True

    return False


async def handle_client_auth(update: Update, context: ContextTypes.DEFAULT_TYPE, state: str) -> bool:
    """Обрабатывает регистрацию и авторизацию клиентов"""
    user_id = update.message.from_user.id
    print(f"DEBUG: handle_client_auth вызван с состоянием: {state}")

    # Регистрация
    if state == 'client_register_username':
        context.user_data['register_client_login'] = update.message.text
        await update.message.reply_text("Введите пароль:")
        user_state.set_state(user_id, 'client_register_password')
        return True

    elif state == 'client_register_password':
        login = context.user_data.get('register_client_login')
        password = update.message.text

        if login:
            if user_state.register_client(login, password, chat_id=user_id):
                keyboard = [
                    [InlineKeyboardButton("Создать заказ", callback_data='create_order')],
                    [InlineKeyboardButton("Наши работы", callback_data='our_works')],
                    [InlineKeyboardButton("Выйти", callback_data='client_logout')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    f"Добро пожаловать, {login}!",
                    reply_markup=reply_markup
                )
                context.user_data['client_login'] = login
            else:
                await update.message.reply_text(
                    "Пользователь с таким логином уже существует. Попробуйте другой логин."
                )
        else:
            await update.message.reply_text("Ошибка при регистрации.")

        user_state.set_state(user_id, None)
        return True

    # Вход
    elif state == 'client_login_username':
        context.user_data['login_client_login'] = update.message.text
        await update.message.reply_text("Введите пароль:")
        user_state.set_state(user_id, 'client_login_password')
        return True

    elif state == 'client_login_password':
        login = context.user_data.get('login_client_login')
        password = update.message.text

        if login and user_state.check_client(login, password):
            user_state.set_client_chat_id(login, user_id)

            keyboard = [
                [InlineKeyboardButton("Создать заказ", callback_data='create_order')],
                [InlineKeyboardButton("Наши работы", callback_data='our_works')],
                [InlineKeyboardButton("Выйти", callback_data='client_logout')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"Добро пожаловать, {login}!",
                reply_markup=reply_markup
            )
            context.user_data['client_login'] = login
        else:
            await update.message.reply_text("Неверный логин или пароль. Попробуйте снова.")

        user_state.set_state(user_id, None)
        return True

    return False


async def handle_order_response(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str,
                                customer_id: int) -> None:
    """Обрабатывает ответ исполнителя на заказ"""
    query = update.callback_query
    contractor_login = user_state.get_entrepreneur_by_chat_id(query.from_user.id)

    if not contractor_login:
        await query.edit_message_text("Ошибка: исполнитель не найден.")
        return

    if action == 'accept':
        order_amount = context.user_data.get('order_amount', 0)
        if order_amount > 0:
            user_state.update_entrepreneur_balance(contractor_login, order_amount)

        orders = user_state.get_orders(contractor_login)
        client_login = None
        chat_id = None

        for i, order in enumerate(orders):
            if isinstance(order, dict) and order.get('client_chat_id') == customer_id and not order.get('accepted',
                                                                                                        False):
                orders[i]['accepted'] = True
                client_login = order.get('client_login')

                # Создаем чат между клиентом и исполнителем
                if client_login:
                    chat_id = user_state.create_chat(
                        client_login,
                        customer_id,
                        contractor_login,
                        query.from_user.id,
                        f"order_{i}"
                    )

                deadline_text = order.get('deadline_text', '')
                end_time = calculate_end_time(deadline_text)

                if end_time:
                    user_state.update_order_timer(contractor_login, i, end_time)
                    timer_info = format_time_remaining(end_time)

                    # Кнопка "Чат с клиентом" для исполнителя
                    if chat_id:
                        keyboard = [
                            [InlineKeyboardButton("💬 Чат с клиентом", callback_data=f'open_chat_{chat_id}')]
                        ]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        await query.edit_message_text(
                            f"✅ Вы приняли заказ!\n{timer_info}",
                            reply_markup=reply_markup
                        )
                    else:
                        await query.edit_message_text(f"✅ Вы приняли заказ!\n{timer_info}")

                    # Сообщение клиенту с кнопкой чата
                    if chat_id:
                        client_keyboard = [
                            [InlineKeyboardButton("💬 Чат с исполнителем", callback_data=f'open_chat_{chat_id}')]
                        ]
                        client_reply_markup = InlineKeyboardMarkup(client_keyboard)
                        await context.bot.send_message(
                            chat_id=customer_id,
                            text=f"✅ Исполнитель принял ваш заказ!\n{timer_info}",
                            reply_markup=client_reply_markup
                        )
                    else:
                        await context.bot.send_message(
                            chat_id=customer_id,
                            text=f"✅ Исполнитель принял ваш заказ!\n{timer_info}"
                        )
                else:
                    # Без таймера
                    if chat_id:
                        keyboard = [
                            [InlineKeyboardButton("💬 Чат с клиентом", callback_data=f'open_chat_{chat_id}')]
                        ]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        await query.edit_message_text("✅ Вы приняли заказ!", reply_markup=reply_markup)

                        client_keyboard = [
                            [InlineKeyboardButton("💬 Чат с исполнителем", callback_data=f'open_chat_{chat_id}')]
                        ]
                        client_reply_markup = InlineKeyboardMarkup(client_keyboard)
                        await context.bot.send_message(
                            chat_id=customer_id,
                            text="✅ Исполнитель принял ваш заказ!",
                            reply_markup=client_reply_markup
                        )
                    else:
                        await query.edit_message_text("✅ Вы приняли заказ!")
                        await context.bot.send_message(
                            chat_id=customer_id,
                            text="✅ Исполнитель принял ваш заказ!"
                        )

                user_state.save_data()
                break

    elif action == 'decline':
        await query.edit_message_text("❌ Вы отказались от заказа!")
        await context.bot.send_message(
            chat_id=customer_id,
            text="❌ Исполнитель отказался от вашего заказа!"
        )


async def open_chat(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: str) -> None:
    """Открывает чат между клиентом и исполнителем"""
    query = update.callback_query
    user_chat_id = query.from_user.id

    chat_info = user_state.get_chat_info(chat_id)
    if not chat_info or not chat_info.get('active', False):
        await query.edit_message_text("Чат не найден или неактивен.")
        return

    # Определяем роль пользователя
    if chat_info.get('client_chat_id') == user_chat_id:
        partner_name = chat_info.get('contractor_login', 'Исполнитель')
        await query.edit_message_text(f"💬 Открыт чат с исполнителем {partner_name}\n\nНапишите сообщение:")
    elif chat_info.get('contractor_chat_id') == user_chat_id:
        partner_name = chat_info.get('client_login', 'Клиент')
        await query.edit_message_text(f"💬 Открыт чат с клиентом {partner_name}\n\nНапишите сообщение:")
    else:
        await query.edit_message_text("Ошибка: вы не участник этого чата.")
        return

    # Устанавливаем состояние чата
    user_state.set_state(user_chat_id, f'in_chat_{chat_id}')


async def handle_chat_messages(update: Update, context: ContextTypes.DEFAULT_TYPE, state: str) -> bool:
    """Обрабатывает сообщения в чате"""
    if not state.startswith('in_chat_'):
        return False

    chat_id = state.replace('in_chat_', '')
    user_chat_id = update.message.from_user.id
    message_text = update.message.text

    # Получаем информацию о чате
    chat_info = user_state.get_chat_info(chat_id)
    if not chat_info or not chat_info.get('active', False):
        await update.message.reply_text("Чат неактивен.")
        user_state.set_state(user_chat_id, None)
        return True

    # Определяем получателя
    partner_chat_id = user_state.get_chat_partner(chat_id, user_chat_id)
    if not partner_chat_id:
        await update.message.reply_text("Партнер по чату не найден.")
        return True

    # Определяем роль отправителя
    from utils import get_user_role_in_chat, format_chat_message
    sender_role = get_user_role_in_chat(user_chat_id, chat_info)

    # Форматируем и отправляем сообщение
    formatted_message = format_chat_message(sender_role, message_text)

    try:
        await context.bot.send_message(chat_id=partner_chat_id, text=formatted_message)
        await update.message.reply_text("✅ Сообщение доставлено")
    except Exception as e:
        await update.message.reply_text("❌ Ошибка при отправке сообщения")
        print(f"Ошибка отправки сообщения: {e}")

    return True