"""
DTO (Data Transfer Objects) для типизации данных
"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass(frozen=True)
class BoxDto:
    """DTO для бокса"""
    id: str
    name: str
    comment: str = ""
    items_count: int = 0
    
    def __str__(self) -> str:
        return f"📦 {self.name} ({self.items_count})"


@dataclass(frozen=True)
class ItemDto:
    """DTO для предмета"""
    id: str
    name: str
    comment: str = ""
    box_id: str = ""
    box_name: str = ""
    created_by: str = ""
    created_at: Optional[str] = None
    
    def __str__(self) -> str:
        return f"📌 {self.name}"


@dataclass
class SearchResult:
    """Результат поиска предметов"""
    items: list[ItemDto] = field(default_factory=list)
    total: int = 0
    query: str = ""
    
    @classmethod
    def from_items(cls, items: list[ItemDto], query: str = "") -> "SearchResult":
        return cls(items=items, total=len(items), query=query)
    
    def is_empty(self) -> bool:
        return len(self.items) == 0


@dataclass
class BoxWithItems:
    """Бокс с количеством предметов"""
    box: BoxDto
    items_count: int
    
    def __str__(self) -> str:
        return f"📦 {self.box.name} ({self.items_count})"
