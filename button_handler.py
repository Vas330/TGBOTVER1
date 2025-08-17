# button_handler.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from handlers_client import (client_menu, show_portfolio, create_order, consultation, handle_order_response,
                             client_login, client_register, client_logout, my_client_orders, open_chat,
                             our_works, category_sites, category_video, show_subcategory_works, show_portfolio_item)
from handlers_contractor import entrepreneur_menu, login_entrepreneur, logout_entrepreneur, my_orders
from handlers_admin import (all_entrepreneurs, entrepreneur_details, change_rating, change_balance,
                            delete_entrepreneur_confirm, register_entrepreneur_start,
                            admin_portfolio_menu, add_portfolio_start, view_portfolio_admin, view_category_admin,
                            show_portfolio_item_admin, delete_portfolio_confirm, execute_portfolio_delete)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Основной обработчик кнопок"""
    query = update.callback_query
    await query.answer()

    data = query.data
    print(f"🔥 DEBUG: Получен callback_data: {data}")

    # Обработка основных ролей
    if data == 'client':
        await client_menu(update, context)
    elif data == 'entrepreneur':
        await entrepreneur_menu(update, context)

    # Обработка кнопок заказчика
    elif data == 'portfolio':
        await show_portfolio(update, context)
    elif data == 'create_order':
        await create_order(update, context)
    elif data == 'consultation':
        await consultation(update, context)
    elif data == 'client_login':
        await client_login(update, context)
    elif data == 'client_register':
        await client_register(update, context)
    elif data == 'client_logout':
        await client_logout(update, context)
    elif data == 'my_client_orders':
        await my_client_orders(update, context)
    elif data == 'our_works':
        await our_works(update, context)
    elif data == 'category_sites':
        print(f"🔥 DEBUG: Переходим к category_sites")
        await category_sites(update, context)
    elif data == 'category_video':
        print(f"🔥 DEBUG: Переходим к category_video")
        await category_video(update, context)

    # ИСПРАВЛЕННАЯ обработка кнопок "Назад" из портфолио
    elif data == 'back_to_sites':
        print(f"🔥 DEBUG: Возврат к сайтам")
        try:
            # Удаляем текущее сообщение (если можем)
            await query.delete_message()
        except:
            pass

        # Отправляем новое сообщение со списком сайтов
        await send_category_sites_message(update, context)

    elif data == 'back_to_video':
        print(f"🔥 DEBUG: Возврат к видео")
        try:
            await query.delete_message()
        except:
            pass
        await send_category_video_message(update, context)

    elif data == 'back_to_our_works':
        print(f"🔥 DEBUG: Возврат к нашим работам")
        try:
            await query.delete_message()
        except:
            pass
        await send_our_works_message(update, context)

    # Обработка элементов портфолио
    elif data.startswith('portfolio_item_'):
        parts = data.split('_')
        category = parts[2]
        index = int(parts[3])
        await show_portfolio_item(update, context, category, index)

    # Обработка подкатегорий работ
    elif data.startswith('subcategory_'):
        subcategory = data.replace('subcategory_', '')
        await show_subcategory_works(update, context, subcategory)

    # Обработка кнопок исполнителя
    elif data == 'login':
        await login_entrepreneur(update, context)
    elif data == 'logout':
        await logout_entrepreneur(update, context)
    elif data == 'my_orders':
        await my_orders(update, context)

    # Обработка административных кнопок
    elif data == 'register_entrepreneur':
        await register_entrepreneur_start(update, context)
    elif data == 'all_entrepreneurs':
        await all_entrepreneurs(update, context)
    elif data == 'portfolio_menu':
        await admin_portfolio_menu(update, context)
    elif data == 'add_portfolio_sites':
        await add_portfolio_start(update, context, 'sites')
    elif data == 'add_portfolio_video':
        await add_portfolio_start(update, context, 'video')
    elif data == 'view_portfolio':
        await view_portfolio_admin(update, context)
    elif data == 'admin_view_sites':
        await view_category_admin(update, context, 'sites')
    elif data == 'admin_view_video':
        await view_category_admin(update, context, 'video')

    # НОВЫЕ ОБРАБОТЧИКИ ДЛЯ УДАЛЕНИЯ ПОРТФОЛИО
    elif data == 'delete_portfolio_start':
        from handlers_admin import delete_portfolio_start
        await delete_portfolio_start(update, context)
    elif data == 'delete_category_sites':
        from handlers_admin import delete_category_items
        await delete_category_items(update, context, 'sites')
    elif data == 'delete_category_video':
        from handlers_admin import delete_category_items
        await delete_category_items(update, context, 'video')
    elif data.startswith('delete_item_'):
        parts = data.split('_')
        category = parts[2]
        index = int(parts[3])
        from handlers_admin import delete_item_confirm
        await delete_item_confirm(update, context, category, index)

    elif data == 'admin_back':
        # Возврат в главное админ меню
        keyboard = [
            [InlineKeyboardButton("Зарегистрировать исполнителя", callback_data='register_entrepreneur')],
            [InlineKeyboardButton("Все исполнители", callback_data='all_entrepreneurs')],
            [InlineKeyboardButton("Управление портфолио", callback_data='portfolio_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text("Добро пожаловать, Администратор!", reply_markup=reply_markup)
    elif data == 'admin_back':
        # Возврат в главное админ меню
        keyboard = [
            [InlineKeyboardButton("Зарегистрировать исполнителя", callback_data='register_entrepreneur')],
            [InlineKeyboardButton("Все исполнители", callback_data='all_entrepreneurs')],
            [InlineKeyboardButton("Управление портфолио", callback_data='portfolio_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text("Добро пожаловать, Администратор!", reply_markup=reply_markup)

    # Обработка элементов портфолио в админке
    elif data.startswith('admin_item_'):
        parts = data.split('_')
        category = parts[2]
        index = int(parts[3])
        await show_portfolio_item_admin(update, context, category, index)
    elif data.startswith('delete_confirm_'):
        parts = data.split('_')
        category = parts[2]
        index = int(parts[3])
        await delete_portfolio_confirm(update, context, category, index)
    elif data.startswith('delete_execute_'):
        parts = data.split('_')
        category = parts[2]
        index = int(parts[3])
        await execute_portfolio_delete(update, context, category, index)

    # Обработка динамических кнопок
    elif data.startswith('entrepreneur_'):
        login = data.split('_')[1]
        await entrepreneur_details(update, context, login)
    elif data.startswith('change_rating_'):
        login = data.split('_')[2]
        await change_rating(update, context, login)
    elif data.startswith('change_balance_'):
        login = data.split('_')[2]
        await change_balance(update, context, login)
    elif data.startswith('delete_entrepreneur_'):
        login = data.split('_')[2]
        await delete_entrepreneur_confirm(update, context, login)

    # Обработка ответов на заказы
    elif data.startswith('accept_order_'):
        customer_id = int(data.split('_')[2])
        await handle_order_response(update, context, 'accept', customer_id)
    elif data.startswith('decline_order_'):
        customer_id = int(data.split('_')[2])
        await handle_order_response(update, context, 'decline', customer_id)

    # Обработка чатов
    elif data.startswith('open_chat_'):
        chat_id = '_'.join(data.split('_')[2:])  # Собираем chat_id обратно
        await open_chat(update, context, chat_id)

    else:
        print(f"❌ DEBUG: Неизвестный callback_data: {data}")
        await query.edit_message_text(f"Неизвестная команда: {data}")


async def send_category_sites_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет новое сообщение со списком сайтов"""
    from state_manager import user_state

    portfolio_items = user_state.get_portfolio_items('sites')
    keyboard = []

    # Добавляем кнопки для каждого проекта
    for i, item in enumerate(portfolio_items):
        keyboard.append([InlineKeyboardButton(item['title'], callback_data=f'portfolio_item_sites_{i}')])

    # Если нет проектов, показываем стандартные подкатегории
    if not portfolio_items:
        keyboard = [
            [InlineKeyboardButton("📄 Лендинги", callback_data='subcategory_landing')],
            [InlineKeyboardButton("🛒 Интернет магазины", callback_data='subcategory_shop')],
            [InlineKeyboardButton("🎨 Сайты на Тильда", callback_data='subcategory_tilda')],
            [InlineKeyboardButton("⚙️ Сайты на WordPress", callback_data='subcategory_wordpress')]
        ]

    keyboard.append([InlineKeyboardButton("← Назад", callback_data='our_works')])
    reply_markup = InlineKeyboardMarkup(keyboard)

    message_text = "Наши сайты:" if portfolio_items else "Выберите тип сайта:"

    await context.bot.send_message(
        chat_id=update.callback_query.from_user.id,
        text=message_text,
        reply_markup=reply_markup
    )


async def send_category_video_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет новое сообщение со списком видео"""
    from state_manager import user_state

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

    await context.bot.send_message(
        chat_id=update.callback_query.from_user.id,
        text=message_text,
        reply_markup=reply_markup
    )


async def send_our_works_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет новое сообщение с категориями работ"""
    keyboard = [
        [InlineKeyboardButton("🌐 Сайты", callback_data='category_sites')],
        [InlineKeyboardButton("🎬 Видео", callback_data='category_video')],
        [InlineKeyboardButton("← Назад", callback_data='client')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=update.callback_query.from_user.id,
        text="Выберите категорию:",
        reply_markup=reply_markup
    )