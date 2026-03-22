"""
Vaultify — Система адресного хранения вещей
Telegram-бот для управления предметами и боксами с инвентарём
"""

import logging
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application
from telegram.error import TelegramError
from config import Config
from database import Database
from handlers import register_handlers

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logging.getLogger('httpx').setLevel(logging.WARNING)  # Отключаем логи HTTP-запросов
logger = logging.getLogger(__name__)


async def notify_admin(bot, db):
    """Отправка уведомления администратору о запуске бота"""
    if Config.BOT_DEV_ID:
        try:
            await bot.send_message(
                chat_id=Config.BOT_DEV_ID,
                text=f'✅ <b>Vaultify запущен!</b>\n\n🕐 Время: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                parse_mode='HTML'
            )
            logger.info(f'Уведомление отправлено администратору {Config.BOT_DEV_ID}')

            # Отправка меню /menu
            keyboard = [
                [InlineKeyboardButton('📦 Боксы', callback_data='menu_box')],
                [InlineKeyboardButton('📑 Список предметов', callback_data='menu_list')],
                [InlineKeyboardButton('🔍 Найти предмет', callback_data='menu_find')]
            ]

            await bot.send_message(
                chat_id=Config.BOT_DEV_ID,
                text='📋 Главное меню:',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except TelegramError as e:
            logger.warning(f'Не удалось отправить уведомление администратору: {e}')


async def run_bot():
    """Асинхронный запуск бота"""
    # Проверка конфигурации
    Config.validate()

    # Инициализация базы данных
    db_url = Config.DATABASE_URL
    logger.info(f'Использование БД: {db_url}')
    db = Database(db_url)

    # Создание приложения
    application = Application.builder().token(Config.BOT_TOKEN).build()

    # Регистрация обработчиков
    register_handlers(application, db)

    # Запуск бота и отправка уведомления
    logger.info('Бот запущен...')

    await application.initialize()
    await application.start()
    
    # Отправка уведомления администратору после запуска
    try:
        await notify_admin(application.bot, db)
    except Exception as e:
        logger.error(f'Ошибка при отправке уведомления: {e}')
    
    await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)

    # Keep running until stopped
    await asyncio.Event().wait()


def main():
    """Запуск бота"""
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info('Бот остановлен')


if __name__ == '__main__':
    main()