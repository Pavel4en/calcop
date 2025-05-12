from flask import Blueprint, render_template, session, request, jsonify
from app.controllers.auth_controller import login_required
from app.models.plans import StudyPlan
from app.models.norms import Norms
from app.models.formulas import Formula
from app.services.formula_executor import FormulaExecutor

calculation_bp = Blueprint('calculation', __name__, url_prefix='/calculation')

@calculation_bp.route('/calculate_workload', methods=['POST'])
@login_required
def calculate_workload_route():
    """Рассчитать учебную нагрузку и вывести результаты"""
    user_dict = session.get('user', {})
    
    # Получаем данные из формы
    data = request.form.to_dict()
    
    # Получаем данные учебного плана из исходного запроса
    academic_year = data.get('academic_year')
    admission_year = data.get('admission_year')
    plan_file = data.get('plan_file')
    show_all_disciplines = data.get('show_all_disciplines', '0') == '1'
    contingent = int(data.get('contingent', '1'))
    course = int(data.get('course', '1'))
    
    # Получаем данные учебного плана
    plan_data = StudyPlan.get_plan_data(academic_year, admission_year, plan_file, show_all_disciplines)
    
    # Фильтрация данных по курсу
    if course:
        plan_data = StudyPlan.filter_plan_data_by_course(plan_data, course)
    
    # Извлекаем код специальности
    specialty_code = StudyPlan.extract_specialty_code(plan_file)
    
    # Получаем информацию о программе из первой записи (если она есть)
    program_info = None
    if plan_data and len(plan_data) > 0:
        program_info = {
            'academic_year': academic_year,
            'admission_year': admission_year,
            'plan_file': plan_file,
            'specialty': plan_data[0][9] if len(plan_data[0]) > 9 else '',  # Титул
            'profile': plan_data[0][11] if len(plan_data[0]) > 11 else '',  # Специальность
            'department': plan_data[0][13] if len(plan_data[0]) > 13 else '',  # НазваниеПрофКафедры
            'education_form': plan_data[0][14] if len(plan_data[0]) > 14 else '',  # ФормаОбучения
            'specialty_code': specialty_code,
            'qualification': plan_data[0][8] if len(plan_data[0]) > 8 else '',  # Квалификация
            'contingent': contingent,
            'course': course
        }
    
    # Индексы колонок в результате запроса
    column_indices = {
        'ИндексДисциплины': 0,
        'Дисциплина': 1,
        'ВидРаботы': 2,
        'Курс': 3,
        'Семестр': 4,
        'Часы': 5,
        'Недели': 6,
        'КодКафедры': 7,
        'Квалификация': 8,
        'Титул': 9,
        'Факультет': 10,
        'Специальность': 11,
        'НазваниеКафедры': 12,
        'НазваниеПрофКафедры': 13,
        'ФормаОбучения': 14,
        'ПланКод': 15,
        'ЗЕТ': 16
    }
    
    # Получаем все нормы из базы данных
    norms_data = Norms.get_all_norms()
    db_norms = {norm['name']: norm['value'] for norm in norms_data}
    
    # Обновляем нормы из формы (если значения были изменены)
    norms = db_norms.copy()
    for key, value in data.items():
        if key.startswith('norm_') and value:
            norm_id = key[5:]  # Убираем префикс 'norm_'
            for norm in norms_data:
                if str(norm['id']) == norm_id:
                    norms[norm['name']] = float(value)
                    break
    
    # Получаем все формулы из базы данных
    formulas = Formula.get_all_formulas()
    
    # Подготавливаем данные для расчета и выполняем расчет
    calculated_data = []
    total_workload = 0
    total_credits = 0
    total_zet_hours = 0  # Общая сумма часов по видам работ "Руководство (ЗЕТ)"
    
    for row in plan_data:
        # Преобразуем данные из кортежа в словарь для удобства
        row_dict = {
            'Индекс дисциплины': row[column_indices['ИндексДисциплины']],
            'Дисциплина': row[column_indices['Дисциплина']],
            'Вид работы': row[column_indices['ВидРаботы']],
            'Курс': row[column_indices['Курс']],
            'Семестр': row[column_indices['Семестр']],
            'Часы': row[column_indices['Часы']],
            'Недели': row[column_indices['Недели']],
            'Название кафедры': row[column_indices['НазваниеКафедры']],
            'Квалификация': row[column_indices['Квалификация']],
            'Форма обучения': row[column_indices['ФормаОбучения']],
            'ЗЕТ': row[column_indices['ЗЕТ']],
            'Файл УП': plan_file,
            'Контингент по дисциплине': contingent,
            'Численность потока': contingent,
            'Количество подгрупп': 1,
            'С непосредственным участием ППС': 'off'  # По умолчанию выключено
        }
        
        # Учитываем значения из формы для этой строки
        row_id = f"{row_dict['Индекс дисциплины']}_{row_dict['Вид работы']}_{row_dict['Семестр']}"
        consider = data.get(f'consider_{row_id}', 'off') == 'on'
        
        if consider:
            row_dict['Контингент по дисциплине'] = int(data.get(f'contingent_{row_id}', contingent))
            row_dict['Численность потока'] = int(data.get(f'stream_{row_id}', contingent))
            row_dict['Количество подгрупп'] = int(data.get(f'subgroups_{row_id}', 1))
            row_dict['С непосредственным участием ППС'] = data.get(f'with_ppe_{row_id}', 'off')
            
            # Рассчитываем нагрузку для этой строки с использованием динамических формул
            workload = FormulaExecutor.calculate_workload(row_dict, norms, formulas)
            
            # Определяем пункт приказа
            order_point = FormulaExecutor.get_order_point(row_dict, formulas)
            
            # Учитываем в общей сумме нагрузки
            total_workload += workload
            
            # Учитываем кредиты для дисциплин, а не для видов работ
            if row_dict['Вид работы'] in ['Лекционные занятия', 'Практические занятия', 'Лабораторные занятия']:
                total_credits += float(row_dict['ЗЕТ']) if row_dict['ЗЕТ'] else 0
                
            # Суммируем часы по видам работ "Руководство (ЗЕТ)"
            if row_dict['Вид работы'] == 'Руководство (ЗЕТ)':
                hours = float(row_dict['Часы']) if row_dict['Часы'] else 0
                total_zet_hours += hours
                
        else:
            workload = 0
            order_point = ""
        
        # Добавляем рассчитанные значения в строку
        row_dict['Нагрузка'] = workload
        row_dict['Пункт приказа'] = order_point
        row_dict['Учитывать'] = consider
        
        calculated_data.append(row_dict)
    
    # Рассчитываем итоговые показатели
    norm_hours_per_position = float(norms.get('Норма времени на одну штатную единицу', 900))
    calculated_positions = round(total_workload / norm_hours_per_position, 2)
    cost_coefficient = round((contingent * norm_hours_per_position) / total_workload, 2) if total_workload > 0 else 0
    
    # Проверяем, превышает ли сумма часов по "Руководство (ЗЕТ)" 60 часов
    zet_hours_warning = total_zet_hours > 60
    
    # Формируем данные для отображения
    workload_summary = {
        'total_workload': round(total_workload, 2),
        'calculated_positions': calculated_positions,
        'cost_coefficient': cost_coefficient,
        'total_credits': round(total_credits, 2),
        'norm_hours_per_position': norm_hours_per_position,
        'total_zet_hours': round(total_zet_hours, 2),
        'zet_hours_warning': zet_hours_warning
    }
    
    # Список столбцов для отображения
    display_columns = [
        'Учитывать',
        'ИндексДисциплины', 
        'Дисциплина', 
        'Курс', 
        'Семестр', 
        'ВидРаботы', 
        'Часы', 
        'Недели', 
        'НазваниеКафедры',
        'Контингент по дисциплине',
        'Численность потока',
        'Количество подгрупп',
        'Нагрузка',
        'Пункт приказа',
        'Комментарии'
    ]
    
    # Сохраняем результаты в сессию для возможного последующего сохранения
    # Flask-Session автоматически обработает сериализацию больших данных
    session['calculated_data'] = calculated_data
    session['workload_summary'] = workload_summary
    session['program_info'] = program_info
    session['contingent'] = contingent
    session['course'] = course
    session.modified = True  # Помечаем сессию как измененную

    return render_template('dashboard/workload_results.html', 
                          user=user_dict,
                          program_info=program_info,
                          workload_summary=workload_summary,
                          calculated_data=calculated_data,
                          display_columns=display_columns,
                          contingent=contingent)