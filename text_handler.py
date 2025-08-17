# text_handler.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from state_manager import user_state
from handlers_common import handle_admin_command


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Простой обработчик текстовых сообщений"""
    user_id = update.message.from_user.id
    text = update.message.text.strip() if update.message.text else ""
    state = user_state.get_state(user_id)

    print(f"🔥 ОТЛАДКА: User={user_id}, Text='{text}', State='{state}'")

    # Обработка команды админ
    if text.lower() == "админ":
        await handle_admin_command(update, context)
        return

    # ТЕСТОВАЯ КОМАНДА
    if text.lower() == "тест":
        try:
            user_state.add_portfolio_item('sites', 'Тест сайт', 'Тест описание', ['https://test.jpg'],
                                          ['https://test.com'])
            sites = user_state.get_portfolio_items('sites')
            await update.message.reply_text(f"✅ Тест: в портфолио {len(sites)} сайтов")
            return
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка теста: {e}")
            return

    # ОБРАБОТКА СОСТОЯНИЙ
    if state:
        print(f"🔥 Обрабатываем состояние: {state}")

        try:
            # АВТОРИЗАЦИЯ КЛИЕНТОВ
            if state == 'client_login_username':
                context.user_data['login_client_login'] = text
                await update.message.reply_text("Введите пароль:")
                user_state.set_state(user_id, 'client_login_password')
                return

            elif state == 'client_login_password':
                login = context.user_data.get('login_client_login')
                password = text

                if login and user_state.check_client(login, password):
                    user_state.set_client_chat_id(login, user_id)
                    
                    keyboard = [
                        [InlineKeyboardButton("Создать заказ", callback_data='create_order')],
                        [InlineKeyboardButton("Наши работы", callback_data='our_works')],
                        [InlineKeyboardButton("Выйти", callback_data='client_logout')]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await update.message.reply_text(
                        f"✅ Добро пожаловать, {login}!",
                        reply_markup=reply_markup
                    )
                    context.user_data['client_login'] = login
                else:
                    await update.message.reply_text("❌ Неверный логин или пароль. Попробуйте снова.")

                user_state.set_state(user_id, None)
                return

            # РЕГИСТРАЦИЯ КЛИЕНТОВ
            elif state == 'client_register_username':
                context.user_data['register_client_login'] = text
                await update.message.reply_text("Введите пароль:")
                user_state.set_state(user_id, 'client_register_password')
                return

            elif state == 'client_register_password':
                login = context.user_data.get('register_client_login')
                password = text

                if login:
                    if user_state.register_client(login, password, chat_id=user_id):
                        keyboard = [
                            [InlineKeyboardButton("Создать заказ", callback_data='create_order')],
                            [InlineKeyboardButton("Наши работы", callback_data='our_works')],
                            [InlineKeyboardButton("Выйти", callback_data='client_logout')]
                        ]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        await update.message.reply_text(
                            f"✅ Регистрация успешна! Добро пожаловать, {login}!",
                            reply_markup=reply_markup
                        )
                        context.user_data['client_login'] = login
                    else:
                        await update.message.reply_text(
                            "❌ Пользователь с таким логином уже существует. Попробуйте другой логин."
                        )
                else:
                    await update.message.reply_text("❌ Ошибка при регистрации.")

                user_state.set_state(user_id, None)
                return

            # АВТОРИЗАЦИЯ ИСПОЛНИТЕЛЕЙ
            elif state == 'login':
                context.user_data['login'] = text
                await update.message.reply_text("Введите пароль:")
                user_state.set_state(user_id, 'password')
                return

            elif state == 'password':
                login = context.user_data.get('login')
                password = text

                if login and user_state.check_entrepreneur(login, password):
                    # Успешный вход
                    user_state.set_entrepreneur_chat_id(login, user_id)
                    balance = user_state.get_entrepreneur_balance(login)

                    keyboard = [
                        [InlineKeyboardButton("Мои заказы", callback_data='my_orders')],
                        [InlineKeyboardButton("Выйти", callback_data='logout')]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await update.message.reply_text(
                        f"✅ Добро пожаловать в систему, {login}!\nВаш баланс: {balance} руб.",
                        reply_markup=reply_markup
                    )
                    context.user_data['contractor_login'] = login
                else:
                    await update.message.reply_text("❌ Данные неверные. Попробуйте снова.")

                user_state.set_state(user_id, None)
                return

            # РЕГИСТРАЦИЯ ИСПОЛНИТЕЛЕЙ (АДМИН)
            elif state == 'register_login':
                context.user_data['register_login'] = text
                await update.message.reply_text("Введите пароль:")
                user_state.set_state(user_id, 'register_password')
                return

            elif state == 'register_password':
                login = context.user_data.get('register_login')
                password = text

                if login:
                    user_state.register_entrepreneur(login, password, chat_id=user_id)
                    await update.message.reply_text(f"✅ Исполнитель {login} зарегистрирован!")
                else:
                    await update.message.reply_text("❌ Ошибка при регистрации.")

                user_state.set_state(user_id, None)
                return

            # СОЗДАНИЕ ЗАКАЗОВ
            elif state == 'order_description':
                client_login = user_state.get_client_by_chat_id(user_id)
                if not client_login:
                    await update.message.reply_text("❌ Ошибка: необходимо войти в аккаунт.")
                    user_state.set_state(user_id, None)
                    return

                context.user_data['order_description'] = text
                context.user_data['client_login'] = client_login
                await update.message.reply_text("1. Какие у нас есть сроки?")
                user_state.set_state(user_id, 'order_deadline')
                return

            elif state == 'order_deadline':
                context.user_data['deadline'] = text
                await update.message.reply_text(
                    "2. Какой у вас ориентировочный бюджет? (Введите число, например 15 000)"
                )
                user_state.set_state(user_id, 'order_budget')
                return

            elif state == 'order_budget':
                from utils import is_valid_number, parse_number
                if is_valid_number(text):
                    budget = parse_number(text)
                    context.user_data['budget'] = text
                    context.user_data['order_amount'] = budget

                    await update.message.reply_text(
                        "✅ Спасибо за предоставленную информацию. Мы скоро свяжемся с вами."
                    )

                    # Здесь можно добавить логику отправки заказа исполнителю
                    user_state.set_state(user_id, None)
                else:
                    await update.message.reply_text(
                        "❌ Просим вас написать число. Это поможет нам подобрать лучшее решение для вашей ситуации."
                    )
                return

            # ОБРАБОТКА ПОРТФОЛИО (старый формат)
            elif state.startswith('add_'):
                await handle_old_portfolio_format(update, context, state, text)
                return

            # АДМИНСКИЕ ОПЕРАЦИИ
            elif state.startswith('new_rating_'):
                login = state.split('_')[2]
                try:
                    rating = int(text)
                    if 1 <= rating <= 10:
                        if user_state.update_entrepreneur_rating(login, rating):
                            await update.message.reply_text("✅ Рейтинг обновлен!")
                        else:
                            await update.message.reply_text("❌ Исполнитель не найден.")
                    else:
                        await update.message.reply_text("❌ Рейтинг должен быть от 1 до 10.")
                except ValueError:
                    await update.message.reply_text("❌ Введите число.")
                user_state.set_state(user_id, None)
                return

            elif state.startswith('new_balance_'):
                login = state.split('_')[2]
                try:
                    balance = float(text.replace(' ', ''))
                    if user_state.set_entrepreneur_balance(login, balance):
                        await update.message.reply_text("✅ Баланс обновлен!")
                    else:
                        await update.message.reply_text("❌ Исполнитель не найден.")
                except ValueError:
                    await update.message.reply_text("❌ Введите корректную сумму.")
                user_state.set_state(user_id, None)
                return

            elif state.startswith('delete_confirm_') and not state.startswith('delete_confirm_sites') and not state.startswith('delete_confirm_video'):
                # Удаление исполнителя
                parts = state.split('_')
                if len(parts) >= 3:
                    login = '_'.join(parts[2:])  # Восстанавливаем логин, если в нем есть подчеркивания
                    response = text.lower().strip()

                    if response == 'да':
                        if user_state.delete_entrepreneur(login):
                            await update.message.reply_text(f"✅ Исполнитель {login} удален.")
                        else:
                            await update.message.reply_text("❌ Исполнитель не найден.")
                    elif response == 'нет':
                        await update.message.reply_text("❌ Удаление отменено.")
                    else:
                        await update.message.reply_text("❓ Пожалуйста, введите 'да' или 'нет'.")
                        return  # Не сбрасываем состояние

                user_state.set_state(user_id, None)
                return

            # УДАЛЕНИЕ ПОРТФОЛИО
            elif state.startswith('delete_confirm_'):
                response = text.lower().strip()
                
                category = context.user_data.get('delete_category')
                index = context.user_data.get('delete_index')
                title = context.user_data.get('delete_title', 'Неизвестный элемент')

                if response == 'да':
                    if user_state.delete_portfolio_item(category, index):
                        await update.message.reply_text(f"✅ Элемент '{title}' успешно удален!")
                    else:
                        await update.message.reply_text("❌ Ошибка при удалении элемента.")
                        
                elif response == 'нет':
                    await update.message.reply_text("❌ Удаление отменено.")
                else:
                    await update.message.reply_text("❓ Пожалуйста, напишите 'да' или 'нет'.")
                    return  # Не сбрасываем состояние

                # Очищаем данные
                context.user_data.pop('delete_category', None)
                context.user_data.pop('delete_index', None)
                context.user_data.pop('delete_title', None)
                user_state.set_state(user_id, None)
                return

            # ЧАТЫ
            elif state.startswith('in_chat_'):
                chat_id = state.replace('in_chat_', '')
                message_text = text

                chat_info = user_state.get_chat_info(chat_id)
                if not chat_info or not chat_info.get('active', False):
                    await update.message.reply_text("❌ Чат неактивен.")
                    user_state.set_state(user_id, None)
                    return

                partner_chat_id = user_state.get_chat_partner(chat_id, user_id)
                if not partner_chat_id:
                    await update.message.reply_text("❌ Партнер по чату не найден.")
                    return

                from utils import get_user_role_in_chat, format_chat_message
                sender_role = get_user_role_in_chat(user_id, chat_info)
                formatted_message = format_chat_message(sender_role, message_text)

                try:
                    await context.bot.send_message(chat_id=partner_chat_id, text=formatted_message)
                    await update.message.reply_text("✅ Сообщение доставлено")
                except Exception as e:
                    await update.message.reply_text("❌ Ошибка при отправке сообщения")
                    print(f"Ошибка отправки сообщения: {e}")
                return

            else:
                print(f"🔥 Неизвестное состояние: {state}")
                await update.message.reply_text(f"❌ Неизвестное состояние: {state}")
                user_state.set_state(user_id, None)

        except Exception as e:
            print(f"💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
            import traceback
            traceback.print_exc()
            await update.message.reply_text(f"💥 Ошибка: {str(e)}")
            user_state.set_state(user_id, None)


async def handle_old_portfolio_format(update: Update, context: ContextTypes.DEFAULT_TYPE, state: str, text: str) -> None:
    """Обрабатывает старый формат добавления портфолио"""
    user_id = update.message.from_user.id
    
    print(f"🔥 СТАРЫЙ ФОРМАТ: состояние {state}")

    if state == 'add_sites_title':
        print(f"🔥 Шаг 1: Сохраняем название '{text}'")
        context.user_data['site_title'] = text
        await update.message.reply_text("Отправьте фото (картинкой) или ссылку на фото:")
        user_state.set_state(user_id, 'add_sites_photo')

    elif state == 'add_sites_photo':
        if text:  # Если это текст (ссылка)
            print(f"🔥 Шаг 2: Сохраняем ссылку на фото '{text}'")
            context.user_data['site_photo'] = text
            context.user_data['site_photo_type'] = 'url'
            await update.message.reply_text("Введите описание:")
            user_state.set_state(user_id, 'add_sites_description')
        else:
            await update.message.reply_text("Отправьте фото или ссылку на фото")

    elif state == 'add_sites_description':
        print(f"🔥 Шаг 3: Сохраняем описание '{text}'")
        context.user_data['site_description'] = text
        await update.message.reply_text("Введите ссылку на сайт:")
        user_state.set_state(user_id, 'add_sites_link')

    elif state == 'add_sites_link':
        print(f"🔥 Шаг 4: Сохраняем ссылку '{text}'")

        title = context.user_data.get('site_title', 'Без названия')
        photo = context.user_data.get('site_photo', '')
        description = context.user_data.get('site_description', 'Без описания')

        # Сохраняем
        user_state.add_portfolio_item('sites', title, description, [photo], [text])
        await update.message.reply_text(f"✅ Сайт '{title}' добавлен!")

        # Очистка
        for key in ['site_title', 'site_photo', 'site_photo_type', 'site_description']:
            context.user_data.pop(key, None)

        user_state.set_state(user_id, None)

    # ВИДЕО аналогично
    elif state == 'add_video_title':
        context.user_data['video_title'] = text
        await update.message.reply_text("Отправьте превью (картинкой) или ссылку:")
        user_state.set_state(user_id, 'add_video_photo')

    elif state == 'add_video_photo':
        if text:
            context.user_data['video_photo'] = text
            context.user_data['video_photo_type'] = 'url'
            await update.message.reply_text("Введите описание:")
            user_state.set_state(user_id, 'add_video_description')
        else:
            await update.message.reply_text("Отправьте превью или ссылку")

    elif state == 'add_video_description':
        context.user_data['video_description'] = text
        await update.message.reply_text("Введите ссылку на видео:")
        user_state.set_state(user_id, 'add_video_link')

    elif state == 'add_video_link':
        title = context.user_data.get('video_title', 'Без названия')
        photo = context.user_data.get('video_photo', '')
        description = context.user_data.get('video_description', 'Без описания')

        user_state.add_portfolio_item('video', title, description, [photo], [text])
        await update.message.reply_text(f"✅ Видео '{title}' добавлено!")

        for key in ['video_title', 'video_photo', 'video_photo_type', 'video_description']:
            context.user_data.pop(key, None)

        user_state.set_state(user_id, None)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик фотографий"""
    user_id = update.message.from_user.id
    state = user_state.get_state(user_id)

    print(f"📸 ФОТО: User={user_id}, State='{state}'")

    # Проверяем все возможные состояния для фото
    if state in ['add_sites_photo', 'add_video_photo']:
        try:
            # Получаем file_id самого большого размера фото
            photo_file_id = update.message.photo[-1].file_id
            print(f"📸 Сохраняем file_id: {photo_file_id}")

            if state == 'add_sites_photo':
                context.user_data['site_photo'] = photo_file_id
                context.user_data['site_photo_type'] = 'file_id'
                await update.message.reply_text("✅ Фото сохранено! Введите описание:")
                user_state.set_state(user_id, 'add_sites_description')

            elif state == 'add_video_photo':
                context.user_data['video_photo'] = photo_file_id
                context.user_data['video_photo_type'] = 'file_id'
                await update.message.reply_text("✅ Превью сохранено! Введите описание:")
                user_state.set_state(user_id, 'add_video_description')

        except Exception as e:
            print(f"💥 Ошибка при обработке фото: {e}")
            await update.message.reply_text(f"❌ Ошибка при сохранении фото: {e}")
    else:
        print(f"📸 Неподходящее состояние для фото: {state}")
        await update.message.reply_text("❌ Отправьте фото в нужный момент процесса добавления.")
