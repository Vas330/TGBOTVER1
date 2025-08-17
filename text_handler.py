# text_handler.py
from telegram import Update
from telegram.ext import ContextTypes

from state_manager import user_state
from handlers_common import handle_admin_command
from handlers_client import handle_order_creation, handle_client_auth, handle_chat_messages
from handlers_contractor import handle_login_process
from handlers_admin import handle_registration_process, handle_admin_updates, handle_portfolio_addition


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
            # Обработка чатов
            if await handle_chat_messages(update, context, state):
                return

            # Обработка создания заказов клиентами
            if await handle_order_creation(update, context, state):
                return

            # Обработка авторизации клиентов
            if await handle_client_auth(update, context, state):
                return

            # Обработка авторизации исполнителей
            if await handle_login_process(update, context, state):
                return

            # Обработка регистрации исполнителей (админ)
            if await handle_registration_process(update, context, state):
                return

            # Обработка административных обновлений (включая удаление портфолио)
            if await handle_admin_updates(update, context, state):
                return

            # ОБРАБОТКА СТАРОГО ФОРМАТА ПОРТФОЛИО (упрощенная и рабочая версия)
            if state.startswith('add_'):
                await handle_old_portfolio_format(update, context, state, text)
                return

            # Если ничего не подошло
            print(f"🔥 Неизвестное состояние: {state}")
            await update.message.reply_text(f"Неизвестное состояние: {state}")
            user_state.set_state(user_id, None)

        except Exception as e:
            print(f"💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
            import traceback
            traceback.print_exc()
            await update.message.reply_text(f"💥 Ошибка: {str(e)}")
            user_state.set_state(user_id, None)


async def handle_old_portfolio_format(update: Update, context: ContextTypes.DEFAULT_TYPE, state: str,
                                      text: str) -> None:
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
    if state in ['add_sites_photo', 'add_video_photo', 'portfolio_add_sites_images', 'portfolio_add_video_images']:
        try:
            # Получаем file_id самого большого размера фото
            photo_file_id = update.message.photo[-1].file_id
            print(f"📸 Сохраняем file_id: {photo_file_id}")

            # СТАРЫЙ ФОРМАТ
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

            # НОВЫЙ ФОРМАТ
            elif state == 'portfolio_add_sites_images':
                images = context.user_data.get('portfolio_sites_images', [])
                images.append(photo_file_id)
                context.user_data['portfolio_sites_images'] = images
                await update.message.reply_text("✅ Фото добавлено! Отправьте еще фото или напишите 'готово':")

            elif state == 'portfolio_add_video_images':
                images = context.user_data.get('portfolio_video_images', [])
                images.append(photo_file_id)
                context.user_data['portfolio_video_images'] = images
                await update.message.reply_text("✅ Фото добавлено! Отправьте еще фото или напишите 'готово':")

        except Exception as e:
            print(f"💥 Ошибка при обработке фото: {e}")
            await update.message.reply_text(f"Ошибка при сохранении фото: {e}")
    else:
        print(f"📸 Неподходящее состояние для фото: {state}")
        await update.message.reply_text("Отправьте фото в нужный момент процесса добавления.")