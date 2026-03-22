"""
Обработчик текстовых сообщений
"""
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from database import Database
from config import Config
from keyboards import get_main_menu_back_keyboard, get_box_view_keyboard, get_boxes_keyboard, get_item_keyboard
from messages import (
    format_box_text,
    format_item_text,
    format_search_results,
    format_not_found,
    format_item_already_exists,
    format_box_already_exists,
)
from helpers import check_authorization, send_and_delete, delete_user_message, delete_message_background
import asyncio
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def create_user_message_handler(db: Database):
    """Создаёт обработчик текстовых сообщений"""

    async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not check_authorization(update):
            return

        text = update.message.text

        # Отмена действия командой /cancel
        if text == '/cancel':
            context.user_data['awaiting_box_create'] = False
            context.user_data['awaiting_box_edit'] = False
            context.user_data['edit_box_id'] = None
            context.user_data['awaiting_item_edit'] = False
            context.user_data['edit_item_id'] = None
            context.user_data['awaiting_item_comment_edit'] = False
            context.user_data['edit_item_comment_id'] = None
            context.user_data['edit_item_box_id'] = None
            context.user_data['add_item_name'] = None
            context.user_data['awaiting_box_select'] = False
            context.user_data['awaiting_item_name'] = False
            context.user_data['add_item_box_id'] = None
            await send_and_delete(update.message, '❌ Действие отменено')
            return

        # Выбор бокса для предмета (если пользователь написал текст вместо нажатия кнопки)
        if context.user_data.get('awaiting_box_select'):
            await send_and_delete(update.message, '📝 Пожалуйста, выберите бокс из предложенных кнопок ниже.\nДля отмены: /cancel')
            return

        # Поиск предмета из меню
        if context.user_data.get('awaiting_menu_find'):
            try:
                items = db.search_items(text)

                if not items:
                    # Отправляем сообщение об ошибке
                    error_msg = await update.message.reply_text(format_not_found(text))

                    # Удаляем оба сообщения через 5 секунд
                    await asyncio.sleep(5)
                    try:
                        await update.message.delete()
                    except:
                        pass
                    try:
                        await error_msg.delete()
                    except:
                        pass

                    context.user_data['awaiting_menu_find'] = False
                    return

                await update.message.reply_text(
                    format_search_results(items, db),
                    reply_markup=get_main_menu_back_keyboard()
                )

                # Удаляем сообщение пользователя в фоне
                asyncio.create_task(delete_message_background(
                    context.bot,
                    update.message.chat_id,
                    update.message.message_id,
                    delay=5
                ))
                context.user_data['awaiting_menu_find'] = False
            except Exception as e:
                logger.error(f'Ошибка при поиске: {e}')
                await update.message.reply_text('❌ Ошибка при поиске')
            return

        # Создание бокса
        if context.user_data.get('awaiting_box_create'):
            name = text.strip()

            existing = db.get_box_by_name(name)
            if existing:
                await send_and_delete(update.message, format_box_already_exists(name))
                return

            db.create_box(name=name)

            boxes = db.get_all_boxes()
            items_counts = {box.id: len(db.get_items_by_box(box.id)) for box in boxes}

            # Сначала отправляем список боксов
            await update.message.reply_text(
                '📦 Выберите бокс для управления:',
                reply_markup=get_boxes_keyboard(boxes, items_counts)
            )

            # Затем отправляем подтверждение и удаляем его в фоне
            confirm_msg = await update.message.reply_text(f'✅ Бокс "{name}" создан!')
            asyncio.create_task(delete_message_background(
                context.bot,
                update.message.chat_id,
                confirm_msg.message_id,
                delay=3
            ))

            await delete_user_message(update)
            context.user_data['awaiting_box_create'] = False
            return

        # Ввод названия предмета для добавления в бокс
        if context.user_data.get('awaiting_item_name'):
            box_id = context.user_data.get('add_item_box_id')
            item_name = text.strip()

            if not item_name:
                await update.message.reply_text('❌ Введите название предмета')
                return

            box = db.get_box_by_id(box_id)
            # existing_items = db.get_items_by_box(box_id)

            # if any(item.name == item_name for item in existing_items):
            #     error_msg = await update.message.reply_text(
            #         msg_module.format_item_already_exists(item_name, box.name)
            #     )

            #     items = db.get_items_by_box(box_id)
            #     await update.message.reply_text(
            #         msg_module.format_box_text(box, len(items)),
            #         reply_markup=get_box_view_keyboard(box, items),
            #         parse_mode='HTML'
            #     )

            #     await asyncio.sleep(5)
            #     try:
            #         await update.message.delete()
            #     except:
            #         pass
            #     try:
            #         await error_msg.delete()
            #     except:
            #         pass

            #     context.user_data['awaiting_item_name'] = False
            #     context.user_data['add_item_box_id'] = None
            #     return

            user = update.effective_user
            username = user.username
            user_display = f'@{username}' if username else (user.first_name or str(user.id))
            created_at = datetime.now().strftime('%Y-%m-%d %H:%M')
            created_by = f'{user_display} ({created_at})'

            db.create_item(name=item_name, box_id=box_id, created_by=created_by)

            items = db.get_items_by_box(box_id)

            # Экранируем HTML символы в названии предмета
            safe_item_name = item_name.replace('<', '&lt;').replace('>', '&gt;')

            # Сначала отправляем меню бокса
            await update.message.reply_text(
                format_box_text(box, len(items)),
                reply_markup=get_box_view_keyboard(box, items),
                parse_mode='HTML'
            )

            # Затем отправляем подтверждение и удаляем его в фоне
            confirm_msg = await update.message.reply_text(f'✅ Предмет "{safe_item_name}" добавлен!')
            asyncio.create_task(delete_message_background(
                context.bot,
                update.message.chat_id,
                confirm_msg.message_id,
                delay=3
            ))

            await delete_user_message(update)

            request_msg_id = context.user_data.get('item_request_message_id')
            if request_msg_id:
                try:
                    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=request_msg_id)
                    context.user_data['item_request_message_id'] = None
                except:
                    pass

            context.user_data['awaiting_item_name'] = False
            context.user_data['add_item_box_id'] = None
            return

        # Редактирование бокса
        if context.user_data.get('awaiting_box_edit'):
            box_id = context.user_data.get('edit_box_id')
            db.update_box(box_id=box_id, name=text)

            box = db.get_box_by_id(box_id)
            items = db.get_items_by_box(box_id)

            # Сначала отправляем меню бокса
            await update.message.reply_text(
                format_box_text(box, len(items)),
                reply_markup=get_box_view_keyboard(box, items),
                parse_mode='HTML'
            )

            # Затем отправляем подтверждение и удаляем его в фоне
            confirm_msg = await update.message.reply_text(f'✅ Бокс переименован!')
            asyncio.create_task(delete_message_background(
                context.bot,
                update.message.chat_id,
                confirm_msg.message_id,
                delay=3
            ))

            await delete_user_message(update)

            request_msg_id = context.user_data.get('edit_box_request_message_id')
            if request_msg_id:
                try:
                    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=request_msg_id)
                    context.user_data['edit_box_request_message_id'] = None
                except:
                    pass

            context.user_data['awaiting_box_edit'] = False
            context.user_data['edit_box_id'] = None
            return

        # Редактирование предмета
        if context.user_data.get('awaiting_item_edit'):
            item_id = context.user_data.get('edit_item_id')
            db.update_item(item_id=item_id, name=text)

            item = db.get_item_by_id(item_id)
            box = db.get_box_by_id(item.box_id)

            # Сначала отправляем клавиатуру предмета
            await update.message.reply_text(
                format_item_text(item, box),
                reply_markup=get_item_keyboard(item, box),
                parse_mode='HTML'
            )

            # Затем отправляем подтверждение и удаляем его в фоне
            confirm_msg = await update.message.reply_text('✅ Предмет переименован!')
            asyncio.create_task(delete_message_background(
                context.bot,
                update.message.chat_id,
                confirm_msg.message_id,
                delay=3
            ))

            await delete_user_message(update)

            request_msg_id = context.user_data.get('edit_item_request_message_id')
            if request_msg_id:
                try:
                    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=request_msg_id)
                    context.user_data['edit_item_request_message_id'] = None
                except:
                    pass

            context.user_data['awaiting_item_edit'] = False
            context.user_data['edit_item_id'] = None
            context.user_data['edit_item_box_id'] = None
            return

        # Редактирование комментария предмета
        if context.user_data.get('awaiting_item_comment_edit'):
            item_id = context.user_data.get('edit_item_comment_id')
            box_id = context.user_data.get('edit_item_box_id')

            comment = text.strip()
            db.update_item(item_id=item_id, comment=comment)

            item = db.get_item_by_id(item_id)
            box = db.get_box_by_id(item.box_id)

            # Сначала отправляем клавиатуру предмета
            await update.message.reply_text(
                format_item_text(item, box),
                reply_markup=get_item_keyboard(item, box),
                parse_mode='HTML'
            )

            # Затем отправляем подтверждение и удаляем его в фоне
            confirm_msg = await update.message.reply_text('✅ Комментарий сохранён!')
            asyncio.create_task(delete_message_background(
                context.bot,
                update.message.chat_id,
                confirm_msg.message_id,
                delay=3
            ))

            await delete_user_message(update)

            request_msg_id = context.user_data.get('edit_item_comment_request_message_id')
            if request_msg_id:
                try:
                    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=request_msg_id)
                    context.user_data['edit_item_comment_request_message_id'] = None
                except:
                    pass

            context.user_data['edit_item_comment_id'] = None
            context.user_data['edit_item_box_id'] = None
            context.user_data['awaiting_item_comment_edit'] = False
            return

        # Все остальные сообщения пользователя - удаляем через 5 секунд
        await asyncio.sleep(5)
        try:
            await update.message.delete()
        except:
            pass

    return MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler)
