from app.utils import execute_query
from typing import List, Dict, Any, Optional, Tuple

class StudyPlan:
    @staticmethod
    def get_academic_years() -> List[Tuple]:
        """Получение списка учебных годов"""
        query = "SELECT DISTINCT УчебныйГод FROM Планы ORDER BY УчебныйГод DESC"
        return execute_query(query, fetch_all=True)

    @staticmethod
    def get_admission_years(academic_year: str) -> List[Tuple]:
        """Получение списка годов набора по учебному году"""
        query = "SELECT DISTINCT ГодНачалаПодготовки FROM Планы WHERE УчебныйГод = ? ORDER BY ГодНачалаПодготовки DESC"
        return execute_query(query, (academic_year,), fetch_all=True)

    @staticmethod
    def get_plan_files(academic_year: str, admission_year: str) -> List[Tuple]:
        """Получение списка файлов учебных планов по годам"""
        query = "SELECT DISTINCT ИмяФайла FROM Планы WHERE ГодНачалаПодготовки = ? AND УчебныйГод = ? ORDER BY ИмяФайла"
        return execute_query(query, (admission_year, academic_year), fetch_all=True)

    @staticmethod
    def get_plan_data(academic_year: str, admission_year: str, plan_file: str, show_all_disciplines: bool) -> List[Tuple]:
        """Получение данных учебного плана"""
        # Если show_all_disciplines = True, то выводим и СчитатьВПлане=0, и СчитатьВПлане=1
        # Если show_all_disciplines = False, то выводим только СчитатьВПлане=1
        query = """
        SELECT 
            PS.ДисциплинаКод AS ИндексДисциплины, 
            PS.Дисциплина, 
            SVR.Название AS ВидРаботы, 
            PNC.Курс, 
            (PNC.Курс - 1) * 2 + PNC.Семестр AS Семестр, 
            PNC.Количество AS Часы, 
            PNC.Недель AS Недели, 
            PS.КодКафедры, 
            P.Квалификация, 
            P.Титул, 
            FCT.Факультет AS Факультет, 
            OOP.Название AS Специальность, 
            K.Название AS НазваниеКафедры, 
            PK.Название AS НазваниеПрофКафедры, 
            F.ФормаОбучения AS ФормаОбучения, 
            P.Код AS ПланКод, 
            PS.ТрудоемкостьКредитов AS ЗЕТ 
        FROM ПланыНовыеЧасы AS PNC 
        JOIN ПланыСтроки AS PS ON PNC.КодОбъекта = PS.Код 
        JOIN Планы AS P ON PS.КодПлана = P.Код 
        JOIN СправочникВидыРабот AS SVR ON PNC.КодВидаРаботы = SVR.Код 
        LEFT JOIN Кафедры AS K ON PS.КодКафедры = K.Номер 
        LEFT JOIN Кафедры AS PK ON P.КодПрофКафедры = PK.Номер 
        JOIN ФормаОбучения AS F ON P.КодФормыОбучения = F.Код 
        LEFT JOIN Факультеты AS FCT ON P.КодФакультета = FCT.Код 
        LEFT JOIN ООП AS OOP ON P.КодАктивногоООП = OOP.Код 
        WHERE P.ИмяФайла = ? 
        AND P.ГодНачалаПодготовки = ? 
        AND P.УчебныйГод = ? 
        AND PNC.КодТипаЧасов = 1 
        AND PS.КодКафедры IS NOT NULL 
        AND PS.Дисциплина NOT IN ('Основной профессиональный модуль специальных дисциплин') 
        AND SVR.Название NOT IN ('Самостоятельная работа', 'Часы на контроль', 'Контроль самостоятельной работы', 
                                'Председатель', 'Член комиссии', 'Секретарь', 'Консультации')
        """
        
        # Добавляем условие для СчитатьВПлане только если не показываем все дисциплины
        if not show_all_disciplines:
            query += " AND PS.СчитатьВПлане = 1"
            
        query += " ORDER BY ИндексДисциплины, Семестр, ВидРаботы"
        
        plan_data = execute_query(query, (plan_file, admission_year, academic_year), fetch_all=True)
        
        # Применяем дополнительные преобразования к данным
        plan_data = StudyPlan.process_plan_data(plan_data)
        
        return plan_data
    
    @staticmethod
    def process_plan_data(plan_data: List[Tuple]) -> List[Tuple]:
        """
        Обработка данных учебного плана: применение всех необходимых трансформаций
        """
        # Сначала переименовываем виды работ
        plan_data = StudyPlan.rename_work_types(plan_data)
        
        # Затем добавляем фиктивные строки для ГИА магистров
        plan_data = StudyPlan.add_fake_gia_rows(plan_data)
        
        # Удаляем строки "Руководство (в рамках ГИА)" и "Рецензирование" для госэкзаменов
        plan_data = StudyPlan.remove_gia_rows_for_state_exams(plan_data)
        
        return plan_data
    
    @staticmethod
    def remove_gia_rows_for_state_exams(plan_data: List[Tuple]) -> List[Tuple]:
        """
        Удаление строк с видами работ "Руководство (в рамках ГИА)" и "Рецензирование"
        для дисциплин, содержащих "государственного экзамена"
        
        Args:
            plan_data: Исходные данные учебного плана
                
        Returns:
            Данные учебного плана без строк ГИА для госэкзаменов
        """
        # Индексы колонок
        discipline_index = 1      # Дисциплина
        work_type_index = 2       # ВидРаботы
        
        # Отфильтрованный список строк
        filtered_data = []
        
        for row in plan_data:
            discipline_name = str(row[discipline_index]).lower()
            work_type = str(row[work_type_index])
            
            # Проверяем, содержит ли название дисциплины "государственного экзамена"
            if "государственного экзамена" in discipline_name:
                # Если да, пропускаем строки с указанными видами работ
                if work_type in ["Руководство (в рамках ГИА)", "Рецензирование"]:
                    continue
            
            # Добавляем все остальные строки в результат
            filtered_data.append(row)
        
        return filtered_data
        
    @staticmethod
    def rename_work_types(plan_data: List[Tuple]) -> List[Tuple]:
        """
        Переименование видов работ "ЗЕТ" в "Руководство (ЗЕТ)" или "Руководство проектной деятельности"
        
        Args:
            plan_data: Исходные данные учебного плана
            
        Returns:
            Обработанные данные учебного плана с переименованными видами работ
        """
        processed_data = []
        
        for row in plan_data:
            # Преобразуем кортеж в список для возможности изменения
            row_list = list(row)
            
            # Индексы колонок
            discipline_index = 1  # Дисциплина
            work_type_index = 2  # ВидРаботы
            
            # Переименование вида работ "ЗЕТ"
            if row_list[work_type_index] == "ЗЕТ":
                if row_list[discipline_index] == "Проектная деятельность":
                    row_list[work_type_index] = "Руководство проектной деятельности"
                else:
                    row_list[work_type_index] = "Руководство (ЗЕТ)"
            
            # Добавляем обработанную строку в результат
            processed_data.append(tuple(row_list))
            
        return processed_data
        
    @staticmethod
    def add_fake_gia_rows(plan_data: List[Tuple]) -> List[Tuple]:
        """
        Добавление фиктивных строк для ГИА и рецензирования,
        а также удаление ненужных строк для бакалавров
        
        Args:
            plan_data: Исходные данные учебного плана
            
        Returns:
            Обработанные данные учебного плана с добавленными фиктивными строками
        """
        processed_data = []
        gia_rows_to_add = []
        
        # Индексы колонок
        discipline_code_index = 0  # ИндексДисциплины
        discipline_index = 1      # Дисциплина
        work_type_index = 2       # ВидРаботы
        course_index = 3          # Курс
        semester_index = 4        # Семестр
        hours_index = 5           # Часы
        qualification_index = 8   # Квалификация
        
        # Для проверки существующих строк
        existing_rows = set()
        
        # Наполняем множество существующих строк
        for row in plan_data:
            # Создаем уникальный ключ для проверки (дисциплина, курс, семестр, вид работы)
            key = (
                row[discipline_code_index], 
                row[course_index], 
                row[semester_index], 
                row[work_type_index]
            )
            existing_rows.add(key)
        
        # Фильтруем строки, удаляя "Рецензирование" для бакалавров
        filtered_data = []
        for row in plan_data:
            qualification_lower = str(row[qualification_index]).lower()
            
            # Проверяем, является ли это строкой "Рецензирование" для бакалавра, которую нужно удалить
            if (qualification_lower == "бакалавр" and 
                row[work_type_index] == "Рецензирование" and
                row[discipline_code_index].startswith("Б3") and
                (row[course_index] == 4 or row[course_index] == 5)):
                # Пропускаем эту строку (не добавляем в filtered_data)
                continue
                
            # Добавляем остальные строки
            filtered_data.append(row)
        
        # Заменяем plan_data на filtered_data для дальнейшей обработки
        plan_data = filtered_data
        
        for row in plan_data:
            # Преобразуем кортеж в список для возможности изменения
            row_list = list(row)
            
            # Получаем значение квалификации в нижнем регистре для регистронезависимого сравнения
            qualification_lower = str(row_list[qualification_index]).lower()
            
            # Проверка для магистров
            if (qualification_lower == "магистр" and 
                row_list[course_index] == 2 and
                row_list[semester_index] == 4 and
                row_list[discipline_code_index].startswith("Б3")):
                
                # Добавляем фиктивные строки для семестров 1, 2, 3 для "Руководство (в рамках ГИА)"
                if row_list[work_type_index] == "Руководство (в рамках ГИА)":
                    for sem in range(1, 4):
                        # Создаем копию текущей строки
                        fake_row = row_list.copy()
                        # Меняем семестр на текущий семестр цикла
                        calc_course = (sem - 1) // 2 + 1
                        fake_row[course_index] = calc_course  # Курс
                        fake_row[semester_index] = sem  # Семестр
                        fake_row[hours_index] = 1  # Часы = 1
                        
                        # Проверяем, не существует ли уже такая строка
                        key = (fake_row[discipline_code_index], fake_row[course_index], 
                            fake_row[semester_index], fake_row[work_type_index])
                        if key not in existing_rows:
                            gia_rows_to_add.append(tuple(fake_row))
                            existing_rows.add(key)
                
                # Добавляем строку "Рецензирование" с часами 0
                key = (row_list[discipline_code_index], 2, 4, "Рецензирование")
                if key not in existing_rows:
                    review_row = row_list.copy()
                    review_row[work_type_index] = "Рецензирование"
                    review_row[hours_index] = 0
                    gia_rows_to_add.append(tuple(review_row))
                    existing_rows.add(key)
                
            # Проверка для бакалавров
            elif (qualification_lower == "бакалавр"):
                # Для 4 курса, 8 семестра
                if (row_list[course_index] == 4 and
                    row_list[semester_index] == 8 and
                    row_list[discipline_code_index].startswith("Б3")):
                    
                    # Добавляем "Руководство (в рамках ГИА)" с часами 1
                    key = (row_list[discipline_code_index], 4, 8, "Руководство (в рамках ГИА)")
                    if key not in existing_rows:
                        gia_row = row_list.copy()
                        gia_row[work_type_index] = "Руководство (в рамках ГИА)"
                        gia_row[hours_index] = 1
                        gia_rows_to_add.append(tuple(gia_row))
                        existing_rows.add(key)
                
                # Для 5 курса, 10 семестра (если есть)
                elif (row_list[course_index] == 5 and
                    row_list[semester_index] == 10 and
                    row_list[discipline_code_index].startswith("Б3")):
                    
                    # Добавляем "Руководство (в рамках ГИА)" с часами 1
                    key = (row_list[discipline_code_index], 5, 10, "Руководство (в рамках ГИА)")
                    if key not in existing_rows:
                        gia_row = row_list.copy()
                        gia_row[work_type_index] = "Руководство (в рамках ГИА)"
                        gia_row[hours_index] = 1
                        gia_rows_to_add.append(tuple(gia_row))
                        existing_rows.add(key)
            
            # Проверка для остальных (не магистр и не бакалавр)
            elif (qualification_lower != "магистр" and qualification_lower != "бакалавр"):
                # Для 5 курса, 10 семестра
                if (row_list[course_index] == 5 and
                    row_list[semester_index] == 10 and
                    row_list[discipline_code_index].startswith("Б3")):
                    
                    # Добавляем "Руководство (в рамках ГИА)" с часами 1
                    key = (row_list[discipline_code_index], 5, 10, "Руководство (в рамках ГИА)")
                    if key not in existing_rows:
                        gia_row = row_list.copy()
                        gia_row[work_type_index] = "Руководство (в рамках ГИА)"
                        gia_row[hours_index] = 1
                        gia_rows_to_add.append(tuple(gia_row))
                        existing_rows.add(key)
                    
                    # Добавляем "Рецензирование" с часами 0
                    key = (row_list[discipline_code_index], 5, 10, "Рецензирование")
                    if key not in existing_rows:
                        review_row = row_list.copy()
                        review_row[work_type_index] = "Рецензирование"
                        review_row[hours_index] = 0
                        gia_rows_to_add.append(tuple(review_row))
                        existing_rows.add(key)
                
                # Для 6 курса, 12 семестра
                elif (row_list[course_index] == 6 and
                    row_list[semester_index] == 12 and
                    row_list[discipline_code_index].startswith("Б3")):
                    
                    # Добавляем "Руководство (в рамках ГИА)" с часами 1
                    key = (row_list[discipline_code_index], 6, 12, "Руководство (в рамках ГИА)")
                    if key not in existing_rows:
                        gia_row = row_list.copy()
                        gia_row[work_type_index] = "Руководство (в рамках ГИА)"
                        gia_row[hours_index] = 1
                        gia_rows_to_add.append(tuple(gia_row))
                        existing_rows.add(key)
                    
                    # Добавляем "Рецензирование" с часами 0
                    key = (row_list[discipline_code_index], 6, 12, "Рецензирование")
                    if key not in existing_rows:
                        review_row = row_list.copy()
                        review_row[work_type_index] = "Рецензирование"
                        review_row[hours_index] = 0
                        gia_rows_to_add.append(tuple(review_row))
                        existing_rows.add(key)
            
            # Добавляем исходную строку в результат
            processed_data.append(tuple(row_list))
        
        # Добавляем фиктивные строки
        processed_data.extend(gia_rows_to_add)
        
        # Сортируем результат
        processed_data.sort(key=lambda x: (x[0], x[3], x[4], x[2]))
        
        return processed_data
    
    @staticmethod
    def filter_plan_data_by_course(plan_data: List[Tuple], course: Optional[int] = None) -> List[Tuple]:
        """
        Фильтрация данных учебного плана по курсу
        
        Args:
            plan_data: Данные учебного плана
            course: Номер курса для фильтрации (None - без фильтрации)
            
        Returns:
            Отфильтрованные данные учебного плана
        """
        if course is None:
            return plan_data
        
        # Индекс колонки "Курс"
        course_index = 3
        
        # Фильтруем строки по курсу
        filtered_data = [row for row in plan_data if row[course_index] == course]
        
        return filtered_data
    
    @staticmethod
    def calculate_course(admission_year: str, academic_year: str = None) -> int:
        """
        Расчет курса на основе года набора и года реализации
        
        Args:
            admission_year: Год набора
            academic_year: Год реализации в формате 'YYYY-YYYY' (если не указан, используется максимальный из БД)
        
        Returns:
            int: Номер курса
        """
        try:
            admission_year_int = int(admission_year)
            
            # Если год реализации передан, извлекаем из него первый год
            if academic_year:
                # Предполагаем формат "2025-2026", берем первую часть
                first_year_str = academic_year.split('-')[0]
                max_year = int(first_year_str)
            else:
                # Иначе получаем максимальный год реализации из базы данных
                max_year_query = "SELECT MAX(УчебныйГод) FROM Планы"
                max_year_result = execute_query(max_year_query, fetch_one=True)
                
                if not max_year_result or not max_year_result[0]:
                    # Если не удалось получить значение из базы данных, возвращаем 1
                    return 1
                else:
                    # Если результат в формате "2025-2026", извлекаем первый год
                    max_year_str = str(max_year_result[0])
                    if '-' in max_year_str:
                        max_year = int(max_year_str.split('-')[0])
                    else:
                        max_year = int(max_year_str)
            
            # Формула: год реализации - год набора + 1
            course = max_year - admission_year_int + 1
            
            # Отладочная информация
            print(f"Расчет курса: {max_year} - {admission_year_int} + 1 = {course}")
            
            # Проверка на допустимые значения
            return max(1, course)
        except Exception as e:
            print(f"Ошибка при расчете курса: {e}")
            return 1
            
    @staticmethod
    def extract_specialty_code(plan_file: str) -> str:
        """
        Извлекает код специальности из названия файла плана (формат XX.XX.XX)
        
        Args:
            plan_file: Название файла учебного плана
            
        Returns:
            str: Код специальности или пустая строка
        """
        import re
        try:
            # Ищем шаблон вида XX.XX.XX
            pattern = r'\d{2}\.\d{2}\.\d{2}'
            match = re.search(pattern, plan_file)
            if match:
                return match.group(0)
            return ""
        except Exception as e:
            print(f"Ошибка при извлечении кода специальности: {e}")
            return ""