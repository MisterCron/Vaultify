"""
Обработчик команды /cancel
"""
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from config import Config
from helpers import check_authorization
import asyncio


def create_cancel_handler(db):
    """Создаёт обработчик команды /cancel"""

    async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not check_authorization(update):
            msg = await update.message.reply_text('❌ Доступ запрещён')
            await asyncio.sleep(5)
            try:
                await msg.delete()
            except:
                pass
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

        msg = await update.message.reply_text('❌ Действие отменено')
        await asyncio.sleep(5)
        try:
            await msg.delete()
        except:
            pass

    return CommandHandler('cancel', cancel)
