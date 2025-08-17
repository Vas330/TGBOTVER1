# handlers_admin.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from state_manager import user_state
from utils import format_entrepreneur_info, format_entrepreneur_list_item, is_valid_rating


async def all_entrepreneurs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает всех исполнителей"""
    entrepreneurs = user_state.entrepreneurs
    count = user_state.get_entrepreneurs_count()
    keyboard = []

    for login in entrepreneurs:
        entrepreneur_data = entrepreneurs[login]
        balance = entrepreneur_data.get('balance', 0)
        rating = entrepreneur_data['rating']
        keyboard.append([
            InlineKeyboardButton(
                format_entrepreneur_list_item(login, rating, balance),
                callback_data=f'entrepreneur_{login}'
            )
        ])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        f"Всего исполнителей: {count}\nУзнать подробнее:",
        reply_markup=reply_markup
    )


async def admin_portfolio_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Меню управления портфолио"""
    keyboard = [
        [InlineKeyboardButton("➕ Добавить сайт", callback_data='add_portfolio_sites')],
        [InlineKeyboardButton("➕ Добавить видео", callback_data='add_portfolio_video')],
        [InlineKeyboardButton("📋 Просмотреть портфолио", callback_data='view_portfolio')],
        [InlineKeyboardButton("🗑 Удалить элемент", callback_data='delete_portfolio_start')],
        [InlineKeyboardButton("← Назад в админ панель", callback_data='admin_back')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        "Управление портфолио:",
        reply_markup=reply_markup
    )


async def delete_portfolio_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начало процесса удаления - выбор категории"""
    keyboard = [
        [InlineKeyboardButton("🌐 Сайты", callback_data='delete_category_sites')],
        [InlineKeyboardButton("🎬 Видео", callback_data='delete_category_video')],
        [InlineKeyboardButton("← Назад", callback_data='portfolio_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        "Выберите категорию для удаления:",
        reply_markup=reply_markup
    )


async def delete_category_items(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str) -> None:
    """Показ элементов категории для удаления"""
    portfolio_items = user_state.get_portfolio_items(category)
    category_names = {'sites': 'сайтов', 'video': 'видео'}
    category_name = category_names.get(category, category)

    if not portfolio_items:
        keyboard = [
            [InlineKeyboardButton("← Назад", callback_data='delete_portfolio_start')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(
            f"В категории {category_name} нет элементов для удаления.",
            reply_markup=reply_markup
        )
        return

    keyboard = []
    for i, item in enumerate(portfolio_items):
        # Ограничиваем длину названия для кнопки
        title = item['title']
        if len(title) > 30:
            title = title[:27] + "..."

        keyboard.append([InlineKeyboardButton(
            f"🗑 {title}",
            callback_data=f'delete_item_{category}_{i}'
        )])

    keyboard.append([InlineKeyboardButton("← Назад", callback_data='delete_portfolio_start')])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        f"Выберите {category_name[:-2]} для удаления ({len(portfolio_items)} элементов):",
        reply_markup=reply_markup
    )


async def delete_item_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str, index: int) -> None:
    """Подтверждение удаления элемента"""
    portfolio_items = user_state.get_portfolio_items(category)

    if 0 <= index < len(portfolio_items):
        item = portfolio_items[index]

        # Сохраняем данные для текстового подтверждения
        context.user_data['delete_category'] = category
        context.user_data['delete_index'] = index
        context.user_data['delete_title'] = item['title']

        await update.callback_query.edit_message_text(
            f"❗ Вы точно хотите удалить:\n\n"
            f"📋 '{item['title']}'\n"
            f"📝 {item['description'][:100]}{'...' if len(item['description']) > 100 else ''}\n\n"
            f"⚠️ Это действие нельзя отменить!\n\n"
            f"Напишите 'да' для подтверждения или 'нет' для отмены."
        )

        # Устанавливаем состояние ожидания подтверждения
        user_state.set_state(update.callback_query.from_user.id, f'delete_confirm_{category}_{index}')
    else:
        await update.callback_query.edit_message_text("Элемент не найден.")


async def handle_delete_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE, state: str) -> bool:
    """Обрабатывает текстовое подтверждение удаления"""
    if not state.startswith('delete_confirm_'):
        return False

    user_id = update.message.from_user.id
    response = update.message.text.lower().strip()

    # Извлекаем данные из контекста
    category = context.user_data.get('delete_category')
    index = context.user_data.get('delete_index')
    title = context.user_data.get('delete_title', 'Неизвестный элемент')

    if response == 'да':
        # Удаляем элемент
        if user_state.delete_portfolio_item(category, index):
            await update.message.reply_text(f"✅ Элемент '{title}' успешно удален!")

            # Отправляем обновленный список категории
            await send_updated_category_list(update, context, category)
        else:
            await update.message.reply_text("❌ Ошибка при удалении элемента.")

    elif response == 'нет':
        await update.message.reply_text("❌ Удаление отменено.")

        # Возвращаемся к списку элементов категории
        await send_updated_category_list(update, context, category)
    else:
        await update.message.reply_text("❓ Пожалуйста, напишите 'да' или 'нет'.")
        return True  # Не сбрасываем состояние, ждем корректный ответ

    # Очищаем данные и состояние
    context.user_data.pop('delete_category', None)
    context.user_data.pop('delete_index', None)
    context.user_data.pop('delete_title', None)
    user_state.set_state(user_id, None)

    return True


async def send_updated_category_list(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str) -> None:
    """Отправляет обновленный список элементов категории"""
    portfolio_items = user_state.get_portfolio_items(category)
    category_names = {'sites': 'сайтов', 'video': 'видео'}
    category_name = category_names.get(category, category)

    if not portfolio_items:
        keyboard = [
            [InlineKeyboardButton("← Назад", callback_data='delete_portfolio_start')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"В категории {category_name} больше нет элементов.",
            reply_markup=reply_markup
        )
        return

    keyboard = []
    for i, item in enumerate(portfolio_items):
        title = item['title']
        if len(title) > 30:
            title = title[:27] + "..."

        keyboard.append([InlineKeyboardButton(
            f"🗑 {title}",
            callback_data=f'delete_item_{category}_{i}'
        )])

    keyboard.append([InlineKeyboardButton("← Назад", callback_data='delete_portfolio_start')])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Выберите {category_name[:-2]} для удаления ({len(portfolio_items)} элементов):",
        reply_markup=reply_markup
    )


async def add_portfolio_start(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str) -> None:
    """Начало добавления элемента портфолио"""
    category_names = {'sites': 'сайт', 'video': 'видео'}
    category_name = category_names.get(category, category)

    await update.callback_query.edit_message_text(f"Введите название {category_name}:")
    # ИСПРАВЛЕНО: используем единый формат состояний
    user_state.set_state(update.callback_query.from_user.id, f'add_{category}_title')


async def view_portfolio_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Просмотр портфолио для админа"""
    keyboard = [
        [InlineKeyboardButton("🌐 Сайты", callback_data='admin_view_sites')],
        [InlineKeyboardButton("🎬 Видео", callback_data='admin_view_video')],
        [InlineKeyboardButton("← Назад", callback_data='portfolio_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        "Выберите категорию для просмотра:",
        reply_markup=reply_markup
    )


async def view_category_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str) -> None:
    """Просмотр категории портфолио для админа"""
    portfolio_items = user_state.get_portfolio_items(category)

    if not portfolio_items:
        keyboard = [
            [InlineKeyboardButton("← Назад", callback_data='view_portfolio')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(
            f"В категории '{category}' пока нет элементов.",
            reply_markup=reply_markup
        )
        return

    keyboard = []
    for i, item in enumerate(portfolio_items):
        keyboard.append([InlineKeyboardButton(
            f"📋 {item['title']}",
            callback_data=f'admin_item_{category}_{i}'
        )])

    keyboard.append([InlineKeyboardButton("← Назад", callback_data='view_portfolio')])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        f"Элементы в категории '{category}' ({len(portfolio_items)}):",
        reply_markup=reply_markup
    )


async def show_portfolio_item_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str,
                                    index: int) -> None:
    """Показ элемента портфолио для админа"""
    portfolio_items = user_state.get_portfolio_items(category)

    if 0 <= index < len(portfolio_items):
        item = portfolio_items[index]

        text = f"🎯 {item['title']}\n\n{item['description']}"

        if item.get('links'):
            text += "\n\n🔗 Ссылки:"
            for link in item['links']:
                text += f"\n• {link}"

        if item.get('images'):
            text += f"\n\n📸 Изображений: {len(item['images'])}"

        keyboard = [
            [InlineKeyboardButton("🗑 Удалить", callback_data=f'delete_confirm_{category}_{index}')],
            [InlineKeyboardButton("← Назад", callback_data=f'admin_view_{category}')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text("Элемент не найден.")


async def delete_portfolio_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str,
                                   index: int) -> None:
    """Подтверждение удаления элемента портфолио"""
    portfolio_items = user_state.get_portfolio_items(category)

    if 0 <= index < len(portfolio_items):
        item = portfolio_items[index]
        keyboard = [
            [InlineKeyboardButton("✅ Да, удалить", callback_data=f'delete_execute_{category}_{index}')],
            [InlineKeyboardButton("❌ Отмена", callback_data=f'admin_item_{category}_{index}')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            f"Вы уверены, что хотите удалить '{item['title']}'?",
            reply_markup=reply_markup
        )
    else:
        await update.callback_query.edit_message_text("Элемент не найден.")


async def execute_portfolio_delete(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str,
                                   index: int) -> None:
    """Выполнение удаления элемента портфолио"""
    if user_state.delete_portfolio_item(category, int(index)):
        await update.callback_query.edit_message_text("Элемент успешно удален!")
        # Возвращаемся к списку категории
        import asyncio
        await asyncio.sleep(1)
        await view_category_admin(update, context, category)
    else:
        await update.callback_query.edit_message_text("Ошибка при удалении элемента.")


async def handle_portfolio_addition(update: Update, context: ContextTypes.DEFAULT_TYPE, state: str) -> bool:
    """УДАЛЕНА - теперь обработка в text_handler.py через handle_old_portfolio_format"""
    # Эта функция больше не используется
    return False


# Остальные функции остаются без изменений...

async def entrepreneur_details(update: Update, context: ContextTypes.DEFAULT_TYPE, login: str) -> None:
    """Показывает детали исполнителя"""
    query = update.callback_query

    if login in user_state.entrepreneurs:
        entrepreneur_data = user_state.entrepreneurs[login]
        password = entrepreneur_data['password']
        rating = entrepreneur_data['rating']
        balance = entrepreneur_data.get('balance', 0)
        chat_id = entrepreneur_data.get('chat_id')

        keyboard = [
            [InlineKeyboardButton("Поменять рейтинг", callback_data=f'change_rating_{login}')],
            [InlineKeyboardButton("Изменить баланс", callback_data=f'change_balance_{login}')],
            [InlineKeyboardButton("Удалить исполнителя", callback_data=f'delete_entrepreneur_{login}')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        info_text = format_entrepreneur_info(login, password, rating, balance, chat_id)
        await query.edit_message_text(info_text, reply_markup=reply_markup)
    else:
        await query.edit_message_text("Исполнитель не найден.")


async def change_rating(update: Update, context: ContextTypes.DEFAULT_TYPE, login: str) -> None:
    """Запрос на изменение рейтинга"""
    query = update.callback_query
    await query.edit_message_text("Введите новый рейтинг (от 1 до 10):")
    user_state.set_state(query.from_user.id, f'new_rating_{login}')


async def change_balance(update: Update, context: ContextTypes.DEFAULT_TYPE, login: str) -> None:
    """Запрос на изменение баланса"""
    query = update.callback_query
    await query.edit_message_text("Введите новый баланс:")
    user_state.set_state(query.from_user.id, f'new_balance_{login}')


async def delete_entrepreneur_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE, login: str) -> None:
    """Подтверждение удаления исполнителя"""
    query = update.callback_query
    await query.edit_message_text(
        f"Вы точно хотите удалить исполнителя {login}? Напишите 'да' или 'нет'."
    )
    user_state.set_state(query.from_user.id, f'delete_confirm_{login}')


async def handle_registration_process(update: Update, context: ContextTypes.DEFAULT_TYPE, state: str) -> bool:
    """
    Обрабатывает процесс регистрации исполнителя.
    Возвращает True, если сообщение было обработано этим хендлером.
    """
    user_id = update.message.from_user.id

    if state == 'register_login':
        context.user_data['register_login'] = update.message.text
        await update.message.reply_text("Введите пароль:")
        user_state.set_state(user_id, 'register_password')
        return True

    elif state == 'register_password':
        login = context.user_data.get('register_login')
        password = update.message.text

        if login:
            user_state.register_entrepreneur(login, password, chat_id=user_id)
            await update.message.reply_text("Данные сохранены в системе!")
        else:
            await update.message.reply_text("Ошибка при регистрации.")

        user_state.set_state(user_id, None)
        return True

    return False


async def handle_admin_updates(update: Update, context: ContextTypes.DEFAULT_TYPE, state: str) -> bool:
    """
    Обрабатывает административные обновления (рейтинг, баланс, удаление).
    Возвращает True, если сообщение было обработано этим хендлером.
    """
    user_id = update.message.from_user.id

    # Обработка подтверждения удаления портфолио
    if await handle_delete_confirmation(update, context, state):
        return True

    # Обработка изменения рейтинга
    if state.startswith('new_rating_'):
        login = state.split('_')[2]
        try:
            rating = int(update.message.text)
            if is_valid_rating(rating):
                if user_state.update_entrepreneur_rating(login, rating):
                    await update.message.reply_text("Рейтинг обновлен!")
                else:
                    await update.message.reply_text("Исполнитель не найден.")
            else:
                await update.message.reply_text("Рейтинг должен быть от 1 до 10.")
        except ValueError:
            await update.message.reply_text("Введите число.")
        user_state.set_state(user_id, None)
        return True

    # Обработка изменения баланса
    elif state.startswith('new_balance_'):
        login = state.split('_')[2]
        try:
            balance = float(update.message.text.replace(' ', ''))
            if user_state.set_entrepreneur_balance(login, balance):
                await update.message.reply_text("Баланс обновлен!")
            else:
                await update.message.reply_text("Исполнитель не найден.")
        except ValueError:
            await update.message.reply_text("Введите корректную сумму.")
        user_state.set_state(user_id, None)
        return True

    # Обработка подтверждения удаления
    elif state.startswith('delete_confirm_'):
        login = state.split('_')[2]
        response = update.message.text.lower().strip()

        if response == 'да':
            if user_state.delete_entrepreneur(login):
                await update.message.reply_text(f"Исполнитель {login} удален.")
            else:
                await update.message.reply_text("Исполнитель не найден.")
            user_state.set_state(user_id, None)
        elif response == 'нет':
            # Возвращаемся к деталям исполнителя
            if login in user_state.entrepreneurs:
                entrepreneur_data = user_state.entrepreneurs[login]
                password = entrepreneur_data['password']
                rating = entrepreneur_data['rating']
                balance = entrepreneur_data.get('balance', 0)
                chat_id = entrepreneur_data.get('chat_id')

                keyboard = [
                    [InlineKeyboardButton("Поменять рейтинг", callback_data=f'change_rating_{login}')],
                    [InlineKeyboardButton("Изменить баланс", callback_data=f'change_balance_{login}')],
                    [InlineKeyboardButton("Удалить исполнителя", callback_data=f'delete_entrepreneur_{login}')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                info_text = format_entrepreneur_info(login, password, rating, balance, chat_id)
                await update.message.reply_text(info_text, reply_markup=reply_markup)
            else:
                await update.message.reply_text("Исполнитель не найден.")
            user_state.set_state(user_id, None)
        else:
            await update.message.reply_text("Пожалуйста, введите 'да' или 'нет'.")
        return True

    return False


async def register_entrepreneur_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начало регистрации исполнителя"""
    query = update.callback_query
    await query.edit_message_text("Введите логин исполнителя:")
    user_state.set_state(query.from_user.id, 'register_login')