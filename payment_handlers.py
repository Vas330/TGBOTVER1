# payment_handlers.py - обновленная версия с правильными уведомлениями о начале работы
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime

from yoomoney_manager import YooMoneyManager
from config import YOOMONEY_SHOP_ID, YOOMONEY_SECRET_KEY


async def send_payment_request(update: Update, context: ContextTypes.DEFAULT_TYPE, order_id: str) -> None:
    """Отправляет запрос на оплату заказа с QR-кодом"""
    firebase = context.bot_data['firebase']

    # Получаем заказ
    order = firebase.get_order_by_id(order_id)
    if not order:
        return

    # Получаем chat_id клиента
    customer_username = order.get('customer', {}).get('username')
    if not customer_username:
        return

    customer_chat_id = firebase.get_user_chat_id_by_username(customer_username)
    if not customer_chat_id:
        print(f"Не найден chat_id для клиента {customer_username}")
        return

    # Создаем менеджер YooMoney
    yoomoney = YooMoneyManager(YOOMONEY_SHOP_ID, YOOMONEY_SECRET_KEY)

    # Генерируем данные платежа
    payment_data = yoomoney.generate_payment_data(
        order_id=order_id,
        amount=order.get('amount', 0),
        description=f"Оплата заказа: {order.get('title', 'Без названия')}"
    )

    # Сохраняем платеж в Firebase
    payment_data['user_id'] = customer_chat_id
    payment_data['order_id'] = order_id
    firebase.create_payment(payment_data)

    # Генерируем QR-код
    qr_image = yoomoney.generate_qr_code(payment_data)

    # Создаем сообщение
    payment_message = yoomoney.create_payment_message(payment_data, order.get('title', 'Без названия'))

    # Кнопки
    keyboard = [
        [InlineKeyboardButton("✅ Я оплатил", callback_data=f'payment_confirm_{order_id}')],
        [InlineKeyboardButton("❓ Помощь с оплатой", callback_data=f'payment_help_{order_id}')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        # Отправляем QR-код и сообщение
        await context.bot.send_photo(
            chat_id=customer_chat_id,
            photo=qr_image,
            caption=payment_message,
            reply_markup=reply_markup
        )

        print(f"QR-код для оплаты отправлен клиенту {customer_username}")

        # Обновляем статус заказа
        firebase.update_order(order_id, {
            'payment_required': True,
            'payment_sent_at': datetime.now(),
            'status': 'waiting_payment'
        })

    except Exception as e:
        print(f"Ошибка отправки QR-кода: {e}")


async def handle_payment_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE, order_id: str) -> None:
    """Обрабатывает подтверждение оплаты от клиента"""
    firebase = context.bot_data['firebase']
    query = update.callback_query
    user_id = query.from_user.id

    # Проверяем заказ
    order = firebase.get_order_by_id(order_id)
    if not order:
        await query.answer("Заказ не найден")
        return

    # Проверяем что это клиент заказа
    customer_username = order.get('customer', {}).get('username')
    client_login = firebase.get_client_by_chat_id(user_id)

    if customer_username != client_login:
        await query.answer("У вас нет доступа к этому заказу")
        return

    # Получаем платеж
    payment = firebase.get_payment_by_order(order_id)
    if not payment:
        await query.answer("Платеж не найден")
        return

    # Обновляем статус платежа как "подтвержден клиентом"
    firebase.update_payment_status(payment['id'], 'client_confirmed', datetime.now())

    # Обновляем заказ
    firebase.update_order(order_id, {
        'status': 'payment_confirmed',
        'client_payment_confirmed_at': datetime.now()
    })

    # Уведомляем клиента
    await query.edit_message_caption(
        caption="✅ ОПЛАТА ПОДТВЕРЖДЕНА\n\n"
                "Спасибо! Мы получили подтверждение оплаты.\n"
                "Ожидаем подтверждения исполнителем и начала работы над проектом.\n\n"
                "Вы получите уведомление, когда исполнитель приступит к работе."
    )

    # Уведомляем исполнителя
    executor_username = order.get('executor', {}).get('username')
    if executor_username:
        executor_chat_id = firebase.get_user_chat_id_by_username(executor_username)
        if executor_chat_id:
            keyboard = [
                [InlineKeyboardButton("🚀 Взять в работу", callback_data=f'start_work_{order_id}')],
                [InlineKeyboardButton("❌ Отказаться", callback_data=f'decline_paid_order_{order_id}')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            try:
                await context.bot.send_message(
                    chat_id=executor_chat_id,
                    text=f"💰 ЗАКАЗ ОПЛАЧЕН КЛИЕНТОМ!\n\n"
                         f"📋 Заказ: {order.get('title', 'Без названия')}\n"
                         f"💰 Сумма: {order.get('amount', 0)} руб.\n"
                         f"👤 Клиент: {customer_username}\n\n"
                         f"Клиент подтвердил оплату заказа.\n"
                         f"Готовы приступить к работе?",
                    reply_markup=reply_markup
                )
                print(f"Уведомление об оплате отправлено исполнителю {executor_username}")
            except Exception as e:
                print(f"Ошибка уведомления исполнителя: {e}")


async def handle_start_work(update: Update, context: ContextTypes.DEFAULT_TYPE, order_id: str) -> None:
    """Обрабатывает начало работы исполнителем с уведомлениями обеим сторонам"""
    firebase = context.bot_data['firebase']
    query = update.callback_query
    user_id = query.from_user.id

    # Проверяем заказ
    order = firebase.get_order_by_id(order_id)
    if not order:
        await query.answer("Заказ не найден")
        return

    # Проверяем что это исполнитель заказа
    executor_username = order.get('executor', {}).get('username')
    contractor_login = firebase.get_entrepreneur_by_chat_id(user_id)

    if executor_username != contractor_login:
        await query.answer("У вас нет доступа к этому заказу")
        return

    # Обновляем заказ - начинаем работу
    firebase.update_order(order_id, {
        'status': 'in_work',
        'work_started_at': datetime.now(),
        'accepted': True
    })

    # Создаем кнопку чата для исполнителя
    executor_keyboard = [
        [InlineKeyboardButton("💬 Открыть чат с клиентом", callback_data=f'open_contractor_chat_{order_id}')],
        [InlineKeyboardButton("🎯 Сдать заказ на проверку", callback_data=f'submit_work_{order_id}')]
    ]
    executor_reply_markup = InlineKeyboardMarkup(executor_keyboard)

    # Уведомляем исполнителя
    await query.edit_message_text(
        "🚀 РАБОТА НАД ПРОЕКТОМ НАЧАЛАСЬ!\n\n"
        f"Заказ: {order.get('title', 'Без названия')}\n"
        f"Статус: В работе\n\n"
        "Вы можете общаться с клиентом через чат заказа.\n"
        "Удачи в работе!",
        reply_markup=executor_reply_markup
    )

    # Уведомляем клиента
    customer_username = order.get('customer', {}).get('username')
    if customer_username:
        customer_chat_id = firebase.get_user_chat_id_by_username(customer_username)
        if customer_chat_id:
            # Создаем кнопку чата для клиента
            client_keyboard = [
                [InlineKeyboardButton("💬 Открыть чат с исполнителем", callback_data=f'open_client_chat_{order_id}')]
            ]
            client_reply_markup = InlineKeyboardMarkup(client_keyboard)

            try:
                await context.bot.send_message(
                    chat_id=customer_chat_id,
                    text=f"🚀 РАБОТА НАД ПРОЕКТОМ НАЧАЛАСЬ!\n\n"
                         f"Заказ: {order.get('title', 'Без названия')}\n"
                         f"Статус: В работе\n\n"
                         f"Исполнитель {executor_username} приступил к работе!\n\n"
                         f"Вы можете общаться через чат заказа.\n"
                         f"Удачи в работе!",
                    reply_markup=client_reply_markup
                )
                print(f"Уведомление о начале работы отправлено клиенту {customer_username}")
            except Exception as e:
                print(f"Ошибка уведомления клиента: {e}")


async def handle_payment_help(update: Update, context: ContextTypes.DEFAULT_TYPE, order_id: str) -> None:
    """Помощь с оплатой"""
    query = update.callback_query

    help_text = """❓ ПОМОЩЬ С ОПЛАТОЙ

📱 Как оплатить через QR-код:
1. Откройте приложение YooMoney на телефоне
2. Нажмите "Сканировать QR" 
3. Наведите камеру на QR-код
4. Подтвердите платеж

💳 Другие способы оплаты:
• Банковской картой через YooMoney
• Через интернет-банк
• В приложении банка по QR-коду

❗ Важно:
После оплаты обязательно нажмите "Я оплатил" в сообщении с QR-кодом.

📞 Нужна помощь?
Обратитесь к нашему менеджеру: @YourManagerUsername"""

    keyboard = [
        [InlineKeyboardButton("◀️ Назад к оплате", callback_data=f'back_to_payment_{order_id}')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_caption(
        caption=help_text,
        reply_markup=reply_markup
    )


async def handle_back_to_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, order_id: str) -> None:
    """Возвращает к сообщению с оплатой"""
    firebase = context.bot_data['firebase']

    # Получаем заказ и платеж
    order = firebase.get_order_by_id(order_id)
    payment = firebase.get_payment_by_order(order_id)

    if not order or not payment:
        await update.callback_query.answer("Ошибка получения данных")
        return

    # Создаем менеджер YooMoney
    yoomoney = YooMoneyManager(YOOMONEY_SHOP_ID, YOOMONEY_SECRET_KEY)

    # Восстанавливаем сообщение об оплате
    payment_message = yoomoney.create_payment_message(payment, order.get('title', 'Без названия'))

    keyboard = [
        [InlineKeyboardButton("✅ Я оплатил", callback_data=f'payment_confirm_{order_id}')],
        [InlineKeyboardButton("❓ Помощь с оплатой", callback_data=f'payment_help_{order_id}')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_caption(
        caption=payment_message,
        reply_markup=reply_markup
    )


async def handle_decline_paid_order(update: Update, context: ContextTypes.DEFAULT_TYPE, order_id: str) -> None:
    """Обрабатывает отказ исполнителя от оплаченного заказа"""
    firebase = context.bot_data['firebase']
    query = update.callback_query
    user_id = query.from_user.id

    # Получаем заказ
    order = firebase.get_order_by_id(order_id)
    if not order:
        await query.answer("Заказ не найден")
        return

    # Проверяем что это исполнитель заказа
    executor_username = order.get('executor', {}).get('username')
    contractor_login = firebase.get_entrepreneur_by_chat_id(user_id)

    if executor_username != contractor_login:
        await query.answer("У вас нет доступа к этому заказу")
        return

    # Обновляем заказ
    firebase.update_order(order_id, {
        'status': 'executor_declined_paid',
        'executor_declined_at': datetime.now()
    })

    # Уведомляем исполнителя
    await query.edit_message_text(
        "❌ ВЫ ОТКАЗАЛИСЬ ОТ ЗАКАЗА\n\n"
        "Заказ был отклонен.\n"
        "Мы найдем другого исполнителя для клиента.\n"
        "Средства будут возвращены клиенту."
    )

    # Уведомляем клиента
    customer_username = order.get('customer', {}).get('username')
    if customer_username:
        customer_chat_id = firebase.get_user_chat_id_by_username(customer_username)
        if customer_chat_id:
            try:
                await context.bot.send_message(
                    chat_id=customer_chat_id,
                    text=f"😔 К сожалению, исполнитель {executor_username} не может взять ваш заказ в работу.\n\n"
                         f"📋 Заказ: {order.get('title', 'Без названия')}\n"
                         f"💰 Сумма: {order.get('amount', 0)} руб.\n\n"
                         f"Мы найдем вам другого квалифицированного исполнителя.\n"
                         f"Средства будут возвращены на вашу карту в течение 3-5 рабочих дней.\n\n"
                         f"Извините за неудобства!"
                )
                print(f"Уведомление об отказе отправлено клиенту {customer_username}")
            except Exception as e:
                print(f"Ошибка уведомления клиента: {e}")


async def handle_paid_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает текстовое сообщение 'оплатил' от клиента"""
    firebase = context.bot_data['firebase']
    user_id = update.message.from_user.id

    # Получаем ожидающие платежи пользователя
    pending_payments = firebase.get_pending_payments_by_user(user_id)

    if not pending_payments:
        await update.message.reply_text(
            "У вас нет ожидающих платежей.\n"
            "Если вы оплатили заказ, используйте кнопку 'Я оплатил' в сообщении с QR-кодом."
        )
        return

    # Если есть только один ожидающий платеж
    if len(pending_payments) == 1:
        payment = pending_payments[0]
        order_id = payment['order_id']

        # Обновляем статус платежа
        firebase.update_payment_status(payment['id'], 'client_confirmed', datetime.now())

        # Обновляем заказ
        firebase.update_order(order_id, {
            'status': 'payment_confirmed',
            'client_payment_confirmed_at': datetime.now()
        })

        order = firebase.get_order_by_id(order_id)

        await update.message.reply_text(
            "✅ ОПЛАТА ПОДТВЕРЖДЕНА\n\n"
            "Спасибо! Мы получили подтверждение оплаты.\n"
            "Ожидаем подтверждения исполнителем и начала работы над проектом.\n\n"
            "Вы получите уведомление, когда исполнитель приступит к работе."
        )

        # Уведомляем исполнителя
        executor_username = order.get('executor', {}).get('username')
        if executor_username:
            executor_chat_id = firebase.get_user_chat_id_by_username(executor_username)
            if executor_chat_id:
                keyboard = [
                    [InlineKeyboardButton("🚀 Взять в работу", callback_data=f'start_work_{order_id}')],
                    [InlineKeyboardButton("❌ Отказаться", callback_data=f'decline_paid_order_{order_id}')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                try:
                    await context.bot.send_message(
                        chat_id=executor_chat_id,
                        text=f"💰 ЗАКАЗ ОПЛАЧЕН КЛИЕНТОМ!\n\n"
                             f"📋 Заказ: {order.get('title', 'Без названия')}\n"
                             f"💰 Сумма: {order.get('amount', 0)} руб.\n"
                             f"👤 Клиент: {order.get('customer', {}).get('username')}\n\n"
                             f"Клиент подтвердил оплату заказа.\n"
                             f"Готовы приступить к работе?",
                        reply_markup=reply_markup
                    )
                except Exception as e:
                    print(f"Ошибка уведомления исполнителя: {e}")

    else:
        # Если несколько ожидающих платежей, показываем список
        keyboard = []
        for payment in pending_payments:
            order = firebase.get_order_by_id(payment['order_id'])
            order_title = order.get('title', 'Без названия') if order else 'Заказ не найден'
            keyboard.append([
                InlineKeyboardButton(
                    f"{order_title} - {payment['amount']:.0f} руб.",
                    callback_data=f"payment_confirm_{payment['order_id']}"
                )
            ])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "У вас несколько ожидающих платежей.\n"
            "Выберите заказ, который вы оплатили:",
            reply_markup=reply_markup
        )