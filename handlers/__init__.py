"""
Модуль обработчиков бота
"""
from .commands import (
    create_start_handler,
    create_menu_handler,
    create_add_handler,
    create_find_handler,
    create_list_handler,
    create_newbox_handler,
    create_box_handler,
)
from .callbacks import create_callback_handler
from .user_messages import create_user_message_handler
from .cancel import create_cancel_handler


def register_handlers(application, db):
    """Регистрация всех обработчиков"""
    application.add_handler(create_start_handler(db))
    application.add_handler(create_menu_handler(db))
    application.add_handler(create_add_handler(db))
    application.add_handler(create_find_handler(db))
    application.add_handler(create_list_handler(db))
    application.add_handler(create_newbox_handler(db))
    application.add_handler(create_box_handler(db))
    application.add_handler(create_callback_handler(db))
    application.add_handler(create_user_message_handler(db))
    application.add_handler(create_cancel_handler(db))
