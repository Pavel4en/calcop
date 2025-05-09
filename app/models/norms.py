from app.utils import execute_query
from typing import List, Dict, Any, Optional, Tuple

class Norms:
    @staticmethod
    def get_all_norms() -> List[Dict[str, Any]]:
        """
        Получение всех норм из таблицы НормыДВФУ
        
        Returns:
            List[Dict[str, Any]]: Список словарей с данными норм
        """
        query = "SELECT ID, Норма, Значение, Блокировка FROM НормыДВФУ ORDER BY ID"
        results = execute_query(query, fetch_all=True)
        
        # Преобразуем результаты в список словарей
        norms_list = []
        for row in results:
            norms_list.append({
                'id': row[0],
                'name': row[1],
                'value': row[2],
                'locked': row[3] == 1  # Преобразуем в булево значение
            })
        
        return norms_list
    
    @staticmethod
    def get_norm_by_id(norm_id: int) -> Optional[Dict[str, Any]]:
        """
        Получение нормы по ID
        
        Args:
            norm_id: ID нормы
            
        Returns:
            Optional[Dict[str, Any]]: Словарь с данными нормы или None, если не найдена
        """
        query = "SELECT ID, Норма, Значение, Блокировка FROM НормыДВФУ WHERE ID = ?"
        result = execute_query(query, (norm_id,), fetch_one=True)
        
        if not result:
            return None
        
        return {
            'id': result[0],
            'name': result[1],
            'value': result[2],
            'locked': result[3] == 1
        }
    
    @staticmethod
    def create_norm(name: str, value: float, locked: bool = False) -> int:
        """
        Создание новой нормы
        
        Args:
            name: Название нормы
            value: Значение нормы
            locked: Признак блокировки (по умолчанию False)
            
        Returns:
            int: ID созданной нормы
        """
        try:
            # Проверка на существование нормы с таким названием
            check_query = "SELECT ID FROM НормыДВФУ WHERE Норма = ?"
            existing = execute_query(check_query, (name,), fetch_one=True)
            
            if existing:
                raise ValueError(f"Норма с названием '{name}' уже существует")
            
            # Создание новой нормы
            locked_value = 1 if locked else 0
            
            insert_query = "INSERT INTO НормыДВФУ (Норма, Значение, Блокировка) VALUES (?, ?, ?)"
            execute_query(insert_query, (name, value, locked_value))
            
            # Получение ID созданной нормы
            get_id_query = "SELECT @@IDENTITY"
            result = execute_query(get_id_query, fetch_one=True)
            
            return result[0] if result and result[0] else 0
        except Exception as e:
            print(f"Ошибка при создании нормы: {e}")
            raise
    
    @staticmethod
    def update_norm(norm_id: int, name: Optional[str] = None, value: Optional[float] = None, 
                   locked: Optional[bool] = None) -> bool:
        """
        Обновление нормы
        
        Args:
            norm_id: ID нормы
            name: Новое название нормы (если None, то не обновляется)
            value: Новое значение нормы (если None, то не обновляется)
            locked: Новый признак блокировки (если None, то не обновляется)
            
        Returns:
            bool: True, если обновление прошло успешно
        """
        try:
            # Проверка существования нормы
            check_query = "SELECT ID FROM НормыДВФУ WHERE ID = ?"
            existing = execute_query(check_query, (norm_id,), fetch_one=True)
            
            if not existing:
                return False
            
            # Формирование запроса обновления
            params = []
            set_clauses = []
            
            if name is not None:
                # Проверка на существование другой нормы с таким названием
                check_name_query = "SELECT ID FROM НормыДВФУ WHERE Норма = ? AND ID != ?"
                name_exists = execute_query(check_name_query, (name, norm_id), fetch_one=True)
                
                if name_exists:
                    raise ValueError(f"Норма с названием '{name}' уже существует")
                    
                set_clauses.append("Норма = ?")
                params.append(name)
            
            if value is not None:
                set_clauses.append("Значение = ?")
                params.append(value)
            
            if locked is not None:
                set_clauses.append("Блокировка = ?")
                params.append(1 if locked else 0)
            
            # Если нет параметров для обновления, возвращаем True
            if not set_clauses:
                return True
            
            # Формирование SQL-запроса
            update_query = f"UPDATE НормыДВФУ SET {', '.join(set_clauses)} WHERE ID = ?"
            params.append(norm_id)
            
            # Выполнение запроса
            execute_query(update_query, params)
            
            return True
        except Exception as e:
            print(f"Ошибка при обновлении нормы: {e}")
            raise
    
    @staticmethod
    def delete_norm(norm_id: int) -> bool:
        """
        Удаление нормы
        
        Args:
            norm_id: ID нормы
            
        Returns:
            bool: True, если удаление прошло успешно
        """
        try:
            # Проверка существования нормы
            check_query = "SELECT ID FROM НормыДВФУ WHERE ID = ?"
            existing = execute_query(check_query, (norm_id,), fetch_one=True)
            
            if not existing:
                return False
            
            # Удаление нормы
            delete_query = "DELETE FROM НормыДВФУ WHERE ID = ?"
            execute_query(delete_query, (norm_id,))
            
            return True
        except Exception as e:
            print(f"Ошибка при удалении нормы: {e}")
            raise
    
    @staticmethod
    def update_norm_value(norm_id: int, new_value: float) -> bool:
        """
        Обновление значения нормы
        
        Args:
            norm_id: ID нормы
            new_value: Новое значение
            
        Returns:
            bool: True, если обновление прошло успешно
        """
        try:
            # Проверяем, не заблокирована ли норма
            check_query = "SELECT Блокировка FROM НормыДВФУ WHERE ID = ?"
            result = execute_query(check_query, (norm_id,), fetch_one=True)
            
            if not result:
                return False  # Норма не найдена
            
            is_locked = result[0] == 1
            
            if is_locked:
                return False  # Норма заблокирована, не обновляем
            
            # Обновляем значение
            update_query = "UPDATE НормыДВФУ SET Значение = ? WHERE ID = ?"
            execute_query(update_query, (new_value, norm_id))
            
            return True
        except Exception as e:
            print(f"Ошибка при обновлении значения нормы: {e}")
            raise