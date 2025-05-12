from app.utils import execute_query
from typing import List, Dict, Any, Optional, Tuple
import datetime
import json

class SavedWorkload:
    @staticmethod
    def create_tables():
        """
        Создание необходимых таблиц, если они не существуют
        """
        # Создание таблицы для сохранения общих сведений о расчете нагрузки
        query_workload = """
        IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'РасчетыНагрузки')
        BEGIN
            CREATE TABLE РасчетыНагрузки (
                ID INT IDENTITY(1,1) PRIMARY KEY,
                НазваниеРасчета NVARCHAR(255) NOT NULL,
                ДатаСоздания DATETIME2 NOT NULL DEFAULT GETDATE(),
                ПользовательID INT NOT NULL,
                АкадемическийГод NVARCHAR(50) NOT NULL,
                ГодНабора NVARCHAR(50) NOT NULL,
                ФайлУчебногоПлана NVARCHAR(255) NOT NULL,
                Контингент INT NOT NULL,
                Курс INT NULL,
                ОбщаяНагрузка FLOAT NOT NULL,
                КоличествоСтавок FLOAT NOT NULL,
                КоэффициентЗатратности FLOAT NOT NULL,
                ТрудоемкостьЗЕТ FLOAT NOT NULL,
                НормаНаСтавку FLOAT NOT NULL DEFAULT 900,
                Комментарий NVARCHAR(MAX) NULL,
                FOREIGN KEY (ПользовательID) REFERENCES Пользователи(ID)
            );
        END
        """
        execute_query(query_workload)
        
        # Добавляем колонку НормаНаСтавку к существующей таблице если она не существует
        query_add_column = """
        IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
                       WHERE TABLE_NAME = 'РасчетыНагрузки' 
                       AND COLUMN_NAME = 'НормаНаСтавку')
        BEGIN
            ALTER TABLE РасчетыНагрузки 
            ADD НормаНаСтавку FLOAT NOT NULL DEFAULT 900
        END
        """
        execute_query(query_add_column)
        
        # Создание таблицы для сохранения сведений о программе
        query_program = """
        IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'СведенияОПрограмме')
        BEGIN
            CREATE TABLE СведенияОПрограмме (
                РасчетID INT PRIMARY KEY,
                КодСпециальности NVARCHAR(50) NULL,
                Специальность NVARCHAR(255) NULL,
                Профиль NVARCHAR(255) NULL,
                Квалификация NVARCHAR(100) NULL,
                ФормаОбучения NVARCHAR(100) NULL,
                Кафедра NVARCHAR(255) NULL,
                FOREIGN KEY (РасчетID) REFERENCES РасчетыНагрузки(ID) ON DELETE CASCADE
            );
        END
        """
        execute_query(query_program)
        
        # Создание таблицы для сохранения строк расчета нагрузки
        query_rows = """
        IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'СтрокиРасчетаНагрузки')
        BEGIN
            CREATE TABLE СтрокиРасчетаНагрузки (
                ID INT IDENTITY(1,1) PRIMARY KEY,
                РасчетID INT NOT NULL,
                ИндексДисциплины NVARCHAR(50) NULL,
                Дисциплина NVARCHAR(255) NOT NULL,
                Курс INT NULL,
                Семестр INT NULL,
                ВидРаботы NVARCHAR(255) NOT NULL,
                Часы FLOAT NULL,
                Недели INT NULL,
                Кафедра NVARCHAR(255) NULL,
                КонтингентПоДисциплине INT NULL,
                ЧисленностьПотока INT NULL,
                КоличествоПодгрупп INT NULL,
                НепосредственноеУчастиеППС BIT NOT NULL DEFAULT 0,
                Нагрузка FLOAT NOT NULL,
                ПунктПриказа NVARCHAR(50) NULL,
                Комментарий NVARCHAR(MAX) NULL,
                Учитывать BIT NOT NULL DEFAULT 1,
                FOREIGN KEY (РасчетID) REFERENCES РасчетыНагрузки(ID) ON DELETE CASCADE
            );
            
            -- Добавляем индекс для быстрого поиска по РасчетID
            CREATE INDEX IX_СтрокиРасчетаНагрузки_РасчетID ON СтрокиРасчетаНагрузки(РасчетID);
        END
        """
        execute_query(query_rows)
        
        return True
    
    @staticmethod
    def save_workload(user_id: int, title: str, data: Dict[str, Any], comment: str = None) -> int:
        """
        Сохранение расчета нагрузки в базу данных
        
        Args:
            user_id: ID пользователя
            title: Название расчета
            data: Данные расчета
            comment: Комментарий к расчету
            
        Returns:
            int: ID созданного расчета
        """
        try:
            # Создаем таблицы, если они не существуют
            SavedWorkload.create_tables()
            
            # Получаем данные для сохранения
            program_info = data.get('program_info', {})
            workload_summary = data.get('workload_summary', {})
            calculated_data = data.get('calculated_data', [])
            
            # Вставляем основные данные расчета и получаем ID
            query_insert_workload = """
            INSERT INTO РасчетыНагрузки (
                НазваниеРасчета, ПользовательID, АкадемическийГод, ГодНабора, 
                ФайлУчебногоПлана, Контингент, Курс, ОбщаяНагрузка, 
                КоличествоСтавок, КоэффициентЗатратности, ТрудоемкостьЗЕТ, НормаНаСтавку, Комментарий
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """
            
            params = (
                title,
                user_id,
                program_info.get('academic_year', ''),
                program_info.get('admission_year', ''),
                program_info.get('plan_file', ''),
                data.get('contingent', 0),
                data.get('course', None),
                workload_summary.get('total_workload', 0),
                workload_summary.get('calculated_positions', 0),
                workload_summary.get('cost_coefficient', 0),
                workload_summary.get('total_zet_hours', 0),
                workload_summary.get('norm_hours_per_position', 900),  # Сохраняем актуальную норму
                comment
            )
            
            # Выполняем вставку основной записи
            execute_query(query_insert_workload, params)
            
            # Получаем ID вставленной записи
            id_query = "SELECT IDENT_CURRENT('РасчетыНагрузки') AS ID"
            id_result = execute_query(id_query, fetch_one=True)
            workload_id = int(id_result[0])
            
            # Вставляем сведения о программе
            query_insert_program = """
            INSERT INTO СведенияОПрограмме (
                РасчетID, КодСпециальности, Специальность, Профиль, 
                Квалификация, ФормаОбучения, Кафедра
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            
            program_params = (
                workload_id,
                program_info.get('specialty_code', ''),
                program_info.get('specialty', ''),
                program_info.get('profile', ''),
                program_info.get('qualification', ''),
                program_info.get('education_form', ''),
                program_info.get('department', '')
            )
            
            execute_query(query_insert_program, program_params)
            
            # Сохраняем строки расчета пакетами для оптимизации
            batch_size = 100
            total_rows = len(calculated_data)
            
            for i in range(0, total_rows, batch_size):
                batch = calculated_data[i:i + batch_size]
                batch_queries = []
                
                for row in batch:
                    query_row = """
                    INSERT INTO СтрокиРасчетаНагрузки (
                        РасчетID, ИндексДисциплины, Дисциплина, Курс, Семестр, 
                        ВидРаботы, Часы, Недели, Кафедра, КонтингентПоДисциплине, 
                        ЧисленностьПотока, КоличествоПодгрупп, НепосредственноеУчастиеППС, 
                        Нагрузка, ПунктПриказа, Комментарий, Учитывать
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    
                    row_params = (
                        workload_id,
                        row.get('Индекс дисциплины', ''),
                        row.get('Дисциплина', ''),
                        row.get('Курс', None),
                        row.get('Семестр', None),
                        row.get('Вид работы', ''),
                        row.get('Часы', 0),
                        row.get('Недели', 0),
                        row.get('Название кафедры', ''),
                        row.get('Контингент по дисциплине', 0),
                        row.get('Численность потока', 0),
                        row.get('Количество подгрупп', 1),
                        1 if row.get('С непосредственным участием ППС', '') == 'on' else 0,
                        row.get('Нагрузка', 0),
                        row.get('Пункт приказа', ''),
                        row.get('Комментарии', ''),
                        1 if row.get('Учитывать', False) else 0
                    )
                    
                    execute_query(query_row, row_params)
            
            return workload_id
        except Exception as e:
            print(f"Ошибка при сохранении расчета: {e}")
            raise
    
    @staticmethod
    def get_user_workloads(user_id: int) -> List[Dict[str, Any]]:
        """
        Получение списка сохраненных расчетов пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            List[Dict[str, Any]]: Список сохраненных расчетов
        """
        query = """
        SELECT 
            w.ID, 
            w.НазваниеРасчета, 
            w.ДатаСоздания, 
            w.АкадемическийГод, 
            w.ГодНабора, 
            w.ФайлУчебногоПлана,
            w.ОбщаяНагрузка,
            p.Специальность,
            p.КодСпециальности,
            p.ФормаОбучения,
            u.ФИО as СоздательФИО
        FROM 
            РасчетыНагрузки w
        LEFT JOIN 
            СведенияОПрограмме p ON w.ID = p.РасчетID
        LEFT JOIN 
            Пользователи u ON w.ПользовательID = u.ID
        WHERE 
            w.ПользовательID = ?
        ORDER BY 
            w.ДатаСоздания DESC
        """
        
        results = execute_query(query, (user_id,), fetch_all=True)
        
        # Преобразуем результаты в список словарей
        workloads = []
        for row in results:
            # Форматируем дату
            date_created = row[2] if row[2] else datetime.datetime.now()
            formatted_date = date_created.strftime("%d.%m.%Y %H:%M")
            
            workloads.append({
                'id': row[0],
                'title': row[1],
                'date_created': formatted_date,
                'academic_year': row[3],
                'admission_year': row[4],
                'plan_file': row[5],
                'total_workload': row[6],
                'specialty': row[7],
                'specialty_code': row[8],
                'education_form': row[9],
                'creator_name': row[10]
            })
        
        return workloads
    
    @staticmethod
    def get_workload_by_id(workload_id: int, include_hidden: bool = False) -> Optional[Dict[str, Any]]:
        """
        Получение расчета нагрузки по ID
        
        Args:
            workload_id: ID расчета
            include_hidden: Включить скрытые строки (не учитываемые в расчете)
            
        Returns:
            Optional[Dict[str, Any]]: Данные расчета или None, если не найден
        """
        # Получаем основные данные о расчете
        query_workload = """
        SELECT 
            w.ID, 
            w.НазваниеРасчета, 
            w.ДатаСоздания, 
            w.ПользовательID,
            w.АкадемическийГод, 
            w.ГодНабора, 
            w.ФайлУчебногоПлана,
            w.Контингент,
            w.Курс,
            w.ОбщаяНагрузка,
            w.КоличествоСтавок,
            w.КоэффициентЗатратности,
            w.ТрудоемкостьЗЕТ,
            w.Комментарий,
            u.ФИО as СоздательФИО,
            ISNULL(w.НормаНаСтавку, 900) as НормаНаСтавку
        FROM 
            РасчетыНагрузки w
        LEFT JOIN 
            Пользователи u ON w.ПользовательID = u.ID
        WHERE 
            w.ID = ?
        """
        
        workload_result = execute_query(query_workload, (workload_id,), fetch_one=True)
        
        if not workload_result:
            return None
        
        # Форматируем дату
        date_created = workload_result[2] if workload_result[2] else datetime.datetime.now()
        formatted_date = date_created.strftime("%d.%m.%Y %H:%M")
        
        # Создаем словарь с основными данными
        workload_data = {
            'id': workload_result[0],
            'title': workload_result[1],
            'date_created': formatted_date,
            'user_id': workload_result[3],
            'academic_year': workload_result[4],
            'admission_year': workload_result[5],
            'plan_file': workload_result[6],
            'contingent': workload_result[7],
            'course': workload_result[8],
            'creator_name': workload_result[14],
            'comment': workload_result[13],
            'workload_summary': {
                'total_workload': workload_result[9],
                'calculated_positions': workload_result[10],
                'cost_coefficient': workload_result[11],
                'total_zet_hours': workload_result[12],
                'norm_hours_per_position': workload_result[15]  # Берем из БД
            }
        }
        
        # Получаем сведения о программе
        query_program = """
        SELECT 
            КодСпециальности,
            Специальность,
            Профиль,
            Квалификация,
            ФормаОбучения,
            Кафедра
        FROM 
            СведенияОПрограмме
        WHERE 
            РасчетID = ?
        """
        
        program_result = execute_query(query_program, (workload_id,), fetch_one=True)
        
        if program_result:
            workload_data['program_info'] = {
                'specialty_code': program_result[0],
                'specialty': program_result[1],
                'profile': program_result[2],
                'qualification': program_result[3],
                'education_form': program_result[4],
                'department': program_result[5],
                'academic_year': workload_data['academic_year'],
                'admission_year': workload_data['admission_year']
            }
        
        # Получаем строки расчета пакетами
        query_rows = """
        SELECT 
            ИндексДисциплины,
            Дисциплина,
            Курс,
            Семестр,
            ВидРаботы,
            Часы,
            Недели,
            Кафедра,
            КонтингентПоДисциплине,
            ЧисленностьПотока,
            КоличествоПодгрупп,
            НепосредственноеУчастиеППС,
            Нагрузка,
            ПунктПриказа,
            Комментарий,
            Учитывать
        FROM 
            СтрокиРасчетаНагрузки
        WHERE 
            РасчетID = ?"""
        
        # Если не включать скрытые, то только учитываемые строки
        if not include_hidden:
            query_rows += " AND Учитывать = 1"
            
        query_rows += " ORDER BY ИндексДисциплины, Семестр, ВидРаботы"
        
        rows_results = execute_query(query_rows, (workload_id,), fetch_all=True)
        
        calculated_data = []
        for row in rows_results:
            # Непосредственное участие ППС (преобразование из bit в строку 'on')
            has_ppe = 'on' if row[11] else ''
            
            # Добавляем строку в список
            calculated_data.append({
                'Индекс дисциплины': row[0],
                'Дисциплина': row[1],
                'Курс': row[2],
                'Семестр': row[3],
                'Вид работы': row[4],
                'Часы': row[5],
                'Недели': row[6],
                'Название кафедры': row[7],
                'Контингент по дисциплине': row[8],
                'Численность потока': row[9],
                'Количество подгрупп': row[10],
                'С непосредственным участием ППС': has_ppe,
                'Нагрузка': row[12],
                'Пункт приказа': row[13],
                'Комментарии': row[14],
                'Учитывать': bool(row[15]),
                'ЗЕТ': None,  # Заполним позже при необходимости
                'Квалификация': program_result[3] if program_result else None,
                'Форма обучения': program_result[4] if program_result else None,
                'Файл УП': workload_data.get('plan_file', '')
            })
        
        workload_data['calculated_data'] = calculated_data
        
        return workload_data
    
    @staticmethod
    def update_workload(workload_id: int, data: Dict[str, Any]) -> bool:
        """
        Обновление расчета нагрузки
        
        Args:
            workload_id: ID расчета
            data: Новые данные расчета
            
        Returns:
            bool: True, если обновление успешно
        """
        try:
            # Получаем данные для обновления
            program_info = data.get('program_info', {})
            workload_summary = data.get('workload_summary', {})
            calculated_data = data.get('calculated_data', [])
            
            # Обновляем основные данные расчета
            query_update_workload = """
            UPDATE РасчетыНагрузки SET
                Контингент = ?,
                ОбщаяНагрузка = ?,
                КоличествоСтавок = ?,
                КоэффициентЗатратности = ?,
                ТрудоемкостьЗЕТ = ?,
                НормаНаСтавку = ?
            WHERE ID = ?
            """
            
            params = (
                data.get('contingent', 0),
                workload_summary.get('total_workload', 0),
                workload_summary.get('calculated_positions', 0),
                workload_summary.get('cost_coefficient', 0),
                workload_summary.get('total_zet_hours', 0),
                workload_summary.get('norm_hours_per_position', 900),
                workload_id
            )
            
            execute_query(query_update_workload, params)
            
            # Удаляем старые строки расчета
            delete_rows_query = "DELETE FROM СтрокиРасчетаНагрузки WHERE РасчетID = ?"
            execute_query(delete_rows_query, (workload_id,))
            
            # Вставляем обновленные строки расчета
            batch_size = 100
            total_rows = len(calculated_data)
            
            for i in range(0, total_rows, batch_size):
                batch = calculated_data[i:i + batch_size]
                
                for row in batch:
                    query_row = """
                    INSERT INTO СтрокиРасчетаНагрузки (
                        РасчетID, ИндексДисциплины, Дисциплина, Курс, Семестр, 
                        ВидРаботы, Часы, Недели, Кафедра, КонтингентПоДисциплине, 
                        ЧисленностьПотока, КоличествоПодгрупп, НепосредственноеУчастиеППС, 
                        Нагрузка, ПунктПриказа, Комментарий, Учитывать
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    
                    row_params = (
                        workload_id,
                        row.get('Индекс дисциплины', ''),
                        row.get('Дисциплина', ''),
                        row.get('Курс', None),
                        row.get('Семестр', None),
                        row.get('Вид работы', ''),
                        row.get('Часы', 0),
                        row.get('Недели', 0),
                        row.get('Название кафедры', ''),
                        row.get('Контингент по дисциплине', 0),
                        row.get('Численность потока', 0),
                        row.get('Количество подгрупп', 1),
                        1 if row.get('С непосредственным участием ППС', '') == 'on' else 0,
                        row.get('Нагрузка', 0),
                        row.get('Пункт приказа', ''),
                        row.get('Комментарии', ''),
                        1 if row.get('Учитывать', False) else 0
                    )
                    
                    execute_query(query_row, row_params)
            
            return True
        except Exception as e:
            print(f"Ошибка при обновлении расчета: {e}")
            return False
    
    @staticmethod
    def delete_workload(workload_id: int) -> bool:
        """
        Удаление расчета нагрузки
        
        Args:
            workload_id: ID расчета
            
        Returns:
            bool: True, если удаление успешно
        """
        try:
            query = "DELETE FROM РасчетыНагрузки WHERE ID = ?"
            execute_query(query, (workload_id,))
            return True
        except Exception as e:
            print(f"Ошибка при удалении расчета: {e}")
            return False