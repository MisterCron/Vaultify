"""
Обработчик команды /cancel
"""
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from config import Config
from helpers import check_authorization
from services.notification import NotificationService


def create_cancel_handler(db, notification_service: NotificationService):
    """Создаёт обработчик команды /cancel"""

    async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not check_authorization(update):
            await notification_service.notify(
                chat_id=update.effective_chat.id,
                text='❌ Доступ запрещён',
            )
            return

        context.user_data['awaiting_box_create'] = False
        context.user_data['awaiting_box_edit'] = False
        context.user_data['edit_box_id'] = None
        context.user_data['edit_box_request_message_id'] = None
        context.user_data['awaiting_item_edit'] = False
        context.user_data['edit_item_id'] = None
        context.user_data['awaiting_item_comment_edit'] = False
        context.user_data['edit_item_comment_id'] = None
        context.user_data['edit_item_comment_request_message_id'] = None
        context.user_data['edit_item_box_id'] = None
        context.user_data['add_item_name'] = None
        context.user_data['awaiting_box_select'] = False
        context.user_data['awaiting_menu_find'] = False

        await notification_service.notify(
            chat_id=update.effective_chat.id,
            text='❌ Действие отменено',
        )

    return CommandHandler('cancel', cancel)
