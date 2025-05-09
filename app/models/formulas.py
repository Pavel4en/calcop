from app.utils import execute_query
from typing import List, Dict, Any, Optional, Tuple

class Formula:
    @staticmethod
    def get_all_formulas() -> List[Dict[str, Any]]:
        """
        Получение всех формул из таблицы Формулы
        
        Returns:
            List[Dict[str, Any]]: Список словарей с данными формул
        """
        query = """
        SELECT ID, Название, КодУсловия, Условие, ФормулаРасчета, ПунктПриказа, Комментарий, 
               УсловиеВыбора 
        FROM Формулы 
        ORDER BY ID
        """
        results = execute_query(query, fetch_all=True)
        
        # Преобразуем результаты в список словарей
        formulas_list = []
        for row in results:
            formulas_list.append({
                'id': row[0],
                'name': row[1],
                'condition_code': row[2],
                'condition': row[3],
                'formula': row[4],
                'order_point': row[5],
                'comment': row[6],
                'selection_condition': row[7] if len(row) > 7 else None
            })
        
        return formulas_list
    
    @staticmethod
    def get_formula_by_id(formula_id: int) -> Optional[Dict[str, Any]]:
        """
        Получение формулы по ID
        
        Args:
            formula_id: ID формулы
            
        Returns:
            Optional[Dict[str, Any]]: Словарь с данными формулы или None, если не найдена
        """
        query = """
        SELECT ID, Название, КодУсловия, Условие, ФормулаРасчета, ПунктПриказа, Комментарий,
               УсловиеВыбора
        FROM Формулы 
        WHERE ID = ?
        """
        result = execute_query(query, (formula_id,), fetch_one=True)
        
        if not result:
            return None
        
        return {
            'id': result[0],
            'name': result[1],
            'condition_code': result[2],
            'condition': result[3],
            'formula': result[4],
            'order_point': result[5],
            'comment': result[6],
            'selection_condition': result[7] if len(result) > 7 else None
        }
    
    @staticmethod
    def create_formula(name: str, condition_code: str, condition: str, formula: str, 
                       order_point: str, comment: str = None, selection_condition: str = None) -> int:
        """
        Создание новой формулы
        
        Args:
            name: Название формулы
            condition_code: Код условия
            condition: Текстовое описание условия
            formula: Формула расчета
            order_point: Пункт приказа
            comment: Комментарий
            selection_condition: Условие выбора формулы (Python-код)
            
        Returns:
            int: ID созданной формулы
        """
        try:
            query = """
            INSERT INTO Формулы (Название, КодУсловия, Условие, ФормулаРасчета, ПунктПриказа, Комментарий, УсловиеВыбора)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            execute_query(query, (name, condition_code, condition, formula, order_point, comment, selection_condition))
            
            # Получение ID созданной формулы
            get_id_query = "SELECT @@IDENTITY"
            result = execute_query(get_id_query, fetch_one=True)
            
            return result[0] if result and result[0] else 0
        except Exception as e:
            print(f"Ошибка при создании формулы: {e}")
            raise
    
    @staticmethod
    def update_formula(formula_id: int, name: Optional[str] = None, condition_code: Optional[str] = None, 
                       condition: Optional[str] = None, formula: Optional[str] = None,
                       order_point: Optional[str] = None, comment: Optional[str] = None,
                       selection_condition: Optional[str] = None) -> bool:
        """
        Обновление формулы
        
        Args:
            formula_id: ID формулы
            name: Новое название формулы
            condition_code: Новый код условия
            condition: Новое текстовое описание условия
            formula: Новая формула расчета
            order_point: Новый пункт приказа
            comment: Новый комментарий
            selection_condition: Новое условие выбора формулы (Python-код)
            
        Returns:
            bool: True, если обновление прошло успешно
        """
        try:
            # Проверка существования формулы
            check_query = "SELECT ID FROM Формулы WHERE ID = ?"
            existing = execute_query(check_query, (formula_id,), fetch_one=True)
            
            if not existing:
                return False
            
            # Формирование запроса обновления
            update_fields = []
            params = []
            
            if name is not None:
                update_fields.append("Название = ?")
                params.append(name)
                
            if condition_code is not None:
                update_fields.append("КодУсловия = ?")
                params.append(condition_code)
                
            if condition is not None:
                update_fields.append("Условие = ?")
                params.append(condition)
                
            if formula is not None:
                update_fields.append("ФормулаРасчета = ?")
                params.append(formula)
                
            if order_point is not None:
                update_fields.append("ПунктПриказа = ?")
                params.append(order_point)
                
            if comment is not None:
                update_fields.append("Комментарий = ?")
                params.append(comment)
                
            if selection_condition is not None:
                update_fields.append("УсловиеВыбора = ?")
                params.append(selection_condition)
            
            # Если нет параметров для обновления, возвращаем True
            if not update_fields:
                return True
            
            # Формирование SQL-запроса
            update_query = f"UPDATE Формулы SET {', '.join(update_fields)} WHERE ID = ?"
            params.append(formula_id)
            
            # Выполнение запроса
            execute_query(update_query, params)
            
            return True
        except Exception as e:
            print(f"Ошибка при обновлении формулы: {e}")
            raise
    
    @staticmethod
    def delete_formula(formula_id: int) -> bool:
        """
        Удаление формулы
        
        Args:
            formula_id: ID формулы
            
        Returns:
            bool: True, если удаление прошло успешно
        """
        try:
            # Проверка существования формулы
            check_query = "SELECT ID FROM Формулы WHERE ID = ?"
            existing = execute_query(check_query, (formula_id,), fetch_one=True)
            
            if not existing:
                return False
            
            # Удаление формулы
            delete_query = "DELETE FROM Формулы WHERE ID = ?"
            execute_query(delete_query, (formula_id,))
            
            return True
        except Exception as e:
            print(f"Ошибка при удалении формулы: {e}")
            raise