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
        # Определяем код условия для данной строки
        condition_code = FormulaExecutor._get_condition_code(row)
        
        # Ищем формулу с соответствующим кодом условия
        for formula in formulas:
            if formula['condition_code'] == condition_code:
                return formula.get('order_point', '')
        
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
        # Определяем код условия для данной строки
        condition_code = FormulaExecutor._get_condition_code(row)
        
        # Ищем формулу с соответствующим кодом условия
        for formula in formulas:
            if formula['condition_code'] == condition_code:
                # Выполняем формулу расчета
                try:
                    result = FormulaExecutor._execute_formula(formula['formula'], row, norms)
                    return round(result, 2)
                except Exception as e:
                    print(f"Ошибка выполнения формулы: {e}")
                    return 0.0
        
        # Если формула не найдена, возвращаем 0
        return 0.0
    
    @staticmethod
    def _get_condition_code(row: Dict[str, Any]) -> str:
        """
        Определяет код условия для строки учебного плана
        
        Args:
            row: Словарь с данными строки учебного плана
            
        Returns:
            str: Код условия
        """
        # Проверяем различные условия и возвращаем соответствующий код
        
        # Лекции
        if row['Вид работы'] == 'Лекционные занятия':
            return 'lecture'
        
        # Практические и лабораторные занятия по языкам и физ. культуре
        elif row['Вид работы'] in ['Практические занятия', 'Лабораторные занятия']:
            if row['Дисциплина'] in ['Иностранный язык', 'Элективные курсы по физической культуре и спорту', 'Физическая культура и спорт']:
                return 'practice_lang_sport'
            else:
                return 'practice_lab'
        
        # Экзамен
        elif row['Вид работы'] == 'Экзамен' and (row['Индекс дисциплины'].startswith('Б1') or row['Индекс дисциплины'].startswith('ФТД')):
            return 'exam'
        
        # Кураторство
        elif row['Вид работы'] == 'Кураторство':
            return 'curator'
        
        # Практики
        elif row['Индекс дисциплины'].startswith('Б2') and row['Вид работы'] == 'Руководство (ЗЕТ)':
            return 'practice_management'
        elif row['Индекс дисциплины'].startswith('Б2') and row['Вид работы'] == 'Недели':
            if re.search(r"07\.03\.01", row.get('Файл УП', '')):
                return 'practice_weeks_architecture'
            else:
                return 'practice_weeks'
        
        # Проектная деятельность
        elif row['Вид работы'] == 'Руководство проектной деятельности' and row['Дисциплина'] == 'Проектная деятельность':
            return 'project_activity'
        
        # Зачет и зачет с оценкой
        elif (row['Вид работы'] == 'Зачет' or row['Вид работы'] == 'Зачет с оценкой') and (row['Индекс дисциплины'].startswith('Б1') or row['Индекс дисциплины'].startswith('ФТД')):
            if row['Дисциплина'] != 'Проектная деятельность':
                return 'credit'
        
        # Письменные работы
        elif row['Вид работы'] in ['Эссе', 'Тест', 'Реферат', 'Расчетно-графическая работа', 'Контрольная работа'] and row['Форма обучения'] == 'Очная форма':
            return 'written_work'
        
        # Рецензирование ВКР
        elif row['Вид работы'] == 'Рецензирование' and (row['Квалификация'].strip().lower() != 'бакалавр'):
            return 'thesis_review'
        
        # Курсовая работа
        elif row['Вид работы'] == 'Курсовая работа':
            return 'course_work'
        
        # Курсовой проект
        elif row['Вид работы'] == 'Курсовой проект':
            return 'course_project'
        
        # ВКР бакалавр и специалитет
        elif row['Вид работы'] == 'Руководство (в рамках ГИА)' and (row['Квалификация'].strip().lower() != 'магистр'):
            return 'thesis_bachelor'
        
        # ВКР магистратура 1 курс
        elif row['Вид работы'] == 'Руководство (в рамках ГИА)' and row['Курс'] == '1' and (row['Квалификация'].strip().lower() == 'магистр'):
            return 'thesis_master_1'
        
        # ВКР магистратура 2 курс
        elif row['Вид работы'] == 'Руководство (в рамках ГИА)' and row['Курс'] == '2' and (row['Квалификация'].strip().lower() == 'магистр'):
            return 'thesis_master_2'
        
        # Государственный экзамен (ГИА)
        elif row['Вид работы'] == 'Экзамен' and row['Индекс дисциплины'].startswith('Б3'):
            if row['Квалификация'].strip().lower() == 'магистр':
                if row['Форма обучения'] == 'Очная форма':
                    return 'state_exam_master_full'
                elif row['Форма обучения'] == 'Заочная форма':
                    return 'state_exam_master_part'
                elif row['Форма обучения'] == 'Очно-заочная форма':
                    return 'state_exam_master_mixed'
            else:
                return 'state_exam_bachelor'
        
        # Если ни одно из условий не выполнено, возвращаем пустой код
        return ''
    
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