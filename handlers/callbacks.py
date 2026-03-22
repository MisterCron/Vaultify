"""
Callback обработчики inline-кнопок
"""
from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from telegram.error import BadRequest
from database import Database
from config import Config
from constants import (
    MENU_BOX, MENU_LIST, MENU_FIND, MENU_MAIN,
    BACK_TO_BOXES, CREATE_BOX, CANCEL_CREATE_BOX,
    EDIT_BOX_PREFIX, CANCEL_EDIT_BOX,
    DELETE_BOX_PREFIX, DELETE_BOX_CONFIRM_PREFIX,
    ADD_ITEM_TO_BOX_PREFIX, ADD_TO_BOX_PREFIX,
    CANCEL_ADD_ITEM, CANCEL_ADD_ITEM_TO_BOX,
    EDIT_ITEM_PREFIX, EDIT_ITEM_COMMENT_PREFIX,
    CANCEL_EDIT_ITEM, CANCEL_EDIT_ITEM_COMMENT,
    DELETE_ITEM_PREFIX, DELETE_ITEM_CONFIRM_PREFIX, DELETE_ITEM_COMMENT_PREFIX,
)
from keyboards import (
    get_main_menu_keyboard,
    get_boxes_keyboard,
    get_box_view_keyboard,
    get_item_keyboard,
    get_create_box_keyboard,
    get_add_item_keyboard,
    get_edit_box_keyboard,
    get_edit_item_keyboard,
    get_edit_comment_keyboard,
    get_delete_confirm_keyboard,
    get_main_menu_back_keyboard,
)
from messages import format_box_text, format_item_text, format_items_list, format_delete_box_warning
from helpers import edit_safe
from services.notification import NotificationService
from dto import BoxDto, ItemDto
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def create_callback_handler(db: Database, notification_service: NotificationService):
    """Создаёт обработчик callback-запросов"""

    async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query

        try:
            await query.answer()
        except BadRequest as e:
            if 'Query is too old' in str(e):
                logger.warning('Callback query слишком стар')
                return
            raise

        # Проверка авторизации для callback
        if not Config.is_user_allowed(query.from_user.id):
            await edit_safe(query, '❌ Доступ запрещён')
            return

        data = query.data
        logger.info(f'Callback received: {data}')

        # Меню - Боксы
        if data == MENU_BOX:
            boxes = db.get_all_boxes_dto()
            await edit_safe(
                query,
                '📦 Выберите бокс для управления:',
                reply_markup=get_boxes_keyboard(boxes)
            )

        # Меню - Список предметов
        elif data == MENU_LIST:
            boxes = db.get_all_boxes_dto()
            if boxes:
                await edit_safe(
                    query,
                    format_items_list(boxes),
                    reply_markup=get_main_menu_back_keyboard()
                )
            else:
                await edit_safe(
                    query,
                    '📑 Список предметов пуст.\n\nСначала создайте бокс и добавьте предметы.',
                    reply_markup=get_main_menu_back_keyboard()
                )

        # Меню - Найти предмет
        elif data == MENU_FIND:
            await edit_safe(
                query,
                '🔍 Введите название предмета для поиска:\n\nПример: молоток',
                reply_markup=get_main_menu_back_keyboard()
            )
            context.user_data['awaiting_menu_find'] = True

        # Главное меню
        elif data == MENU_MAIN:
            await edit_safe(
                query,
                '📋 Главное меню:',
                reply_markup=get_main_menu_keyboard()
            )

        # Список боксов
        elif data == BACK_TO_BOXES:
            boxes = db.get_all_boxes_dto()
            await edit_safe(
                query,
                '📦 Выберите бокс для управления:',
                reply_markup=get_boxes_keyboard(boxes)
            )

        # Создание бокса
        elif data == CREATE_BOX:
            await edit_safe(
                query,
                '📝 Введите название для нового бокса:\n\nПример: Инструменты',
                reply_markup=get_create_box_keyboard()
            )
            context.user_data['awaiting_box_create'] = True

        # Добавление предмета в бокс (кнопка в меню бокса)
        elif data.startswith(ADD_ITEM_TO_BOX_PREFIX):
            box_id = data.split('_', 4)[4]
            box = db.get_box_by_id(box_id)
            context.user_data['add_item_box_id'] = box_id
            context.user_data['awaiting_item_name'] = True
            context.user_data['item_request_message_id'] = query.message.message_id

            await edit_safe(
                query,
                f'📝 Введите название предмета для бокса «{box.name}»:',
                reply_markup=get_add_item_keyboard(box_id)
            )

        # Добавление предмета в бокс (из команды /add)
        elif data.startswith(ADD_TO_BOX_PREFIX):
            box_id = data.split('_', 3)[3]
            item_name = context.user_data.get('add_item_name')

            if item_name:
                box = db.get_box_by_id(box_id)
                # existing_items = db.get_items_by_box(box_id)

                # if any(item.name == item_name for item in existing_items):
                #     from messages import format_item_already_exists
                #     await edit_safe(query, format_item_already_exists(item_name, box.name))
                #     context.user_data['add_item_name'] = None
                #     context.user_data['awaiting_box_select'] = False
                #     return

                user = query.from_user
                username = user.username
                user_display = f'@{username}' if username else (user.first_name or str(user.id))
                created_at = datetime.now().strftime('%Y-%m-%d %H:%M')
                created_by = f'{user_display} ({created_at})'

                db.create_item(name=item_name, box_id=box_id, created_by=created_by)

                # Экранируем HTML символы в названии предмета
                safe_item_name = item_name.replace('<', '&lt;').replace('>', '&gt;')

                # Возвращаемся к меню боксов
                boxes = db.get_all_boxes_dto()
                await edit_safe(
                    query,
                    '📦 Выберите бокс для управления:',
                    reply_markup=get_boxes_keyboard(boxes)
                )

                # Отправляем подтверждение через сервис уведомлений
                await notification_service.notify_success(
                    chat_id=query.message.chat_id,
                    action=f'Предмет "{safe_item_name}" добавлен в бокс "{box.name}"',
                )

                context.user_data['add_item_name'] = None
                context.user_data['awaiting_box_select'] = False
            else:
                await edit_safe(query, '❌ Ошибка: название предмета не найдено')

        # Отмена добавления предмета
        elif data == CANCEL_ADD_ITEM:
            await edit_safe(query, '❌ Добавление предмета отменено')
            context.user_data['add_item_name'] = None
            context.user_data['awaiting_box_select'] = False

        # Просмотр бокса
        elif data.startswith('box_'):
            box_id = data.split('_', 1)[1]
            box = db.get_box_dto_by_id(box_id)
            items = db.get_items_by_box_dto(box_id, box.name if box else "")

            await edit_safe(
                query,
                format_box_text(box, box.items_count),
                reply_markup=get_box_view_keyboard(box, items),
                parse_mode='HTML'
            )

        # Просмотр предмета
        elif data.startswith('item_'):
            item_id = data.split('_', 1)[1]
            item = db.get_item_dto_by_id(item_id)
            box = db.get_box_dto_by_id(item.box_id)

            await edit_safe(
                query,
                format_item_text(item),
                reply_markup=get_item_keyboard(item, box),
                parse_mode='HTML'
            )

        # Редактирование бокса
        elif data.startswith(EDIT_BOX_PREFIX):
            box_id = data.split('_', 2)[2]
            box = db.get_box_by_id(box_id)
            context.user_data['edit_box_id'] = box_id
            context.user_data['awaiting_box_edit'] = True
            context.user_data['edit_box_request_message_id'] = query.message.message_id

            await edit_safe(
                query,
                f'📝 Введите новое название для бокса «{box.name}»:',
                reply_markup=get_edit_box_keyboard(box_id)
            )

        # Редактирование предмета
        elif data.startswith(EDIT_ITEM_PREFIX) and not data.startswith(EDIT_ITEM_COMMENT_PREFIX):
            item_id = data.split('_', 2)[2]
            item = db.get_item_by_id(item_id)
            context.user_data['edit_item_id'] = item_id
            context.user_data['awaiting_item_edit'] = True
            context.user_data['edit_item_box_id'] = item.box_id
            context.user_data['edit_item_request_message_id'] = query.message.message_id

            await edit_safe(
                query,
                f'📝 Введите новое название для предмета «{item.name}»:',
                reply_markup=get_edit_item_keyboard(item_id)
            )

        # Редактирование комментария предмета
        elif data.startswith(EDIT_ITEM_COMMENT_PREFIX):
            item_id = data.split('_', 3)[3]
            item = db.get_item_by_id(item_id)
            context.user_data['edit_item_comment_id'] = item_id
            context.user_data['awaiting_item_comment_edit'] = True
            context.user_data['edit_item_box_id'] = item.box_id
            context.user_data['edit_item_comment_request_message_id'] = query.message.message_id

            await edit_safe(
                query,
                f'📝 Введите комментарий для предмета «{item.name}»:',
                reply_markup=get_edit_comment_keyboard(item_id),
                parse_mode='HTML'
            )

        # Удаление предмета (подтверждение)
        elif data.startswith(DELETE_ITEM_PREFIX) and not data.startswith(DELETE_ITEM_CONFIRM_PREFIX) and not data.startswith(DELETE_ITEM_COMMENT_PREFIX):
            item_id = data.split('_', 2)[2]
            item = db.get_item_by_id(item_id)

            if not item:
                await edit_safe(query, '❌ Предмет не найден')
                return

            await edit_safe(
                query,
                f'⚠️ Вы уверены, что хотите удалить предмет «{item.name}»?\n\nЭто действие нельзя отменить.',
                reply_markup=get_delete_confirm_keyboard(
                    f'{DELETE_ITEM_CONFIRM_PREFIX}{item_id}',
                    f'item_{item_id}'
                ),
                parse_mode='HTML'
            )

        # Подтверждение удаления предмета
        elif data.startswith(DELETE_ITEM_CONFIRM_PREFIX):
            item_id = data.split('_', 3)[3]
            item = db.get_item_by_id(item_id)

            if not item:
                await edit_safe(query, '❌ Предмет не найден')
                return

            box_id = item.box_id
            db.delete_item(item_id)

            # Возвращаемся к боксу
            box = db.get_box_dto_by_id(box_id)
            items = db.get_items_by_box_dto(box_id, box.name if box else "")

            # Редактируем сообщение с клавиатурой бокса
            await edit_safe(
                query,
                format_box_text(box, box.items_count),
                reply_markup=get_box_view_keyboard(box, items),
                parse_mode='HTML'
            )

            # Отправляем подтверждение через сервис уведомлений
            await notification_service.notify(
                chat_id=query.message.chat_id,
                text='🗑️ Предмет удалён',
            )

        # Удаление бокса (подтверждение)
        elif data.startswith(DELETE_BOX_PREFIX) and not data.startswith(DELETE_BOX_CONFIRM_PREFIX):
            box_id = data.split('_', 2)[2]
            box = db.get_box_by_id(box_id)

            if not box:
                await edit_safe(query, '❌ Бокс не найден')
                return

            items_count = len(db.get_items_by_box(box_id))
            warning = format_delete_box_warning(items_count)

            await edit_safe(
                query,
                f'⚠️ Вы уверены, что хотите удалить бокс «{box.name}»?{warning}\n\nЭто действие нельзя отменить.',
                reply_markup=get_delete_confirm_keyboard(
                    f'{DELETE_BOX_CONFIRM_PREFIX}{box_id}',
                    BACK_TO_BOXES
                ),
                parse_mode='HTML'
            )

        # Подтверждение удаления бокса
        elif data.startswith(DELETE_BOX_CONFIRM_PREFIX):
            box_id = data.split('_', 3)[3]
            box = db.get_box_by_id(box_id)

            if not box:
                await edit_safe(query, '❌ Бокс не найден')
                return

            db.delete_box(box_id)

            # Возвращаемся к списку боксов
            boxes = db.get_all_boxes_dto()

            # Редактируем сообщение с клавиатурой списка боксов
            await edit_safe(
                query,
                '📦 Выберите бокс для управления:',
                reply_markup=get_boxes_keyboard(boxes)
            )

            # Отправляем подтверждение через сервис уведомлений
            await notification_service.notify(
                chat_id=query.message.chat_id,
                text='🗑️ Бокс удалён',
            )

        # Отмена редактирования бокса
        elif data == CANCEL_EDIT_BOX:
            box_id = context.user_data.get('edit_box_id')
            if box_id:
                box = db.get_box_dto_by_id(box_id)
                items = db.get_items_by_box_dto(box_id, box.name if box else "")
                await edit_safe(
                    query,
                    format_box_text(box, box.items_count),
                    reply_markup=get_box_view_keyboard(box, items),
                    parse_mode='HTML'
                )
            context.user_data['edit_box_id'] = None
            context.user_data['edit_box_request_message_id'] = None
            context.user_data['awaiting_box_edit'] = False

        # Отмена редактирования предмета
        elif data == CANCEL_EDIT_ITEM:
            item_id = context.user_data.get('edit_item_id')
            if item_id:
                item = db.get_item_dto_by_id(item_id)
                box = db.get_box_dto_by_id(item.box_id)
                await edit_safe(
                    query,
                    format_item_text(item),
                    reply_markup=get_item_keyboard(item, box),
                    parse_mode='HTML'
                )
            else:
                box_id = context.user_data.get('edit_item_box_id')
                if box_id:
                    box = db.get_box_dto_by_id(box_id)
                    items = db.get_items_by_box_dto(box_id, box.name if box else "")
                    await edit_safe(
                        query,
                        format_box_text(box, box.items_count),
                        reply_markup=get_box_view_keyboard(box, items),
                        parse_mode='HTML'
                    )
            context.user_data['edit_item_id'] = None
            context.user_data['edit_item_box_id'] = None
            context.user_data['edit_item_request_message_id'] = None
            context.user_data['awaiting_item_edit'] = False

        # Удаление комментария предмета
        elif data.startswith(DELETE_ITEM_COMMENT_PREFIX):
            item_id = data.replace('delete_item_comment_', '', 1)
            item = db.get_item_dto_by_id(item_id)

            if not item:
                await edit_safe(query, f'❌ Предмет не найден (id={item_id})')
                return

            db.update_item(item_id=item_id, comment='')

            # Получаем обновлённый предмет
            item = db.get_item_dto_by_id(item_id)
            box = db.get_box_dto_by_id(item.box_id)

            # Редактируем сообщение с меню предмета
            await edit_safe(
                query,
                format_item_text(item),
                reply_markup=get_item_keyboard(item, box),
                parse_mode='HTML'
            )

            # Отправляем подтверждение через сервис уведомлений
            await notification_service.notify(
                chat_id=query.message.chat_id,
                text='✅ Комментарий удалён!',
            )

            context.user_data['edit_item_comment_id'] = None
            context.user_data['edit_item_box_id'] = None
            context.user_data['awaiting_item_comment_edit'] = False

        # Отмена редактирования комментария предмета
        elif data == CANCEL_EDIT_ITEM_COMMENT:
            item_id = context.user_data.get('edit_item_comment_id')
            if item_id:
                item = db.get_item_dto_by_id(item_id)
                box = db.get_box_dto_by_id(item.box_id)
                await edit_safe(
                    query,
                    format_item_text(item),
                    reply_markup=get_item_keyboard(item, box),
                    parse_mode='HTML'
                )
            else:
                box_id = context.user_data.get('edit_item_box_id')
                if box_id:
                    box = db.get_box_dto_by_id(box_id)
                    items = db.get_items_by_box_dto(box_id, box.name if box else "")
                    await edit_safe(
                        query,
                        format_box_text(box, box.items_count),
                        reply_markup=get_box_view_keyboard(box, items),
                        parse_mode='HTML'
                    )
            context.user_data['edit_item_comment_id'] = None
            context.user_data['edit_item_comment_request_message_id'] = None
            context.user_data['edit_item_box_id'] = None
            context.user_data['awaiting_item_comment_edit'] = False

        # Отмена создания бокса
        elif data == CANCEL_CREATE_BOX:
            boxes = db.get_all_boxes()
            items_counts = {box.id: len(db.get_items_by_box(box.id)) for box in boxes}
            await edit_safe(
                query,
                '📦 Выберите бокс для управления:',
                reply_markup=get_boxes_keyboard(boxes, items_counts)
            )
            context.user_data['awaiting_box_create'] = False

        # Отмена добавления предмета
        elif data == CANCEL_ADD_ITEM_TO_BOX:
            box_id = context.user_data.get('add_item_box_id')
            if box_id:
                box = db.get_box_dto_by_id(box_id)
                items = db.get_items_by_box_dto(box_id, box.name if box else "")
                await edit_safe(
                    query,
                    format_box_text(box, box.items_count),
                    reply_markup=get_box_view_keyboard(box, items),
                    parse_mode='HTML'
                )
            context.user_data['awaiting_item_name'] = False
            context.user_data['add_item_box_id'] = None
            context.user_data['item_request_message_id'] = None

    return CallbackQueryHandler(callback_handler)
