from sqlalchemy import Column, String, ForeignKey, create_engine
from sqlalchemy.orm import relationship, declarative_base, sessionmaker
from uuid6 import uuid7

Base = declarative_base()


class Box(Base):
    """Модель бокса (контейнера для предметов)"""
    __tablename__ = 'boxes'

    id = Column(String, primary_key=True, default=lambda: str(uuid7()))
    name = Column(String, unique=True, nullable=False)
    comment = Column(String, default='')

    items = relationship('Item', back_populates='box', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Box {self.name}>'


class Item(Base):
    """Модель предмета"""
    __tablename__ = 'items'

    id = Column(String, primary_key=True, default=lambda: str(uuid7()))
    name = Column(String, nullable=False)
    comment = Column(String, default='')
    box_id = Column(String, ForeignKey('boxes.id'), nullable=False)
    created_by = Column(String, default='')  # Информация о создателе и дате

    box = relationship('Box', back_populates='items')

    def __repr__(self):
        return f'<Item {self.name}>'


def create_session(db_url: str = 'sqlite+aiosqlite:///inventory.db'):
    """Создаёт движок и сессию для работы с БД"""
    engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()
