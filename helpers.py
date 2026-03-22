"""
Вспомогательные функции для бота
"""
import asyncio
import logging
from telegram import Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes
from config import Config

logger = logging.getLogger(__name__)


def check_authorization(update: Update) -> bool:
    """Проверка доступа пользователя"""
    if not Config.is_user_allowed(update.effective_user.id):
        return False
    return True


async def edit_safe(query, text, **kwargs):
    """Безопасное редактирование сообщения с обработкой ошибок"""
    try:
        await query.edit_message_text(text, **kwargs)
    except BadRequest as e:
        if 'Message' not in str(e):  # Игнорируем ошибки редактирования сообщения
            logger.warning(f'Ошибка редактирования: {e}')


async def delete_message(message, delay: int = 5):
    """Удаление сообщения через указанное количество секунд"""
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except Exception:
        pass


async def send_and_delete(message, text: str, delay: int = 5):
    """Отправляет сообщение и удаляет его через delay секунд"""
    msg = await message.reply_text(text)
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except Exception:
        pass


async def delete_user_message(update: Update, delay: int = 5):
    """Удаление сообщения пользователя через указанное количество секунд"""
    await asyncio.sleep(delay)
    try:
        await update.message.delete()
    except Exception:
        pass


async def delete_message_background(bot, chat_id: int, message_id: int, delay: int = 3):
    """Фоновое удаление сообщения через указанное количество секунд"""
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass
