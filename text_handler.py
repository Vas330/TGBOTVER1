# text_handler.py - исправленная версия с автоматической поддержкой telegram_id
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime

from handlers_common import handle_admin_command
from payment_handlers import handle_paid_text_message


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений с Firebase и новой структурой сообщений"""
    firebase = context.bot_data['firebase']
    user_id = update.message.from_user.id
    text = update.message.text.strip() if update.message.text else ""
    state = firebase.get_user_state(user_id)

    print(f"DEBUG: User={user_id}, Text='{text}', State='{state}'")

    # Обработка команды админ
    if text.lower() == "админ":
        await handle_admin_command(update, context)
        return

    # Обработка слова "оплатил"
    if text.lower() == "оплатил":
        await handle_paid_text_message(update, context)
        return

    # ОБРАБОТКА СОСТОЯНИЙ
    if state:
        print(f"Обрабатываем состояние: {state}")

        try:
            # ОБРАБОТКА ВВОДА НАЗВАНИЯ ЗАКАЗА
            if state == 'order_name_input':
                order_name = text.strip()
                if not order_name:
                    await update.message.reply_text("Название заказа не может быть пустым. Введите название:")
                    return

                customer_id = context.user_data.get('pending_order_customer_id')
                if customer_id:
                    from handlers_client import process_order_acceptance
                    await process_order_acceptance(update, context, order_name, customer_id)
                    context.user_data.pop('pending_order_customer_id', None)
                    context.user_data.pop('pending_order_action', None)
                else:
                    await update.message.reply_text("Ошибка: данные заказа не найдены.")

                firebase.clear_user_state(user_id)
                return

            # АВТОРИЗАЦИЯ КЛИЕНТОВ
            elif state == 'client_login_username':
                context.user_data['login_client_login'] = text
                await update.message.reply_text("Введите пароль:")
                firebase.set_user_state(user_id, 'client_login_password')
                return

            elif state == 'client_login_password':
                login = context.user_data.get('login_client_login')
                password = text

                if login and firebase.check_client(login, password):
                    firebase.set_client_chat_id(login, user_id)

                    keyboard = [
                        [InlineKeyboardButton("📝 Создать заказ", callback_data='create_order')],
                        [InlineKeyboardButton("📋 Мои заказы", callback_data='my_client_orders')],
                        [InlineKeyboardButton("🎯 Наши услуги", callback_data='our_services')],
                        [InlineKeyboardButton("🎨 Наши работы", callback_data='our_works')],
                        [InlineKeyboardButton("🚪 Выйти", callback_data='client_logout')]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await update.message.reply_text(
                        f"Добро пожаловать, {login}!",
                        reply_markup=reply_markup
                    )
                    context.user_data['client_login'] = login
                else:
                    await update.message.reply_text("Неверный логин или пароль. Попробуйте снова.")

                firebase.clear_user_state(user_id)
                return

            # РЕГИСТРАЦИЯ КЛИЕНТОВ - ИСПРАВЛЕНО
            elif state == 'client_register_username':
                context.user_data['register_client_login'] = text
                await update.message.reply_text("Введите пароль:")
                firebase.set_user_state(user_id, 'client_register_password')
                return

            elif state == 'client_register_password':
                login = context.user_data.get('register_client_login')
                password = text

                if login:
                    # ИСПРАВЛЕНО: добавляем telegram_id автоматически
                    if firebase.register_client(login, password, chat_id=user_id, telegram_id=str(user_id)):
                        keyboard = [
                            [InlineKeyboardButton("📝 Создать заказ", callback_data='create_order')],
                            [InlineKeyboardButton("📋 Мои заказы", callback_data='my_client_orders')],
                            [InlineKeyboardButton("🎯 Наши услуги", callback_data='our_services')],
                            [InlineKeyboardButton("🎨 Наши работы", callback_data='our_works')],
                            [InlineKeyboardButton("🚪 Выйти", callback_data='client_logout')]
                        ]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        await update.message.reply_text(
                            f"Регистрация успешна! Добро пожаловать, {login}!",
                            reply_markup=reply_markup
                        )
                        context.user_data['client_login'] = login
                    else:
                        await update.message.reply_text(
                            "Пользователь с таким логином уже существует. Попробуйте другой логин."
                        )
                else:
                    await update.message.reply_text("Ошибка при регистрации.")

                firebase.clear_user_state(user_id)
                return

            # АВТОРИЗАЦИЯ ИСПОЛНИТЕЛЕЙ
            elif state == 'login':
                context.user_data['login'] = text
                await update.message.reply_text("Введите пароль:")
                firebase.set_user_state(user_id, 'password')
                return

            elif state == 'password':
                login = context.user_data.get('login')
                password = text

                if login and firebase.check_entrepreneur(login, password):
                    firebase.set_entrepreneur_chat_id(login, user_id)
                    balance = firebase.get_balance(login)

                    keyboard = [
                        [InlineKeyboardButton("📋 Мои заказы", callback_data='my_orders')],
                        [InlineKeyboardButton("👤 Личный кабинет", callback_data='personal_cabinet')],
                        [InlineKeyboardButton("🚪 Выйти", callback_data='logout')]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await update.message.reply_text(
                        f"Добро пожаловать в систему, {login}!\nВаш баланс: {balance} руб.",
                        reply_markup=reply_markup
                    )
                    context.user_data['contractor_login'] = login
                else:
                    await update.message.reply_text("Данные неверные. Попробуйте снова.")

                firebase.clear_user_state(user_id)
                return

            # РЕГИСТРАЦИЯ ИСПОЛНИТЕЛЕЙ (АДМИН) - ИСПРАВЛЕНО
            elif state == 'register_login':
                context.user_data['register_login'] = text
                await update.message.reply_text("Введите пароль:")
                firebase.set_user_state(user_id, 'register_password')
                return

            elif state == 'register_password':
                login = context.user_data.get('register_login')
                password = text

                if login:
                    # ИСПРАВЛЕНО: добавляем telegram_id автоматически
                    firebase.register_entrepreneur(login, password, chat_id=user_id, telegram_id=str(user_id))
                    await update.message.reply_text(f"Исполнитель {login} зарегистрирован!")
                else:
                    await update.message.reply_text("Ошибка при регистрации.")

                firebase.clear_user_state(user_id)
                return

            # СОЗДАНИЕ ЗАКАЗОВ С УВЕДОМЛЕНИЯМИ
            elif state == 'order_description':
                client_login = firebase.get_client_by_chat_id(user_id)
                if not client_login:
                    await update.message.reply_text("Ошибка: необходимо войти в аккаунт.")
                    firebase.clear_user_state(user_id)
                    return

                context.user_data['order_description'] = text
                context.user_data['client_login'] = client_login
                await update.message.reply_text("1. Какие у нас есть сроки?")
                firebase.set_user_state(user_id, 'order_deadline')
                return

            elif state == 'order_deadline':
                context.user_data['deadline'] = text
                await update.message.reply_text(
                    "2. Какой у вас ориентировочный бюджет? (Введите число, например 15 000)"
                )
                firebase.set_user_state(user_id, 'order_budget')
                return

            elif state == 'order_budget':
                from utils import is_valid_number, parse_number, format_order_info

                if is_valid_number(text):
                    budget = parse_number(text)
                    context.user_data['budget'] = text
                    context.user_data['order_amount'] = budget
                    client_login = context.user_data.get('client_login')

                    print(f"DEBUG: Начинаем поиск исполнителя для заказа от {client_login} на сумму {budget}")

                    # ИЩЕМ ИСПОЛНИТЕЛЯ С НАИВЫСШИМ РЕЙТИНГОМ
                    top_entrepreneur = firebase.get_top_executor()
                    print(f"DEBUG: Результат поиска топ исполнителя: {top_entrepreneur}")

                    if top_entrepreneur:
                        # Получаем chat_id исполнителя
                        top_entrepreneur_chat_id = firebase.get_user_chat_id_by_username(top_entrepreneur)
                        print(f"DEBUG: Chat ID исполнителя {top_entrepreneur}: {top_entrepreneur_chat_id}")

                        # СОЗДАЕМ ЗАКАЗ В FIREBASE
                        order_data = {
                            'title': 'Новый заказ',
                            'description': context.user_data.get('order_description', 'Не указано'),
                            'customer': {
                                'id': str(user_id),
                                'username': client_login
                            },
                            'executor': {
                                'id': '',
                                'username': top_entrepreneur
                            },
                            'amount': budget,
                            'deadline_text': context.user_data.get('deadline', 'Не указано'),
                            'status': 'pending',
                            'accepted': False,
                            'timer_active': False
                        }

                        print(f"DEBUG: Создаем заказ с данными: {order_data}")
                        order_id = firebase.create_order(order_data)
                        print(f"DEBUG: Заказ создан с ID: {order_id}")

                        # ОТПРАВЛЯЕМ УВЕДОМЛЕНИЕ ИСПОЛНИТЕЛЮ
                        if top_entrepreneur_chat_id and order_id:
                            order_info_text = format_order_info(
                                context.user_data.get('order_description', 'Не указано'),
                                context.user_data.get('deadline', 'Не указано'),
                                context.user_data['budget'],
                                client_login
                            )

                            keyboard = [
                                [InlineKeyboardButton("✅ Принять заказ", callback_data=f'accept_order_{user_id}')],
                                [InlineKeyboardButton("❌ Отказаться", callback_data=f'decline_order_{user_id}')]
                            ]
                            reply_markup = InlineKeyboardMarkup(keyboard)

                            context.user_data['pending_order_id'] = order_id

                            # Сохраняем связь между customer_id и order_id в Firebase для быстрого поиска
                            firebase.db.collection('temp_orders').document(str(user_id)).set({
                                'order_id': order_id,
                                'customer_id': user_id,
                                'executor': top_entrepreneur,
                                'created_at': datetime.now()
                            })

                            try:
                                print(
                                    f"DEBUG: Отправляем уведомление исполнителю {top_entrepreneur} (chat_id: {top_entrepreneur_chat_id})")
                                await context.bot.send_message(
                                    chat_id=top_entrepreneur_chat_id,
                                    text=f"🔔 НОВЫЙ ЗАКАЗ!\n\n{order_info_text}",
                                    reply_markup=reply_markup
                                )
                                print(f"DEBUG: Уведомление успешно отправлено!")

                                await update.message.reply_text(
                                    "✅ Заказ успешно создан!\n\n"
                                    f"🎯 Исполнитель {top_entrepreneur} получил уведомление и скоро свяжется с вами.\n\n"
                                    "📱 Вы получите уведомление, когда исполнитель ответит."
                                )
                            except Exception as e:
                                print(f"DEBUG: Ошибка отправки уведомления исполнителю: {e}")
                                import traceback
                                traceback.print_exc()
                                await update.message.reply_text(
                                    "Заказ создан, но возникла проблема с уведомлением исполнителя.\n"
                                    "Мы свяжемся с вами в ближайшее время."
                                )
                        else:
                            print(
                                f"DEBUG: Проблема с отправкой - chat_id: {top_entrepreneur_chat_id}, order_id: {order_id}")
                            await update.message.reply_text(
                                "Заказ создан! Мы обработаем его и свяжемся с вами в ближайшее время."
                            )
                    else:
                        print("DEBUG: Топ исполнитель не найден")
                        await update.message.reply_text(
                            "К сожалению, в системе нет доступных исполнителей.\n"
                            "Мы добавим вас в очередь и свяжемся, когда появится свободный специалист."
                        )

                    firebase.clear_user_state(user_id)
                else:
                    await update.message.reply_text(
                        "Просим вас написать число. Это поможет нам подобрать лучшее решение для вашей ситуации."
                    )
                return

            # ЧАТЫ КЛИЕНТОВ - ИСПРАВЛЕНО
            elif state.startswith('in_client_chat_'):
                order_id = state.replace('in_client_chat_', '')
                message_text = text

                # Получаем логин клиента напрямую
                client_login = firebase.get_client_by_chat_id(user_id)
                if not client_login:
                    await update.message.reply_text("Необходимо войти в систему.")
                    firebase.clear_user_state(user_id)
                    return

                order = firebase.get_order_by_id(order_id)
                if not order:
                    await update.message.reply_text("Заказ не найден.")
                    firebase.clear_user_state(user_id)
                    return

                # Проверяем, что это заказ данного клиента
                if order.get('customer', {}).get('username') != client_login:
                    await update.message.reply_text("У вас нет доступа к этому заказу.")
                    firebase.clear_user_state(user_id)
                    return

                # Сохраняем сообщение
                firebase.add_message(
                    order_id=order_id,
                    user_id=str(user_id),  # Используем chat_id как user_id
                    user_role='customer',  # Роль пользователя
                    text=message_text
                )

                print(f"Сообщение от клиента {client_login} сохранено: {message_text}")

                # Уведомляем исполнителя
                executor_name = order.get('executor', {}).get('username')
                if executor_name:
                    executor_chat_id = firebase.get_user_chat_id_by_username(executor_name)
                    if executor_chat_id:
                        try:
                            await context.bot.send_message(
                                chat_id=executor_chat_id,
                                text=f"Новое сообщение от заказчика\n"
                                     f"Заказ: {order.get('title', 'Без названия')}\n"
                                     f"Сообщение: {message_text}"
                            )
                        except Exception as e:
                            print(f"Ошибка отправки уведомления исполнителю: {e}")

                await update.message.reply_text("Сообщение отправлено исполнителю")
                return

            # ЧАТЫ ИСПОЛНИТЕЛЕЙ - ИСПРАВЛЕНО
            elif state.startswith('in_contractor_chat_'):
                order_id = state.replace('in_contractor_chat_', '')
                message_text = text

                # Получаем логин исполнителя напрямую
                contractor_login = firebase.get_entrepreneur_by_chat_id(user_id)
                if not contractor_login:
                    await update.message.reply_text("Необходимо войти в систему.")
                    firebase.clear_user_state(user_id)
                    return

                order = firebase.get_order_by_id(order_id)
                if not order:
                    await update.message.reply_text("Заказ не найден.")
                    firebase.clear_user_state(user_id)
                    return

                # Проверяем, что это заказ данного исполнителя
                if order.get('executor', {}).get('username') != contractor_login:
                    await update.message.reply_text("У вас нет доступа к этому заказу.")
                    firebase.clear_user_state(user_id)
                    return

                # Сохраняем сообщение
                firebase.add_message(
                    order_id=order_id,
                    user_id=str(user_id),  # Используем chat_id как user_id
                    user_role='executor',  # Роль пользователя
                    text=message_text
                )

                print(f"Сообщение от исполнителя {contractor_login} сохранено: {message_text}")

                # Уведомляем заказчика
                customer_name = order.get('customer', {}).get('username')
                if customer_name:
                    customer_chat_id = firebase.get_user_chat_id_by_username(customer_name)
                    if customer_chat_id:
                        try:
                            await context.bot.send_message(
                                chat_id=customer_chat_id,
                                text=f"Новое сообщение от исполнителя\n"
                                     f"Заказ: {order.get('title', 'Без названия')}\n"
                                     f"Сообщение: {message_text}"
                            )
                        except Exception as e:
                            print(f"Ошибка отправки уведомления заказчику: {e}")

                await update.message.reply_text("Сообщение отправлено заказчику")
                return

            # ОБРАБОТКА ВЫВОДА СРЕДСТВ
            elif state.startswith('withdraw_amount_input_'):
                contractor_login = state.replace('withdraw_amount_input_', '')
                try:
                    amount = float(text.replace(' ', '').replace(',', '.'))
                    balance = firebase.get_balance(contractor_login)

                    if amount <= 0:
                        await update.message.reply_text("Сумма должна быть больше 0.")
                        return

                    if amount > balance:
                        await update.message.reply_text(
                            f"Недостаточно средств.\nДоступно: {balance} руб.\nВведите меньшую сумму:"
                        )
                        return

                    keyboard = [
                        [InlineKeyboardButton("✅ Подтвердить",
                                              callback_data=f'withdraw_amount_{contractor_login}_{amount}')],
                        [InlineKeyboardButton("❌ Отмена", callback_data='personal_cabinet')]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)

                    await update.message.reply_text(
                        f"Подтвердите вывод {amount} руб.\nС баланса будет списано: {amount} руб.",
                        reply_markup=reply_markup
                    )

                except ValueError:
                    await update.message.reply_text("Введите корректную сумму (только цифры):")
                    return

                firebase.clear_user_state(user_id)
                return

            else:
                print(f"Неизвестное состояние: {state}")
                await update.message.reply_text(f"Неизвестное состояние: {state}")
                firebase.clear_user_state(user_id)

        except Exception as e:
            print(f"КРИТИЧЕСКАЯ ОШИБКА: {e}")
            import traceback
            traceback.print_exc()
            await update.message.reply_text(f"Ошибка: {str(e)}")
            firebase.clear_user_state(user_id)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик фотографий с Firebase"""
    firebase = context.bot_data['firebase']
    user_id = update.message.from_user.id
    state = firebase.get_user_state(user_id)

    print(f"ФОТО: User={user_id}, State='{state}'")

    # Проверяем состояния для фото
    if state in ['add_sites_photo', 'add_video_photo']:
        try:
            photo_file_id = update.message.photo[-1].file_id
            print(f"Сохраняем file_id: {photo_file_id}")

            if state == 'add_sites_photo':
                context.user_data['site_photo'] = photo_file_id
                context.user_data['site_photo_type'] = 'file_id'
                await update.message.reply_text("Фото сохранено! Введите описание:")
                firebase.set_user_state(user_id, 'add_sites_description')

            elif state == 'add_video_photo':
                context.user_data['video_photo'] = photo_file_id
                context.user_data['video_photo_type'] = 'file_id'
                await update.message.reply_text("Превью сохранено! Введите описание:")
                firebase.set_user_state(user_id, 'add_video_description')

        except Exception as e:
            print(f"Ошибка при обработке фото: {e}")
            await update.message.reply_text(f"Ошибка при сохранении фото: {e}")
    else:
        print(f"Неподходящее состояние для фото: {state}")
        await update.message.reply_text("Отправьте фото в нужный момент")