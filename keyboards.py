"""
Клавиатуры для бота
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
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


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура главного меню"""
    keyboard = [
        [InlineKeyboardButton('📦 Боксы', callback_data=MENU_BOX)],
        [InlineKeyboardButton('📑 Список предметов', callback_data=MENU_LIST)],
        [InlineKeyboardButton('🔍 Найти предмет', callback_data=MENU_FIND)]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_boxes_keyboard(boxes, items_counts=None, show_main_menu: bool = True) -> InlineKeyboardMarkup:
    """Клавиатура списка боксов
    
    Args:
        boxes: Список боксов
        items_counts: Словарь {box_id: count} с количеством предметов (опционально)
        show_main_menu: Показывать ли кнопку главного меню
    """
    keyboard = []
    for box in boxes:
        items_count = items_counts.get(box.id, 0) if items_counts else 0
        keyboard.append([
            InlineKeyboardButton(
                f'📦 {box.name} ({items_count})',
                callback_data=f'box_{box.id}'
            )
        ])
    
    keyboard.append([InlineKeyboardButton('➕ Создать бокс', callback_data=CREATE_BOX)])
    
    if show_main_menu:
        keyboard.append([InlineKeyboardButton('📋 Главное меню', callback_data=MENU_MAIN)])
    
    return InlineKeyboardMarkup(keyboard)


def get_box_view_keyboard(box, items) -> InlineKeyboardMarkup:
    """Клавиатура просмотра бокса"""
    keyboard = []
    
    # Кнопки предметов
    for item in items:
        keyboard.append([
            InlineKeyboardButton(item.name, callback_data=f'item_{item.id}')
        ])
    
    # Кнопки управления
    keyboard.append([
        InlineKeyboardButton('➕ Добавить предмет', callback_data=f'{ADD_ITEM_TO_BOX_PREFIX}{box.id}')
    ])
    keyboard.append([
        InlineKeyboardButton('✏️ Переименовать', callback_data=f'{EDIT_BOX_PREFIX}{box.id}'),
        InlineKeyboardButton('🗑️ Удалить', callback_data=f'{DELETE_BOX_PREFIX}{box.id}')
    ])
    keyboard.append([InlineKeyboardButton('⬅️ Назад', callback_data=BACK_TO_BOXES)])
    
    return InlineKeyboardMarkup(keyboard)


def get_item_keyboard(item, box) -> InlineKeyboardMarkup:
    """Клавиатура просмотра предмета"""
    keyboard = [
        [
            InlineKeyboardButton('✏️ Переименовать', callback_data=f'{EDIT_ITEM_PREFIX}{item.id}'),
            InlineKeyboardButton('🗑️ Удалить', callback_data=f'{DELETE_ITEM_PREFIX}{item.id}')
        ],
        [InlineKeyboardButton('📝 Комментарий', callback_data=f'{EDIT_ITEM_COMMENT_PREFIX}{item.id}')],
        [InlineKeyboardButton('⬅️ Назад к боксу', callback_data=f'box_{box.id}')]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_cancel_keyboard(callback_data: str) -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой отмены"""
    keyboard = [[InlineKeyboardButton('❌ Отмена', callback_data=callback_data)]]
    return InlineKeyboardMarkup(keyboard)


def get_back_keyboard(callback_data: str) -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой назад"""
    keyboard = [[InlineKeyboardButton('⬅️ Назад', callback_data=callback_data)]]
    return InlineKeyboardMarkup(keyboard)


def get_main_menu_back_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой главное меню"""
    keyboard = [[InlineKeyboardButton('📋 Главное меню', callback_data=MENU_MAIN)]]
    return InlineKeyboardMarkup(keyboard)


def get_delete_confirm_keyboard(confirm_data: str, cancel_data: str) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения удаления"""
    keyboard = [
        [
            InlineKeyboardButton('✅ Да, удалить', callback_data=confirm_data),
            InlineKeyboardButton('❌ Отмена', callback_data=cancel_data)
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_edit_item_keyboard(item_id: str) -> InlineKeyboardMarkup:
    """Клавиатура отмены редактирования предмета"""
    keyboard = [[InlineKeyboardButton('❌ Отмена', callback_data=CANCEL_EDIT_ITEM)]]
    return InlineKeyboardMarkup(keyboard)


def get_edit_box_keyboard(box_id: str) -> InlineKeyboardMarkup:
    """Клавиатура отмены редактирования бокса"""
    keyboard = [[InlineKeyboardButton('❌ Отмена', callback_data=CANCEL_EDIT_BOX)]]
    return InlineKeyboardMarkup(keyboard)


def get_add_item_keyboard(box_id: str) -> InlineKeyboardMarkup:
    """Клавиатура отмены добавления предмета"""
    keyboard = [[InlineKeyboardButton('❌ Отмена', callback_data=CANCEL_ADD_ITEM_TO_BOX)]]
    return InlineKeyboardMarkup(keyboard)


def get_create_box_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура отмены создания бокса"""
    keyboard = [[InlineKeyboardButton('❌ Отмена', callback_data=CANCEL_CREATE_BOX)]]
    return InlineKeyboardMarkup(keyboard)


def get_edit_comment_keyboard(item_id: str) -> InlineKeyboardMarkup:
    """Клавиатура редактирования комментария"""
    keyboard = [
        [InlineKeyboardButton('🗑️ Удалить комментарий', callback_data=f'{DELETE_ITEM_COMMENT_PREFIX}{item_id}')],
        [InlineKeyboardButton('❌ Отмена', callback_data=CANCEL_EDIT_ITEM_COMMENT)]
    ]
    return InlineKeyboardMarkup(keyboard)
