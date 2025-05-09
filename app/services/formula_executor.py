import re
from typing import Dict, Any, Optional, List

class FormulaExecutor:
    """
    Класс для выполнения формул расчета нагрузки.
    """
    
    @staticmethod
    def get_order_point(row: Dict[str, Any], formulas: List[Dict[str, Any]]) -> str:
        """
        Определяет пункт приказа для строки учебного плана, используя формулы из базы данных
        
        Args:
            row: Словарь с данными строки учебного плана
            formulas: Список формул из базы данных
            
        Returns:
            str: Номер пункта приказа
        """
        # Определяем формулу для данной строки
        matching_formula = FormulaExecutor._find_matching_formula(row, formulas)
        
        # Если найдена формула, возвращаем пункт приказа
        if matching_formula:
            return matching_formula.get('order_point', '')
        
        return ''
    
    @staticmethod
    def calculate_workload(row: Dict[str, Any], norms: Dict[str, Any], formulas: List[Dict[str, Any]]) -> float:
        """
        Рассчитывает нагрузку для строки учебного плана, используя формулы из базы данных
        
        Args:
            row: Словарь с данными строки учебного плана
            norms: Словарь с нормами
            formulas: Список формул из базы данных
            
        Returns:
            float: Рассчитанная нагрузка
        """
        # Определяем формулу для данной строки
        matching_formula = FormulaExecutor._find_matching_formula(row, formulas)
        
        # Если найдена формула, выполняем расчет
        if matching_formula:
            try:
                result = FormulaExecutor._execute_formula(matching_formula['formula'], row, norms)
                return round(result, 2)
            except Exception as e:
                print(f"Ошибка выполнения формулы: {e}")
                return 0.0
        
        # Если формула не найдена, возвращаем 0
        return 0.0
    
    @staticmethod
    def _find_matching_formula(row: Dict[str, Any], formulas: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Находит подходящую формулу для строки учебного плана, используя условия выбора
        
        Args:
            row: Словарь с данными строки учебного плана
            formulas: Список формул из базы данных
            
        Returns:
            Optional[Dict[str, Any]]: Формула или None, если не найдена
        """
        # Сначала проверяем формулы с условиями выбора
        for formula in formulas:
            selection_condition = formula.get('selection_condition')
            if selection_condition and FormulaExecutor._evaluate_selection_condition(row, selection_condition):
                return formula
        
        # Если не нашли подходящую формулу, возвращаем None
        return None
    
    @staticmethod
    def _evaluate_selection_condition(row: Dict[str, Any], selection_condition: str) -> bool:
        """
        Оценивает условие выбора для строки учебного плана
        
        Args:
            row: Словарь с данными строки учебного плана
            selection_condition: Строка с Python-выражением условия выбора
            
        Returns:
            bool: True, если условие выполняется
        """
        if not selection_condition:
            return False
        
        try:
            # Создаем безопасное пространство имен для выполнения условия
            safe_vars = {
                'row': row,
                're': re
            }
            
            # Выполняем условие
            result = eval(selection_condition, {"__builtins__": {}}, safe_vars)
            
            # Преобразуем результат в булево значение
            return bool(result)
        except Exception as e:
            print(f"Ошибка выполнения условия выбора '{selection_condition}': {e}")
            return False
    
    @staticmethod
    def _execute_formula(formula_str: str, row: Dict[str, Any], norms: Dict[str, Any]) -> float:
        """
        Выполняет формулу расчета
        
        Args:
            formula_str: Строка с формулой
            row: Словарь с данными строки учебного плана
            norms: Словарь с нормами
            
        Returns:
            float: Результат вычисления формулы
        """
        try:
            # Создаем безопасное пространство имен для выполнения формулы
            safe_vars = {
                'row': row,
                'norms': norms,
                'float': float,
                'int': int,
                'round': round,
                're': re
            }
            
            # Выполняем формулу
            result = eval(formula_str, {"__builtins__": {}}, safe_vars)
            
            # Преобразуем результат в число с плавающей точкой
            return float(result)
        except Exception as e:
            print(f"Ошибка выполнения формулы '{formula_str}': {e}")
            raise