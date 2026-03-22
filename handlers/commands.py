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


def create_start_handler(db: Database, notification_service: NotificationService = None):
    """Обработчик команды /start"""
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not check_authorization(update):
            await update.message.reply_text('❌ Доступ запрещён')
            return

        await update.message.reply_text(
            format_welcome_text(),
            reply_markup=get_main_menu_keyboard()
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
            asyncio.create_task(notification_service.delete_message(update.message, delay=5))
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
            asyncio.create_task(notification_service.delete_message(update.message, delay=5))
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

        asyncio.create_task(notification_service.delete_message(update.message, delay=5))

    return CommandHandler('add', add)


def create_find_handler(db: Database, notification_service: NotificationService = None):
    """Обработчик команды /find"""
    async def find(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not check_authorization(update):
            await update.message.reply_text('❌ Доступ запрещён')
            return

        if not context.args:
            await update.message.reply_text('❌ Укажите название для поиска.\nПример: /find молоток')
            asyncio.create_task(notification_service.delete_message(update.message, delay=5))
            return

        from messages import format_not_found, format_search_results

        query = ' '.join(context.args)
        items = db.search_items(query)

        if not items:
            await update.message.reply_text(format_not_found(query))
            asyncio.create_task(notification_service.delete_message(update.message, delay=5))
            return

        await update.message.reply_text(format_search_results(items, db))
        asyncio.create_task(notification_service.delete_message(update.message, delay=5))

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

        await update.message.reply_text(format_items_list(boxes))
        asyncio.create_task(notification_service.delete_message(update.message, delay=5))

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
            asyncio.create_task(notification_service.delete_message(update.message, delay=5))
            return

        name = ' '.join(context.args)

        existing = db.get_box_by_name(name)
        if existing:
            await update.message.reply_text(format_box_already_exists(name))
            asyncio.create_task(notification_service.delete_message(update.message, delay=5))
            return

        db.create_box(name=name)
        await update.message.reply_text(f'✅ Бокс "{name}" создан!')
        asyncio.create_task(notification_service.delete_message(update.message, delay=5))

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
        asyncio.create_task(notification_service.delete_message(update.message, delay=5))

    return CommandHandler('box', box_menu)
