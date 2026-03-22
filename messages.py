"""
Форматирование сообщений для бота
"""


def format_box_text(box, items_count: int) -> str:
    """Форматирование информации о боксе"""
    # Экранируем HTML символы
    name = box.name.replace('<', '&lt;').replace('>', '&gt;')
    comment = box.comment.replace('<', '&lt;').replace('>', '&gt;') if box.comment else ''
    
    text = f'📦 <b>{name}</b>\n'
    if comment:
        text += f'Комментарий: {comment}\n'
    text += f'\nПредметов: {items_count}\n'
    return text


def format_item_text(item, box) -> str:
    """Форматирование информации о предмете"""
    # Экранируем HTML символы
    name = item.name.replace('<', '&lt;').replace('>', '&gt;')
    comment = item.comment.replace('<', '&lt;').replace('>', '&gt;') if item.comment else ''
    created_by = item.created_by.replace('<', '&lt;').replace('>', '&gt;') if item.created_by else ''
    
    text = f'📌 <b>{name}</b>\n'
    text += f'Бокс: {box.name}\n'
    if comment:
        text += f'Комментарий: {comment}\n'
    else:
        text += 'Комментарий: _нет_\n'
    if created_by:
        text += f'Создан: {created_by}\n'
    return text


def format_items_list(boxes, db=None) -> str:
    """Форматирование списка всех предметов по боксам
    
    Args:
        boxes: Список боксов
        db: Экземпляр Database для получения предметов (опционально)
    """
    text = '📦 Все предметы по боксам:\n\n'
    for box in boxes:
        items = db.get_items_by_box(box.id) if db else []
        text += f'🗂️ {box.name}\n'
        if items:
            for item in items:
                text += f'   {item.name}\n'
        else:
            text += '   (пусто)\n'
        text += '\n'
    return text


def format_search_results(items, db) -> str:
    """Форматирование результатов поиска"""
    text = f'🔍 Найдено предметов: {len(items)}\n'
    for item in items:
        box = db.get_box_by_id(item.box_id)
        if item.comment:
            text += f'🔧 {item.name} ({item.comment})\n'
        else:
            text += f'🔧 {item.name}\n'
        text += f'   📦 Бокс: {box.name}\n\n'
    return text


def format_welcome_text() -> str:
    """Текст приветственного сообщения"""
    return """
👋 Добро пожаловать в Inventory Bot!

📋 Основные команды:

➕ Добавить предмет
/add <название> — выберите бокс через меню

🔍 Найти предмет
/find <название> — быстрый поиск

📦 Управление боксами
/box — открыть интерактивный список

📑 Просмотр всего списка
/list — все предметы по боксам

🆕 Создать бокс
/newbox <название>

❌ Отмена действия
/cancel
    """.strip()


def format_delete_box_warning(items_count: int) -> str:
    """Предупреждение об удалении бокса с предметами"""
    if items_count > 0:
        return f'\n\n⚠️ В боксе находится {items_count} предмет(ов).\nВсе предметы будут удалены!'
    return ''


def format_item_already_exists(item_name: str, box_name: str) -> str:
    """Сообщение о том, что предмет уже существует"""
    return f'❌ Предмет "{item_name}" уже существует в боксе "{box_name}"'


def format_box_already_exists(name: str) -> str:
    """Сообщение о том, что бокс уже существует"""
    return f'❌ Бокс с названием "{name}" уже существует'


def format_not_found(query: str, item_type: str = 'предметы') -> str:
    """Сообщение о том, что ничего не найдено"""
    return f'❌ {item_type.capitalize()} с "{query}" не найдены'
