"""
Вспомогательные функции для бота
"""
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
