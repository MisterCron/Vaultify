import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Конфигурация бота"""
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    BOT_DEV_ID = os.getenv('BOT_DEV_ID')
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///vaultify.db')
    ALLOWED_USERS = os.getenv('ALLOWED_USERS', '')

    @classmethod
    def get_allowed_users(cls) -> set[int]:
        """Получение списка разрешённых пользователей"""
        if not cls.ALLOWED_USERS:
            return set()
        return {int(uid.strip()) for uid in cls.ALLOWED_USERS.split(',') if uid.strip()}

    @classmethod
    def is_user_allowed(cls, user_id: int) -> bool:
        """Проверка доступа пользователя"""
        # Администратор (BOT_DEV_ID) всегда имеет доступ
        if cls.BOT_DEV_ID and str(user_id) == str(cls.BOT_DEV_ID):
            return True
        
        allowed = cls.get_allowed_users()
        # Если список пустой — доступ разрешён всем (для обратной совместимости)
        return len(allowed) == 0 or user_id in allowed

    @classmethod
    def validate(cls):
        """Проверка необходимых переменных окружения"""
        if not cls.BOT_TOKEN:
            raise ValueError('BOT_TOKEN не указан в .env')
        return True
