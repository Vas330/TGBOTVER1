# button_handler.py - обновленная версия с новыми кнопками для чата и сдачи заказов
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from handlers_client import (client_menu, show_portfolio, create_order, consultation, handle_order_response,
                             client_login, client_register, client_logout, my_client_orders, open_chat,
                             our_works, category_sites, category_video, show_subcategory_works, show_portfolio_item,
                             show_client_order_details, open_client_chat, accept_work, request_revision)
from handlers_contractor import (entrepreneur_menu, login_entrepreneur, logout_entrepreneur, my_orders,
                                 show_contractor_order_details, open_contractor_chat, submit_work)
from handlers_services import (
    our_services_menu,
    video_production_menu,
    website_development_menu,
    video_ads_details,
    video_social_details,
    video_animation_details,
    video_3d_details,
    web_landing_details,
    web_shop_details,
    web_multipage_details,
    web_platforms_details
)
from payment_handlers import (
    handle_payment_confirmation,
    handle_start_work,
    handle_payment_help,
    handle_back_to_payment,
    handle_decline_paid_order
)
from datetime import datetime


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Основной обработчик кнопок с Firebase"""
    firebase = context.bot_data['firebase']
    query = update.callback_query
    await query.answer()

    data = query.data
    print(f"DEBUG: Получен callback_data: {data}")

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
        await category_sites(update, context)
    elif data == 'category_video':
        await category_video(update, context)

    # НОВЫЕ ОБРАБОТЧИКИ ДЛЯ УСЛУГ
    elif data == 'our_services':
        await our_services_menu(update, context)

    # Главные разделы услуг
    elif data == 'service_video':
        await video_production_menu(update, context)
    elif data == 'service_websites':
        await website_development_menu(update, context)

    # Видеопродакшн - детали
    elif data == 'video_ads':
        await video_ads_details(update, context)
    elif data == 'video_social':
        await video_social_details(update, context)
    elif data == 'video_animation':
        await video_animation_details(update, context)
    elif data == 'video_3d':
        await video_3d_details(update, context)

    # Разработка сайтов - детали
    elif data == 'web_landing':
        await web_landing_details(update, context)
    elif data == 'web_shop':
        await web_shop_details(update, context)
    elif data == 'web_multipage':
        await web_multipage_details(update, context)
    elif data == 'web_platforms':
        await web_platforms_details(update, context)

    # ОБРАБОТЧИКИ ПЛАТЕЖЕЙ
    elif data.startswith('payment_confirm_'):
        order_id = data.replace('payment_confirm_', '')
        await handle_payment_confirmation(update, context, order_id)

    elif data.startswith('start_work_'):
        order_id = data.replace('start_work_', '')
        await handle_start_work(update, context, order_id)

    elif data.startswith('payment_help_'):
        order_id = data.replace('payment_help_', '')
        await handle_payment_help(update, context, order_id)

    elif data.startswith('back_to_payment_'):
        order_id = data.replace('back_to_payment_', '')
        await handle_back_to_payment(update, context, order_id)

    elif data.startswith('decline_paid_order_'):
        order_id = data.replace('decline_paid_order_', '')
        await handle_decline_paid_order(update, context, order_id)

    # ОБРАБОТЧИКИ ЧАТА ДЛЯ КЛИЕНТОВ
    elif data.startswith('open_client_chat_'):
        order_id = data.replace('open_client_chat_', '')
        await open_client_chat(update, context, order_id)

    elif data.startswith('client_order_'):
        order_id = data.replace('client_order_', '')
        await show_client_order_details(update, context, order_id)

    # ОБРАБОТЧИКИ ЧАТА ДЛЯ ИСПОЛНИТЕЛЕЙ
    elif data.startswith('open_contractor_chat_'):
        order_id = data.replace('open_contractor_chat_', '')
        await open_contractor_chat(update, context, order_id)

    elif data.startswith('contractor_order_'):
        order_id = data.replace('contractor_order_', '')
        await show_contractor_order_details(update, context, order_id)

    # НОВЫЕ ОБРАБОТЧИКИ ДЛЯ СДАЧИ И ПРИЕМКИ ЗАКАЗОВ
    elif data.startswith('submit_work_'):
        order_id = data.replace('submit_work_', '')
        await submit_work(update, context, order_id)

    elif data.startswith('accept_work_'):
        order_id = data.replace('accept_work_', '')
        await accept_work(update, context, order_id)

    elif data.startswith('request_revision_'):
        order_id = data.replace('request_revision_', '')
        await request_revision(update, context, order_id)

    # СТАРЫЕ ОБРАБОТЧИКИ ДЛЯ СОВМЕСТИМОСТИ
    elif data.startswith('submit_order_'):
        parts = data.split('_')
        contractor_login = parts[2]
        order_id = parts[3]
        await handle_order_submission(update, context, contractor_login, order_id)

    elif data.startswith('accept_submitted_'):
        completion_id = data.replace('accept_submitted_', '')
        await handle_client_order_decision(update, context, 'accept', completion_id)

    elif data.startswith('reject_submitted_'):
        completion_id = data.replace('reject_submitted_', '')
        await handle_client_order_decision(update, context, 'reject', completion_id)

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
    elif data == 'personal_cabinet':
        from handlers_contractor import personal_cabinet
        await personal_cabinet(update, context)

    # ОБРАБОТЧИКИ ЛИЧНОГО КАБИНЕТА
    elif data.startswith('withdraw_money_'):
        contractor_login = data.replace('withdraw_money_', '')
        from handlers_contractor import withdraw_money
        await withdraw_money(update, context, contractor_login)

    elif data.startswith('withdraw_amount_'):
        parts = data.split('_')
        contractor_login = parts[2]
        amount = float(parts[3])
        from handlers_contractor import process_withdrawal
        await process_withdrawal(update, context, contractor_login, amount)

    elif data.startswith('withdraw_custom_'):
        contractor_login = data.replace('withdraw_custom_', '')
        from handlers_contractor import withdraw_custom_amount
        await withdraw_custom_amount(update, context, contractor_login)

    elif data == 'withdraw_unavailable':
        await query.edit_message_text("Недостаточно средств для вывода.\nПополните баланс, выполнив заказы.")

    elif data == 'order_details':
        from handlers_contractor import order_details
        await order_details(update, context)

    # Обработка административных кнопок
    elif data == 'register_entrepreneur':
        await register_entrepreneur_start(update, context)
    elif data == 'all_entrepreneurs':
        await all_entrepreneurs(update, context)
    elif data == 'portfolio_menu':
        await admin_portfolio_menu(update, context)

    # Обработка ответов на заказы
    elif data.startswith('accept_order_'):
        customer_id = int(data.split('_')[2])
        await handle_order_response(update, context, 'accept', customer_id)
    elif data.startswith('decline_order_'):
        customer_id = int(data.split('_')[2])
        await handle_order_response(update, context, 'decline', customer_id)

    # Обработка чатов
    elif data.startswith('open_chat_'):
        chat_id = '_'.join(data.split('_')[2:])
        await open_chat(update, context, chat_id)

    else:
        print(f"DEBUG: Неизвестный callback_data: {data}")
        await query.edit_message_text(f"Неизвестная команда: {data}")


async def handle_order_submission(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                  contractor_login: str, order_id: str) -> None:
    """Обрабатывает сдачу заказа исполнителем (старый обработчик)"""
    firebase = context.bot_data['firebase']
    query = update.callback_query

    # Обновляем заказ в Firebase
    firebase.update_order(order_id, {
        'submitted_for_review': True,
        'submission_time': datetime.now()
    })

    await query.edit_message_text(f"Заказ отправлен клиенту на проверку!\nОжидайте решения клиента.")

    # Уведомляем клиента через Firebase
    # Здесь можно добавить логику уведомления клиента


async def handle_client_order_decision(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                       action: str, completion_id: str) -> None:
    """Обрабатывает решение клиента по заказу (старый обработчик)"""
    firebase = context.bot_data['firebase']
    query = update.callback_query

    if action == 'accept':
        await query.edit_message_text("Заказ принят! Спасибо за работу с нами!")
    elif action == 'reject':
        await query.edit_message_text("Заказ отправлен на доработку.")


# Заглушки для админских функций
async def register_entrepreneur_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    firebase = context.bot_data['firebase']
    await update.callback_query.edit_message_text("Введите логин исполнителя:")
    firebase.set_user_state(update.callback_query.from_user.id, 'register_login')


async def all_entrepreneurs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.edit_message_text("Функция в разработке...")


async def admin_portfolio_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.edit_message_text("Функция в разработке...")