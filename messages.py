"""
Форматирование сообщений для бота
"""
from dto import BoxDto, ItemDto, SearchResult


def format_box_text(box: BoxDto, items_count: int | None = None) -> str:
    """Форматирование информации о боксе
    
    Args:
        box: DTO бокса
        items_count: Количество предметов (если None, берётся из box.items_count)
    """
    # Экранируем HTML символы
    name = box.name.replace('<', '&lt;').replace('>', '&gt;')
    comment = box.comment.replace('<', '&lt;').replace('>', '&gt;') if box.comment else ''
    count = items_count if items_count is not None else box.items_count

    text = f'📦 <b>{name}</b>\n'
    if comment:
        text += f'Комментарий: {comment}\n'
    text += f'\nПредметов: {count}\n'
    return text


def format_item_text(item: ItemDto) -> str:
    """Форматирование информации о предмете
    
    Args:
        item: DTO предмета
    """
    # Экранируем HTML символы
    name = item.name.replace('<', '&lt;').replace('>', '&gt;')
    comment = item.comment.replace('<', '&lt;').replace('>', '&gt;') if item.comment else ''
    created_by = item.created_by.replace('<', '&lt;').replace('>', '&gt;') if item.created_by else ''

    text = f'📌 <b>{name}</b>\n'
    text += f'Бокс: {item.box_name}\n'
    if comment:
        text += f'Комментарий: {comment}\n'
    else:
        text += 'Комментарий: _нет_\n'
    if created_by:
        text += f'Создан: {created_by}\n'
    return text


def format_items_list(boxes: list[BoxDto], db=None) -> str:
    """Форматирование списка всех предметов по боксам

    Args:
        boxes: Список DTO боксов
        db: Экземпляр Database для получения предметов (опционально)
    """
    text = '📦 Все предметы по боксам:\n\n'
    for box in boxes:
        text += f'🗂️ {box.name}\n'
        if db and box.items_count > 0:
            items = db.get_items_by_box(box.id)
            if items:
                for item in items:
                    text += f'   📌 {item.name}\n'
            else:
                text += '   (пусто)\n'
        else:
            text += f'   ({box.items_count} предметов)\n'
        text += '\n'
    return text


def format_search_results(result: SearchResult) -> str:
    """Форматирование результатов поиска
    
    Args:
        result: SearchResult DTO
    """
    text = f'🔍 Найдено предметов: {result.total}\n'
    for item in result.items:
        if item.comment:
            text += f'🔧 {item.name} ({item.comment})\n'
        else:
            text += f'🔧 {item.name}\n'
        text += f'   📦 Бокс: {item.box_name}\n\n'
    return text


def format_welcome_text() -> str:
    """Текст приветственного сообщения"""
    return """
👋 Добро пожаловать в Vaultify!

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
