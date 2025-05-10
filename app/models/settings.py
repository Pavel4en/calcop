from app.utils import execute_query
from typing import Dict, Any, Optional

class Settings:
    @staticmethod
    def get_all_settings() -> Dict[str, Any]:
        """
        Получение всех настроек калькулятора
        
        Returns:
            Dict[str, Any]: Словарь с настройками
        """
        query = "SELECT КлючНастройки, ЗначениеНастройки FROM НастройкиКалькулятор"
        results = execute_query(query, fetch_all=True)
        
        # Преобразуем результаты в словарь
        settings_dict = {}
        for key, value in results:
            settings_dict[key] = value
        
        return settings_dict
    
    @staticmethod
    def get_setting(key: str) -> Optional[str]:
        """
        Получение значения настройки по ключу
        
        Args:
            key: Ключ настройки
            
        Returns:
            Optional[str]: Значение настройки или None, если не найдена
        """
        query = "SELECT ЗначениеНастройки FROM НастройкиКалькулятор WHERE КлючНастройки = ?"
        result = execute_query(query, (key,), fetch_one=True)
        
        if result:
            return result[0]
        return None
    
    @staticmethod
    def update_setting(key: str, value: str) -> bool:
        """
        Обновление значения настройки
        
        Args:
            key: Ключ настройки
            value: Новое значение настройки
            
        Returns:
            bool: True, если операция успешна
        """
        try:
            # Проверяем существование настройки
            check_query = "SELECT 1 FROM НастройкиКалькулятор WHERE КлючНастройки = ?"
            exists = execute_query(check_query, (key,), fetch_one=True)
            
            if exists:
                # Обновляем существующую настройку
                update_query = "UPDATE НастройкиКалькулятор SET ЗначениеНастройки = ? WHERE КлючНастройки = ?"
                execute_query(update_query, (value, key))
            else:
                # Создаем новую настройку
                insert_query = "INSERT INTO НастройкиКалькулятор (КлючНастройки, ЗначениеНастройки) VALUES (?, ?)"
                execute_query(insert_query, (key, value))
            
            return True
        except Exception as e:
            print(f"Ошибка при обновлении настройки {key}: {e}")
            return False
    
    @staticmethod
    def create_settings_table():
        """
        Создание таблицы настроек калькулятора, если она не существует
        """
        try:
            # Проверяем существование таблицы
            check_query = """
            IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'НастройкиКалькулятор')
            BEGIN
                CREATE TABLE НастройкиКалькулятор (
                    КлючНастройки NVARCHAR(255) PRIMARY KEY,
                    ЗначениеНастройки NVARCHAR(MAX) NULL
                )
                
                -- Добавляем начальные настройки
                INSERT INTO НастройкиКалькулятор (КлючНастройки, ЗначениеНастройки) VALUES
                ('ИнструкцияСсылка', ''),
                ('ТелеграмСсылка', ''),
                ('КоэффициентЗатратности', '15')
            END
            """
            execute_query(check_query)
            
            return True
        except Exception as e:
            print(f"Ошибка при создании таблицы настроек: {e}")
            return False