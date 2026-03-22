"""
Сервис уведомлений для бота
Аналогично реализации в Remnashop
"""
import asyncio
import logging
from typing import Optional, Union

from telegram import Bot, InlineKeyboardMarkup, Message, ReplyKeyboardMarkup

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Централизованный сервис отправки уведомлений
    
    Поддерживает:
    - Текстовые сообщения
    - Автоудаление через заданный интервал
    - Inline и Reply клавиатуры
    """
    
    def __init__(self, bot: Bot, default_auto_delete: int = 3):
        """
        Инициализация сервиса уведомлений
        
        Args:
            bot: Экземпляр бота
            default_auto_delete: Время автоудаления сообщений в секундах (по умолчанию 3)
        """
        self.bot = bot
        self.default_auto_delete = default_auto_delete
    
    async def notify(
        self,
        chat_id: int,
        text: str,
        reply_markup: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]] = None,
        auto_delete: Optional[int] = None,
        parse_mode: str = 'HTML',
    ) -> Optional[Message]:
        """
        Отправка уведомления пользователю
        
        Args:
            chat_id: ID чата для отправки
            text: Текст сообщения
            reply_markup: Клавиатура (опционально)
            auto_delete: Время автоудаления в секундах (None = использовать default_auto_delete)
            parse_mode: Режим парсинга ('HTML' или 'Markdown')
        
        Returns:
            Отправленное сообщение или None при ошибке
        """
        try:
            message = await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
            )
            
            # Планируем автоудаление если указано
            delete_delay = auto_delete if auto_delete is not None else self.default_auto_delete
            if delete_delay is not None and delete_delay > 0:
                asyncio.create_task(self._delete_later(message, delete_delay))
            
            return message
            
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления в чат {chat_id}: {e}")
            return None
    
    async def notify_callback(
        self,
        callback_message: Message,
        text: str,
        reply_markup: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]] = None,
        auto_delete: Optional[int] = None,
        parse_mode: str = 'HTML',
    ) -> Optional[Message]:
        """
        Отправка уведомления в ответ на callback-запрос
        
        Args:
            callback_message: Сообщение, из которого был вызван callback
            text: Текст сообщения
            reply_markup: Клавиатура (опционально)
            auto_delete: Время автоудаления в секундах
            parse_mode: Режим парсинга
        
        Returns:
            Отправленное сообщение или None при ошибке
        """
        return await self.notify(
            chat_id=callback_message.chat_id,
            text=text,
            reply_markup=reply_markup,
            auto_delete=auto_delete,
            parse_mode=parse_mode,
        )
    
    async def _delete_later(self, message: Message, delay: int):
        """
        Удаление сообщения через заданный интервал
        
        Args:
            message: Сообщение для удаления
            delay: Задержка в секундах перед удалением
        """
        await asyncio.sleep(delay)
        try:
            await message.delete()
            logger.debug(f"Сообщение {message.message_id} удалено через {delay} сек")
        except Exception as e:
            logger.debug(f"Не удалось удалить сообщение {message.message_id}: {e}")
    
    async def edit_message(
        self,
        message: Message,
        text: str,
        reply_markup: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]] = None,
        parse_mode: str = 'HTML',
    ) -> bool:
        """
        Редактирование существующего сообщения
        
        Args:
            message: Сообщение для редактирования
            text: Новый текст
            reply_markup: Новая клавиатура (опционально)
            parse_mode: Режим парсинга
        
        Returns:
            True если успешно, False при ошибке
        """
        try:
            await message.edit_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
            )
            return True
        except Exception as e:
            logger.debug(f"Ошибка редактирования сообщения: {e}")
            return False
    
    async def notify_success(
        self,
        chat_id: int,
        action: str,
        auto_delete: Optional[int] = None,
    ) -> Optional[Message]:
        """
        Отправка уведомления об успешном действии
        
        Args:
            chat_id: ID чата
            action: Описание действия (например, "Бокс создан")
            auto_delete: Время автоудаления
        
        Returns:
            Отправленное сообщение или None
        """
        return await self.notify(
            chat_id=chat_id,
            text=f'✅ {action}',
            auto_delete=auto_delete,
        )
    
    async def notify_error(
        self,
        chat_id: int,
        error: str,
        auto_delete: Optional[int] = None,
    ) -> Optional[Message]:
        """
        Отправка уведомления об ошибке
        
        Args:
            chat_id: ID чата
            error: Описание ошибки
            auto_delete: Время автоудаления
        
        Returns:
            Отправленное сообщение или None
        """
        return await self.notify(
            chat_id=chat_id,
            text=f'❌ {error}',
            auto_delete=auto_delete,
        )
