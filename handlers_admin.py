# handlers_admin.py - полная админ-панель с управлением исполнителями и портфолио
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime


async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Главное меню админ-панели"""
    firebase = context.bot_data['firebase']

    admin_text = """🔧 АДМИН-ПАНЕЛЬ

Выберите раздел для управления:"""

    keyboard = [
        [InlineKeyboardButton("👥 Исполнители", callback_data='admin_executors')],
        [InlineKeyboardButton("🎨 Портфолио", callback_data='admin_portfolio')],
        [InlineKeyboardButton("📊 Статистика", callback_data='admin_stats')],
        [InlineKeyboardButton("🔙 Выход", callback_data='admin_exit')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(admin_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(admin_text, reply_markup=reply_markup)


async def admin_executors_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Меню управления исполнителями"""
    firebase = context.bot_data['firebase']

    executors_text = """👥 УПРАВЛЕНИЕ ИСПОЛНИТЕЛЯМИ

Выберите действие:"""

    keyboard = [
        [InlineKeyboardButton("📋 Все исполнители", callback_data='admin_view_executors')],
        [InlineKeyboardButton("➕ Добавить исполнителя", callback_data='admin_add_executor')],
        [InlineKeyboardButton("❌ Удалить исполнителя", callback_data='admin_delete_executor')],
        [InlineKeyboardButton("🔙 Назад в админ-панель", callback_data='admin_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(executors_text, reply_markup=reply_markup)


async def view_all_executors(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Просмотр всех исполнителей"""
    firebase = context.bot_data['firebase']

    try:
        executors = firebase.get_all_executors()

        if not executors:
            text = "📋 ИСПОЛНИТЕЛИ\n\nИсполнители не найдены."
        else:
            text = f"📋 ИСПОЛНИТЕЛИ ({len(executors)})\n\n"

            for i, executor in enumerate(executors, 1):
                username = executor.get('username', 'Неизвестно')
                balance = executor.get('balance', 0)
                rating = executor.get('rating', 10)
                completed_orders = executor.get('completed_orders', 0)
                status = executor.get('status', 'active')

                text += f"{i}. {username}\n"
                text += f"   💰 Баланс: {balance} руб.\n"
                text += f"   ⭐ Рейтинг: {rating}\n"
                text += f"   ✅ Заказов: {completed_orders}\n"
                text += f"   🔘 Статус: {status}\n\n"

    except Exception as e:
        text = f"❌ Ошибка при загрузке исполнителей: {str(e)}"
        print(f"Ошибка получения исполнителей: {e}")

    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data='admin_view_executors')],
        [InlineKeyboardButton("🔙 Назад", callback_data='admin_executors')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)


async def add_executor_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начало добавления исполнителя"""
    firebase = context.bot_data['firebase']
    user_id = update.callback_query.from_user.id

    await update.callback_query.edit_message_text(
        "➕ ДОБАВИТЬ ИСПОЛНИТЕЛЯ\n\nВведите логин для нового исполнителя:"
    )
    firebase.set_user_state(user_id, 'admin_add_executor_login')


async def delete_executor_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начало удаления исполнителя"""
    firebase = context.bot_data['firebase']

    try:
        executors = firebase.get_all_executors()

        if not executors:
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='admin_executors')]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.callback_query.edit_message_text(
                "❌ УДАЛИТЬ ИСПОЛНИТЕЛЯ\n\nИсполнители не найдены.",
                reply_markup=reply_markup
            )
            return

        text = "❌ УДАЛИТЬ ИСПОЛНИТЕЛЯ\n\nВыберите исполнителя для удаления:"
        keyboard = []

        for executor in executors:
            username = executor.get('username', 'Неизвестно')
            keyboard.append([
                InlineKeyboardButton(
                    f"❌ {username}",
                    callback_data=f'admin_delete_confirm_{username}'
                )
            ])

        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='admin_executors')])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

    except Exception as e:
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='admin_executors')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            f"❌ Ошибка при загрузке списка исполнителей: {str(e)}",
            reply_markup=reply_markup
        )


async def confirm_delete_executor(update: Update, context: ContextTypes.DEFAULT_TYPE, username: str) -> None:
    """Подтверждение удаления исполнителя"""
    text = f"⚠️ ПОДТВЕРЖДЕНИЕ УДАЛЕНИЯ\n\nВы действительно хотите удалить исполнителя '{username}'?\n\nЭто действие нельзя отменить!"

    keyboard = [
        [
            InlineKeyboardButton("✅ Да, удалить", callback_data=f'admin_delete_execute_{username}'),
            InlineKeyboardButton("❌ Отмена", callback_data='admin_delete_executor')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)


async def execute_delete_executor(update: Update, context: ContextTypes.DEFAULT_TYPE, username: str) -> None:
    """Выполнение удаления исполнителя"""
    firebase = context.bot_data['firebase']

    try:
        success = firebase.delete_executor(username)

        if success:
            text = f"✅ Исполнитель '{username}' успешно удален!"
        else:
            text = f"❌ Не удалось найти исполнителя '{username}' для удаления."

    except Exception as e:
        text = f"❌ Ошибка при удалении исполнителя: {str(e)}"
        print(f"Ошибка удаления исполнителя: {e}")

    keyboard = [
        [InlineKeyboardButton("🔙 К управлению исполнителями", callback_data='admin_executors')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)


async def admin_portfolio_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Меню управления портфолио"""
    firebase = context.bot_data['firebase']

    try:
        # Получаем статистику портфолио
        portfolio_count = firebase.get_portfolio_count()

        portfolio_text = f"""🎨 УПРАВЛЕНИЕ ПОРТФОЛИО

Всего элементов: {portfolio_count}

Выберите действие:"""

        keyboard = [
            [InlineKeyboardButton("📋 Просмотр портфолио", callback_data='admin_view_portfolio')],
            [InlineKeyboardButton("➕ Добавить в портфолио", callback_data='admin_add_portfolio')],
            [InlineKeyboardButton("❌ Удалить из портфолио", callback_data='admin_delete_portfolio')],
            [InlineKeyboardButton("🔙 Назад в админ-панель", callback_data='admin_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(portfolio_text, reply_markup=reply_markup)

    except Exception as e:
        text = f"❌ Ошибка при загрузке меню портфолио: {str(e)}"
        print(f"Ошибка загрузки меню портфолио: {e}")

        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='admin_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)


async def view_portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Просмотр портфолио"""
    firebase = context.bot_data['firebase']

    try:
        portfolio_items = firebase.get_portfolio()

        if not portfolio_items:
            text = "🎨 ПОРТФОЛИО\n\nПортфолио пусто."
        else:
            text = f"🎨 ПОРТФОЛИО ({len(portfolio_items)})\n\n"

            for i, item in enumerate(portfolio_items, 1):
                title = item.get('title', 'Без названия')
                category = item.get('category', 'Без категории')
                description = item.get('description', 'Без описания')

                text += f"{i}. {title}\n"
                text += f"   📂 Категория: {category}\n"
                text += f"   📝 {description[:50]}{'...' if len(description) > 50 else ''}\n\n"

    except Exception as e:
        text = f"❌ Ошибка при загрузке портфолио: {str(e)}"
        print(f"Ошибка загрузки портфолио: {e}")

    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data='admin_view_portfolio')],
        [InlineKeyboardButton("🔙 Назад", callback_data='admin_portfolio')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)


async def add_portfolio_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начало добавления элемента в портфолио"""
    firebase = context.bot_data['firebase']
    user_id = update.callback_query.from_user.id

    text = """➕ ДОБАВИТЬ В ПОРТФОЛИО

Выберите категорию:"""

    keyboard = [
        [InlineKeyboardButton("🌐 Сайты", callback_data='admin_portfolio_category_sites')],
        [InlineKeyboardButton("🎬 Видео", callback_data='admin_portfolio_category_video')],
        [InlineKeyboardButton("🔙 Назад", callback_data='admin_portfolio')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)


async def portfolio_category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str) -> None:
    """Обработка выбора категории для портфолио"""
    firebase = context.bot_data['firebase']
    user_id = update.callback_query.from_user.id

    context.user_data['portfolio_category'] = category

    category_names = {
        'sites': 'Сайты',
        'video': 'Видео'
    }

    category_display = category_names.get(category, category)

    await update.callback_query.edit_message_text(
        f"➕ ДОБАВИТЬ В ПОРТФОЛИО\n\nКатегория: {category_display}\n\nВведите название проекта:"
    )

    firebase.set_user_state(user_id, f'admin_portfolio_title_{category}')


async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Статистика системы"""
    firebase = context.bot_data['firebase']

    try:
        stats = firebase.get_admin_stats()

        text = f"""📊 СТАТИСТИКА СИСТЕМЫ

👥 Пользователи:
   • Клиентов: {stats.get('clients_count', 0)}
   • Исполнителей: {stats.get('executors_count', 0)}
   • Всего пользователей: {stats.get('total_users', 0)}

📋 Заказы:
   • Всего заказов: {stats.get('orders_count', 0)}
   • В работе: {stats.get('active_orders', 0)}
   • Завершенных: {stats.get('completed_orders', 0)}

🎨 Портфолио:
   • Элементов: {stats.get('portfolio_count', 0)}

💰 Финансы:
   • Общий баланс исполнителей: {stats.get('total_balance', 0)} руб."""

    except Exception as e:
        text = f"❌ Ошибка при загрузке статистики: {str(e)}"
        print(f"Ошибка загрузки статистики: {e}")

    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data='admin_stats')],
        [InlineKeyboardButton("🔙 Назад", callback_data='admin_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)


async def admin_exit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Выход из админ-панели"""
    await update.callback_query.edit_message_text(
        "👋 Вы вышли из админ-панели.\n\nДля повторного входа напишите 'админ'."
    )