"""
Конвертеры для преобразования между моделями и DTO
"""
from models import Box, Item
from dto import BoxDto, ItemDto


def box_to_dto(box: Box, items_count: int = 0) -> BoxDto:
    """Конвертирует Box модель в BoxDto"""
    return BoxDto(
        id=box.id,
        name=box.name,
        comment=box.comment or "",
        items_count=items_count,
    )


def item_to_dto(item: Item, box_name: str = "") -> ItemDto:
    """Конвертирует Item модель в ItemDto"""
    # Парсим created_by для извлечения даты
    created_at = None
    if item.created_by:
        # Формат: "@username (2026-03-22 12:00)"
        try:
            start = item.created_by.rfind("(")
            end = item.created_by.rfind(")")
            if start != -1 and end != -1:
                created_at = item.created_by[start + 1:end].strip()
        except (ValueError, IndexError):
            pass
    
    return ItemDto(
        id=item.id,
        name=item.name,
        comment=item.comment or "",
        box_id=item.box_id,
        box_name=box_name,
        created_by=item.created_by or "",
        created_at=created_at,
    )


def boxes_to_dtos(boxes: list[Box], items_counts: dict[str, int] | None = None) -> list[BoxDto]:
    """Конвертирует список Box моделей в список BoxDto"""
    items_counts = items_counts or {}
    return [box_to_dto(box, items_counts.get(box.id, 0)) for box in boxes]


def items_to_dtos(items: list[Item], box_name: str = "") -> list[ItemDto]:
    """Конвертирует список Item моделей в список ItemDto"""
    return [item_to_dto(item, box_name) for item in items]
