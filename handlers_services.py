# handlers_services.py - обработчики раздела "Наши услуги"
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes


async def our_services_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Главное меню раздела 'Наши услуги'"""
    services_text = """🎯 НАШИ УСЛУГИ

Мы предлагаем полный спектр digital-решений для вашего бизнеса:

• Видеопродакшн — создаём контент, который продаёт
• Разработка сайтов — строим ваше присутствие в интернете

Выберите интересующее направление:"""

    keyboard = [
        [InlineKeyboardButton("🎬 Видеопродакшн", callback_data='service_video')],
        [InlineKeyboardButton("🌐 Разработка сайтов", callback_data='service_websites')],
        [InlineKeyboardButton("◀️ Назад", callback_data='client')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(services_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(services_text, reply_markup=reply_markup)


async def video_production_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Меню видеопродакшена"""
    video_text = """🎬 ВИДЕОПРОДАКШН

Видео — это самый быстрый способ донести идею до клиента и выделиться среди конкурентов. Мы создаём контент, который повышает конверсию и делает бренд узнаваемым.

Наши направления:"""

    keyboard = [
        [InlineKeyboardButton("📺 Рекламные ролики", callback_data='video_ads')],
        [InlineKeyboardButton("📱 Креативы для соцсетей", callback_data='video_social')],
        [InlineKeyboardButton("🎨 Анимация и моушен-графика", callback_data='video_animation')],
        [InlineKeyboardButton("🎯 3D-видео", callback_data='video_3d')],
        [InlineKeyboardButton("◀️ Назад к услугам", callback_data='our_services')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(video_text, reply_markup=reply_markup)


async def website_development_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Меню разработки сайтов"""
    websites_text = """🌐 РАЗРАБОТКА САЙТОВ

Сайт — это главный инструмент онлайн-продаж. Мы делаем сайты, которые работают на бизнес: привлекают клиентов, повышают конверсию и укрепляют доверие.

Наши решения:"""

    keyboard = [
        [InlineKeyboardButton("📄 Лендинги", callback_data='web_landing')],
        [InlineKeyboardButton("🛒 Интернет-магазины", callback_data='web_shop')],
        [InlineKeyboardButton("🏢 Многостраничные сайты", callback_data='web_multipage')],
        [InlineKeyboardButton("⚡ Сайты на Tilda и WordPress", callback_data='web_platforms')],
        [InlineKeyboardButton("◀️ Назад к услугам", callback_data='our_services')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(websites_text, reply_markup=reply_markup)


# ВИДЕОПРОДАКШН - ДЕТАЛЬНЫЕ СТРАНИЦЫ

async def video_ads_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Рекламные ролики - детали"""
    ads_text = """📺 РЕКЛАМНЫЕ РОЛИКИ

Продающие видео для YouTube, TikTok, Instagram и ТВ.

👉 Полезно: повышают конверсию в заявки и покупки, помогают привлечь новых клиентов и закрепиться в памяти аудитории.

✨ Что входит:
• Разработка сценария и концепции
• Профессиональная съёмка
• Монтаж и цветокоррекция
• Звуковое оформление
• Адаптация под разные платформы

💰 Стоимость: от 50 000 руб.
⏰ Сроки: 7-14 дней"""

    keyboard = [
        [InlineKeyboardButton("📞 Обсудить проект", callback_data='create_order')],
        [InlineKeyboardButton("◀️ К видеопродакшну", callback_data='service_video')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(ads_text, reply_markup=reply_markup)


async def video_social_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Креативы для соцсетей - детали"""
    social_text = """📱 КРЕАТИВЫ ДЛЯ СОЦСЕТЕЙ

Короткие, цепляющие видео для рекламы и сторис.

👉 Полезно: увеличивают кликабельность (CTR), снижают стоимость лида и обеспечивают быстрый поток клиентов.

✨ Что входит:
• Креативные концепции
• Съёмка в трендовых форматах
• Быстрый монтаж
• Адаптация под соцсети
• Тестирование гипотез

💰 Стоимость: от 15 000 руб.
⏰ Сроки: 3-7 дней"""

    keyboard = [
        [InlineKeyboardButton("📞 Обсудить проект", callback_data='create_order')],
        [InlineKeyboardButton("◀️ К видеопродакшну", callback_data='service_video')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(social_text, reply_markup=reply_markup)


async def video_animation_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Анимация и моушен-графика - детали"""
    animation_text = """🎨 АНИМАЦИЯ И МОУШЕН-ГРАФИКА

Яркие ролики, которые упрощают подачу сложных идей.

👉 Полезно: удерживают внимание зрителя и формируют современный образ компании.

✨ Что входит:
• 2D и 3D анимация
• Моушен-дизайн
• Инфографика
• Персонажная анимация
• Логотипы и заставки

💰 Стоимость: от 30 000 руб.
⏰ Сроки: 10-21 день"""

    keyboard = [
        [InlineKeyboardButton("📞 Обсудить проект", callback_data='create_order')],
        [InlineKeyboardButton("◀️ К видеопродакшну", callback_data='service_video')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(animation_text, reply_markup=reply_markup)


async def video_3d_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """3D-видео - детали"""
    video_3d_text = """🎯 3D-ВИДЕО

Реалистичная визуализация товаров и проектов.

👉 Полезно: впечатляет аудиторию, формирует доверие к бренду и помогает выделиться на рынке.

✨ Что входит:
• 3D-моделирование
• Фотореалистичная визуализация
• Анимация объектов
• Спецэффекты
• Презентационные ролики

💰 Стоимость: от 80 000 руб.
⏰ Сроки: 14-30 дней"""

    keyboard = [
        [InlineKeyboardButton("📞 Обсудить проект", callback_data='create_order')],
        [InlineKeyboardButton("◀️ К видеопродакшну", callback_data='service_video')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(video_3d_text, reply_markup=reply_markup)


# РАЗРАБОТКА САЙТОВ - ДЕТАЛЬНЫЕ СТРАНИЦЫ

async def web_landing_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Лендинги - детали"""
    landing_text = """📄 ЛЕНДИНГИ

Одностраничные сайты под один оффер или услугу.

👉 Полезно: повышают конверсию рекламы, мотивируют посетителя оставить заявку или совершить покупку.

✨ Что входит:
• Уникальный дизайн
• Адаптивная вёрстка
• Формы обратной связи
• Интеграция с CRM
• Настройка аналитики

💰 Стоимость: от 25 000 руб.
⏰ Сроки: 5-10 дней"""

    keyboard = [
        [InlineKeyboardButton("📞 Обсудить проект", callback_data='create_order')],
        [InlineKeyboardButton("◀️ К разработке сайтов", callback_data='service_websites')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(landing_text, reply_markup=reply_markup)


async def web_shop_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Интернет-магазины - детали"""
    shop_text = """🛒 ИНТЕРНЕТ-МАГАЗИНЫ

Полноценные онлайн-продажи с каталогом, корзиной и оплатой.

👉 Полезно: расширяют клиентскую базу и позволяют зарабатывать 24/7 без ограничений.

✨ Что входит:
• Каталог товаров
• Корзина и оформление заказов
• Система оплаты
• Личный кабинет пользователя
• Админ-панель для управления

💰 Стоимость: от 80 000 руб.
⏰ Сроки: 21-45 дней"""

    keyboard = [
        [InlineKeyboardButton("📞 Обсудить проект", callback_data='create_order')],
        [InlineKeyboardButton("◀️ К разработке сайтов", callback_data='service_websites')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(shop_text, reply_markup=reply_markup)


async def web_multipage_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Многостраничные сайты - детали"""
    multipage_text = """🏢 МНОГОСТРАНИЧНЫЕ САЙТЫ

Подробное представление компании, услуг и портфолио.

👉 Полезно: формируют доверие и имидж, помогают увеличить узнаваемость бренда и привлекать клиентов из поисковых систем.

✨ Что входит:
• Корпоративный дизайн
• Структура до 20 страниц
• SEO-оптимизация
• Блог/новости
• Интеграция с соцсетями

💰 Стоимость: от 60 000 руб.
⏰ Сроки: 14-30 дней"""

    keyboard = [
        [InlineKeyboardButton("📞 Обсудить проект", callback_data='create_order')],
        [InlineKeyboardButton("◀️ К разработке сайтов", callback_data='service_websites')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(multipage_text, reply_markup=reply_markup)


async def web_platforms_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Сайты на платформах - детали"""
    platforms_text = """⚡ САЙТЫ НА TILDA И WORDPRESS

Быстрые решения на популярных платформах.

👉 Полезно: легко обновлять самому, быстро запускать новые страницы и тестировать гипотезы без программиста.

✨ Что входит:
• Настройка платформы
• Адаптивный дизайн
• Базовая SEO-настройка
• Обучение управлению
• Техподдержка 30 дней

💰 Стоимость: от 20 000 руб.
⏰ Сроки: 3-7 дней"""

    keyboard = [
        [InlineKeyboardButton("📞 Обсудить проект", callback_data='create_order')],
        [InlineKeyboardButton("◀️ К разработке сайтов", callback_data='service_websites')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(platforms_text, reply_markup=reply_markup)