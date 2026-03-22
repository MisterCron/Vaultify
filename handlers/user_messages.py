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
    format_box_already_exists,
)
from helpers import check_authorization
from services.notification import NotificationService
from dto import BoxDto, ItemDto
import asyncio
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def create_user_message_handler(db: Database, notification_service: NotificationService):
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
            await notification_service.notify(
                chat_id=update.effective_chat.id,
                text='❌ Действие отменено',
            )
            return

        # Выбор бокса для предмета (если пользователь написал текст вместо нажатия кнопки)
        if context.user_data.get('awaiting_box_select'):
            await notification_service.notify(
                chat_id=update.effective_chat.id,
                text='📝 Пожалуйста, выберите бокс из предложенных кнопок ниже.\nДля отмены: /cancel',
            )
            return

        # Поиск предмета из меню
        if context.user_data.get('awaiting_menu_find'):
            try:
                result = db.search_items_dto(text)

                if result.is_empty():
                    # Отправляем сообщение об ошибке
                    await notification_service.notify(
                        chat_id=update.effective_chat.id,
                        text=format_not_found(text),
                    )
                    context.user_data['awaiting_menu_find'] = False
                    return

                await update.message.reply_text(
                    format_search_results(result),
                    reply_markup=get_main_menu_back_keyboard()
                )
                context.user_data['awaiting_menu_find'] = False
            except Exception as e:
                logger.error(f'Ошибка при поиске: {e}')
                await notification_service.notify(
                    chat_id=update.effective_chat.id,
                    text='❌ Ошибка при поиске',
                )
            return

        # Создание бокса
        if context.user_data.get('awaiting_box_create'):
            name = text.strip()

            existing = db.get_box_by_name(name)
            if existing:
                await notification_service.notify_error(
                    chat_id=update.effective_chat.id,
                    error=format_box_already_exists(name),
                )
                return

            db.create_box(name=name)

            boxes = db.get_all_boxes_dto()

            # Отправляем список боксов
            await update.message.reply_text(
                '📦 Выберите бокс для управления:',
                reply_markup=get_boxes_keyboard(boxes)
            )

            # Отправляем подтверждение через сервис уведомлений
            await notification_service.notify_success(
                chat_id=update.effective_chat.id,
                action=f'Бокс "{name}" создан',
            )

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

            box = db.get_box_dto_by_id(box_id)
            items = db.get_items_by_box_dto(box_id, box.name)

            # Экранируем HTML символы в названии предмета
            safe_item_name = item_name.replace('<', '&lt;').replace('>', '&gt;')

            # Отправляем меню бокса
            await update.message.reply_text(
                format_box_text(box, box.items_count),
                reply_markup=get_box_view_keyboard(box, items),
                parse_mode='HTML'
            )

            # Отправляем подтверждение через сервис уведомлений
            await notification_service.notify_success(
                chat_id=update.effective_chat.id,
                action=f'Предмет "{safe_item_name}" добавлен',
            )

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

            box = db.get_box_dto_by_id(box_id)
            items = db.get_items_by_box_dto(box_id, box.name)

            # Отправляем меню бокса
            await update.message.reply_text(
                format_box_text(box, box.items_count),
                reply_markup=get_box_view_keyboard(box, items),
                parse_mode='HTML'
            )

            # Отправляем подтверждение через сервис уведомлений
            await notification_service.notify_success(
                chat_id=update.effective_chat.id,
                action='Бокс переименован',
            )

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

            item = db.get_item_dto_by_id(item_id)
            box = db.get_box_dto_by_id(item.box_id)

            # Отправляем клавиатуру предмета
            await update.message.reply_text(
                format_item_text(item),
                reply_markup=get_item_keyboard(item, box),
                parse_mode='HTML'
            )

            # Отправляем подтверждение через сервис уведомлений
            await notification_service.notify_success(
                chat_id=update.effective_chat.id,
                action='Предмет переименован',
            )

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

            item = db.get_item_dto_by_id(item_id)
            box = db.get_box_dto_by_id(item.box_id)

            # Отправляем клавиатуру предмета
            await update.message.reply_text(
                format_item_text(item),
                reply_markup=get_item_keyboard(item, box),
                parse_mode='HTML'
            )

            # Отправляем подтверждение через сервис уведомлений
            await notification_service.notify_success(
                chat_id=update.effective_chat.id,
                action='Комментарий сохранён',
            )

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

        # Все остальные сообщения пользователя - middleware удалит автоматически

    return MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler)
