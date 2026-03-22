"""
Обработчик для автоматического удаления сообщений пользователя
"""
import asyncio
import logging
from telegram import Update
from telegram.ext import MessageHandler, filters
from services.notification import NotificationService

logger = logging.getLogger(__name__)


def create_delete_user_message_handler(notification_service: NotificationService, delay: int = 5):
    """
    Создаёт обработчик для автоматического удаления сообщений пользователя
    
    Перехватывает все сообщения от пользователей и удаляет их через заданный интервал.
    Работает прозрачно для других обработчиков (группа -1).
    """
    
    async def delete_message(update: Update, context):
        """Просто планируем удаление сообщения"""
        message = update.message
        
        # Планируем удаление сообщения через заданный интервал
        asyncio.create_task(
            notification_service.delete_message(message, delay=delay)
        )
    
    # Фильтр: только сообщения от пользователей (не от ботов, не сервисные)
    msg_filter = filters.ALL & ~filters.StatusUpdate.ALL
    
    return MessageHandler(msg_filter, delete_message)
