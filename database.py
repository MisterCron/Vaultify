from sqlalchemy import create_engine, func, or_
from sqlalchemy.orm import sessionmaker
from models import Box, Item, Base
from dto import BoxDto, ItemDto, SearchResult, BoxWithItems
from dto.converters import box_to_dto, item_to_dto, boxes_to_dtos, items_to_dtos


class Database:
    """Класс для работы с базой данных"""

    def __init__(self, db_url: str = 'sqlite:///vaultify.db'):
        self.engine = create_engine(db_url, echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self._boxes_cache: list[Box] | None = None
        self._items_cache: dict[str, list[Item]] = {}

    def get_session(self):
        return self.Session()

    def clear_cache(self):
        """Очистка кэша"""
        self._boxes_cache = None
        self._items_cache = {}

    # Box operations
    def create_box(self, name: str, comment: str = '') -> Box:
        session = self.get_session()
        try:
            box = Box(name=name, comment=comment)
            session.add(box)
            session.commit()
            session.refresh(box)
            self.clear_cache()
            return box
        finally:
            session.close()

    def get_all_boxes(self) -> list[Box]:
        if self._boxes_cache is not None:
            return self._boxes_cache

        session = self.get_session()
        try:
            self._boxes_cache = session.query(Box).order_by(func.lower(Box.name)).all()
            return self._boxes_cache
        finally:
            session.close()

    def get_all_boxes_dto(self) -> list[BoxDto]:
        """Получить все боксы как DTO"""
        boxes = self.get_all_boxes()
        items_counts = {box.id: self.get_items_count(box.id) for box in boxes}
        return boxes_to_dtos(boxes, items_counts)

    def get_box_by_id(self, box_id: str) -> Box | None:
        session = self.get_session()
        try:
            return session.query(Box).filter(Box.id == box_id).first()
        finally:
            session.close()

    def get_box_dto_by_id(self, box_id: str) -> BoxDto | None:
        """Получить бокс как DTO"""
        box = self.get_box_by_id(box_id)
        if not box:
            return None
        items_count = self.get_items_count(box_id)
        return box_to_dto(box, items_count)

    def get_box_by_name(self, name: str) -> Box | None:
        session = self.get_session()
        try:
            return session.query(Box).filter(Box.name == name).first()
        finally:
            session.close()

    def update_box(self, box_id: str, name: str = None, comment: str = None) -> Box | None:
        session = self.get_session()
        try:
            box = session.query(Box).filter(Box.id == box_id).first()
            if box:
                if name:
                    box.name = name
                if comment is not None:
                    box.comment = comment
                session.commit()
                session.refresh(box)
                self.clear_cache()
            return box
        finally:
            session.close()

    def delete_box(self, box_id: str) -> bool:
        session = self.get_session()
        try:
            box = session.query(Box).filter(Box.id == box_id).first()
            if box:
                session.delete(box)
                session.commit()
                self.clear_cache()
                return True
            return False
        finally:
            session.close()

    # Item operations
    def create_item(self, name: str, box_id: str, comment: str = '', created_by: str = '') -> Item:
        session = self.get_session()
        try:
            item = Item(name=name, box_id=box_id, comment=comment, created_by=created_by)
            session.add(item)
            session.commit()
            session.refresh(item)
            self._items_cache.pop(box_id, None)
            return item
        finally:
            session.close()

    def get_items_by_box(self, box_id: str) -> list[Item]:
        if box_id in self._items_cache:
            return self._items_cache[box_id]

        session = self.get_session()
        try:
            items = session.query(Item).filter(Item.box_id == box_id).order_by(func.lower(Item.name)).all()
            self._items_cache[box_id] = items
            return items
        finally:
            session.close()

    def get_items_by_box_dto(self, box_id: str, box_name: str = "") -> list[ItemDto]:
        """Получить предметы бокса как DTO"""
        items = self.get_items_by_box(box_id)
        return items_to_dtos(items, box_name)

    def get_item_by_id(self, item_id: str) -> Item | None:
        session = self.get_session()
        try:
            return session.query(Item).filter(Item.id == item_id).first()
        finally:
            session.close()

    def get_item_dto_by_id(self, item_id: str) -> ItemDto | None:
        """Получить предмет как DTO с информацией о боксе"""
        item = self.get_item_by_id(item_id)
        if not item:
            return None
        box = self.get_box_by_id(item.box_id)
        return item_to_dto(item, box.name if box else "")

    def search_items(self, query: str) -> list[Item]:
        session = self.get_session()
        try:
            # Получаем все предметы и фильтруем на уровне Python
            # Это нужно для корректной работы с кириллицей в SQLite
            all_items = session.query(Item).all()
            query_lower = query.lower()
            filtered = [
                item for item in all_items
                if query_lower in item.name.lower() or query_lower in (item.comment or '').lower()
            ]
            # Сортировка результатов по имени (регистронезависимо)
            return sorted(filtered, key=lambda x: x.name.lower())
        finally:
            session.close()

    def search_items_dto(self, query: str) -> SearchResult:
        """Поиск предметов с возвратом SearchResult DTO"""
        items = self.search_items(query)
        # Добавляем имена боксов
        items_dto = []
        for item in items:
            box = self.get_box_by_id(item.box_id)
            items_dto.append(item_to_dto(item, box.name if box else ""))
        return SearchResult.from_items(items_dto, query)

    def get_box_by_name(self, name: str) -> Box | None:
        session = self.get_session()
        try:
            return session.query(Box).filter(func.lower(Box.name) == func.lower(name)).first()
        finally:
            session.close()

    def update_item(self, item_id: str, name: str = None, comment: str = None) -> Item | None:
        session = self.get_session()
        try:
            item = session.query(Item).filter(Item.id == item_id).first()
            if item:
                if name:
                    item.name = name
                if comment is not None:
                    item.comment = comment
                session.commit()
                session.refresh(item)
                self._items_cache.pop(item.box_id, None)
            return item
        finally:
            session.close()

    def delete_item(self, item_id: str) -> bool:
        session = self.get_session()
        try:
            item = session.query(Item).filter(Item.id == item_id).first()
            if item:
                session.delete(item)
                session.commit()
                self._items_cache.pop(item.box_id, None)
                return True
            return False
        finally:
            session.close()

    def get_all_items_with_boxes(self) -> list[tuple[Item, Box]]:
        session = self.get_session()
        try:
            return session.query(Item, Box).join(Box).all()
        finally:
            session.close()

    def get_items_count(self, box_id: str) -> int:
        """Получить количество предметов в боксе"""
        session = self.get_session()
        try:
            return session.query(func.count(Item.id)).filter(Item.box_id == box_id).scalar() or 0
        finally:
            session.close()
