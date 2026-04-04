"""
Обработчики команд бота
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler
from database import Database
from config import Config
from constants import ADD_TO_BOX_PREFIX, CANCEL_ADD_ITEM, CREATE_BOX
from keyboards import get_main_menu_keyboard, get_boxes_keyboard
from messages import format_welcome_text, format_items_list, format_box_already_exists
from helpers import check_authorization
from services.notification import NotificationService
from dto import BoxDto
import asyncio
import shutil
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def create_start_handler(db: Database, notification_service: NotificationService = None):
    """Обработчик команды /start"""
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not check_authorization(update):
            await update.message.reply_text('❌ Доступ запрещён')
            return

        user_id = update.effective_user.id
        is_admin = str(user_id) == str(Config.BOT_DEV_ID)

        # Формируем текст приветствия
        welcome_text = format_welcome_text()
        if is_admin:
            welcome_text += '\n\n🔧 <b>Администратор:</b> Используйте /backup для создания бекапа БД'

        await update.message.reply_text(
            welcome_text,
            reply_markup=get_main_menu_keyboard(),
            parse_mode='HTML'
        )

    return CommandHandler('start', start)


def create_menu_handler(db: Database, notification_service: NotificationService = None):
    """Обработчик команды /menu"""
    async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not check_authorization(update):
            await update.message.reply_text('❌ Доступ запрещён')
            return

        await update.message.reply_text(
            '📋 Главное меню:',
            reply_markup=get_main_menu_keyboard()
        )

    return CommandHandler('menu', menu)


def create_add_handler(db: Database, notification_service: NotificationService = None):
    """Обработчик команды /add"""
    async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not check_authorization(update):
            await update.message.reply_text('❌ Доступ запрещён')
            return

        if not context.args:
            await update.message.reply_text(
                '❌ Неверный формат.\nИспользуйте: /add <название>\n\nПример: /add Молоток'
            )
            return

        item_name = ' '.join(context.args)
        context.user_data['add_item_name'] = item_name
        context.user_data['awaiting_box_select'] = True

        boxes = db.get_all_boxes()
        if not boxes:
            await update.message.reply_text(
                '📦 Нет созданных боксов.\nСначала создайте бокс через /newbox'
            )
            context.user_data['awaiting_box_select'] = False
            return

        keyboard = []
        for box in boxes:
            keyboard.append([
                InlineKeyboardButton(f'📦 {box.name}', callback_data=f'{ADD_TO_BOX_PREFIX}{box.id}')
            ])
        keyboard.append([InlineKeyboardButton('❌ Отмена', callback_data=CANCEL_ADD_ITEM)])

        await update.message.reply_text(
            f'📝 Выберите бокс для предмета "{item_name}":',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    return CommandHandler('add', add)


def create_find_handler(db: Database, notification_service: NotificationService = None):
    """Обработчик команды /find"""
    async def find(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not check_authorization(update):
            await update.message.reply_text('❌ Доступ запрещён')
            return

        if not context.args:
            await update.message.reply_text('❌ Укажите название для поиска.\nПример: /find молоток')
            return

        from messages import format_not_found, format_search_results

        query = ' '.join(context.args)
        items = db.search_items(query)

        if not items:
            await update.message.reply_text(format_not_found(query))
            return

        await update.message.reply_text(format_search_results(items, db))

    return CommandHandler('find', find)


def create_list_handler(db: Database, notification_service: NotificationService = None):
    """Обработчик команды /list"""
    async def list_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not check_authorization(update):
            await update.message.reply_text('❌ Доступ запрещён')
            return

        boxes = db.get_all_boxes_dto()

        if not boxes:
            await update.message.reply_text('📭 Нет созданных боксов')
            return

        await update.message.reply_text(format_items_list(boxes, db))

    return CommandHandler('list', list_items)


def create_newbox_handler(db: Database, notification_service: NotificationService = None):
    """Обработчик команды /newbox для создания бокса"""
    async def newbox(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not check_authorization(update):
            await update.message.reply_text('❌ Доступ запрещён')
            return

        if not context.args:
            await update.message.reply_text(
                '❌ Неверный формат.\nИспользуйте: /newbox <название>\n\nПример: /newbox Инструменты'
            )
            return

        name = ' '.join(context.args)

        existing = db.get_box_by_name(name)
        if existing:
            await update.message.reply_text(format_box_already_exists(name))
            return

        db.create_box(name=name)
        await update.message.reply_text(f'✅ Бокс "{name}" создан!')

    return CommandHandler('newbox', newbox)


def create_box_handler(db: Database, notification_service: NotificationService = None):
    """Обработчик команды /box с inline-кнопками"""
    async def box_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not check_authorization(update):
            await update.message.reply_text('❌ Доступ запрещён')
            return

        boxes = db.get_all_boxes_dto()

        if not boxes:
            await update.message.reply_text(
                '📦 Нет созданных боксов.\nСначала создайте бокс через /newbox'
            )
            return

        await update.message.reply_text(
            '📦 Выберите бокс для управления:',
            reply_markup=get_boxes_keyboard(boxes, show_main_menu=False)
        )

    return CommandHandler('box', box_menu)


def create_backup_handler(db: Database, notification_service: NotificationService = None):
    """Обработчик команды /backup для создания бекапа базы данных"""
    async def backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Проверка прав администратора
        user_id = update.effective_user.id
        if str(user_id) != str(Config.BOT_DEV_ID):
            await update.message.reply_text('❌ Эта команда доступна только администратору')
            return

        try:
            await update.message.reply_text('⏳ Создание бекапа базы данных...')

            # Получаем путь к базе данных из конфигурации
            db_url = Config.DATABASE_URL
            
            # Обрабатываем SQLite URL (формат: sqlite:///path/to/db.sqlite)
            if db_url.startswith('sqlite:///'):
                db_path = db_url.replace('sqlite:///', '')
                # Для абсолютных путей в Unix (начинаются с /)
                if not os.path.isabs(db_path):
                    db_path = os.path.abspath(db_path)
                
                if not os.path.exists(db_path):
                    await update.message.reply_text('❌ Файл базы данных не найден')
                    return

                # Создаём временную копию базы данных
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_filename = f'vaultify_backup_{timestamp}.db'
                backup_path = os.path.join('/tmp', backup_filename)
                
                # Копируем файл базы данных
                shutil.copy2(db_path, backup_path)
                
                # Отправляем файл пользователю
                with open(backup_path, 'rb') as db_file:
                    await update.message.reply_document(
                        document=db_file,
                        filename=backup_filename,
                        caption=f'✅ Бекап базы данных создан\n📅 Дата: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n📦 Размер: {os.path.getsize(backup_path) / 1024:.2f} КБ'
                    )
                
                # Удаляем временный файл
                os.remove(backup_path)
                
                logger.info(f'Бекап создан: {backup_filename} пользователем {user_id}')
                
            else:
                # Для других типов БД (PostgreSQL и т.д.)
                await update.message.reply_text(
                    '❌ Бекап поддерживается только для SQLite баз данных.\n'
                    f'Текущий тип БД: {db_url.split(":")[0]}'
                )

        except Exception as e:
            logger.error(f'Ошибка при создании бекапа: {e}')
            await update.message.reply_text(f'❌ Ошибка при создании бекапа: {str(e)}')

    return CommandHandler('backup', backup)
