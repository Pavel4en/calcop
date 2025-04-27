import hashlib
from app.utils import execute_query
from typing import Optional, List, Dict, Any, Tuple

class User:
    def __init__(self, id: int, login: str, full_name: str, is_admin: bool = False):
        self.id = id
        self.login = login
        self.full_name = full_name
        self.is_admin = is_admin
    
    @staticmethod
    def hash_login_password(login: str, password: str) -> bytes:
        """Хеширование пароля на основе логина и пароля"""
        combined = str(login).lower() + str(password)
        md5_hash = hashlib.md5(combined.encode()).digest()
        return md5_hash
    
    @classmethod
    def authenticate(cls, login: str, password: str) -> Optional['User']:
        """Аутентификация пользователя"""
        hashed_password = cls.hash_login_password(login, password)
        
        # Запрос на поиск пользователя
        user_query = "SELECT ID, Логин, ФИО FROM Пользователи WHERE Логин = ? AND Пароль = ?"
        user_data = execute_query(user_query, (login, hashed_password), fetch_one=True)
        
        if not user_data:
            return None
        
        user_id, user_login, full_name = user_data
        
        # Проверка на администратора
        admin_query = "SELECT 1 FROM [Пользователи-Роли] WHERE КодПользователя = ? AND КодРоли = 17"
        is_admin = execute_query(admin_query, (user_id,), fetch_one=True) is not None
        
        return cls(user_id, user_login, full_name, is_admin)
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация пользователя в словарь для хранения в сессии"""
        return {
            'id': self.id,
            'login': self.login,
            'full_name': self.full_name,
            'is_admin': self.is_admin
        }
    
    @classmethod
    def from_dict(cls, user_dict: Dict[str, Any]) -> 'User':
        """Создание объекта пользователя из словаря"""
        return cls(
            id=user_dict['id'],
            login=user_dict['login'],
            full_name=user_dict['full_name'],
            is_admin=user_dict['is_admin']
        )