from flask import Blueprint, render_template, session, request
from app.controllers.auth_controller import login_required
from app.models.plans import StudyPlan
from app.models.norms import Norms

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index():
    user_dict = session.get('user', {})
    
    # Получение годов реализации для селекта
    academic_years = StudyPlan.get_academic_years()
    
    return render_template('dashboard/index.html', user=user_dict, academic_years=academic_years)

@main_bp.route('/get_admission_years', methods=['GET'])
@login_required
def get_admission_years():
    academic_year = request.args.get('academic_year')
    
    if not academic_year:
        return "Не указан учебный год", 400
    
    # Получение годов набора для выбранного учебного года
    admission_years = StudyPlan.get_admission_years(academic_year)
    
    return render_template('dashboard/partials/admission_years.html', 
                           admission_years=admission_years)

@main_bp.route('/get_plan_files', methods=['GET'])
@login_required
def get_plan_files():
    academic_year = request.args.get('academic_year')
    admission_year = request.args.get('admission_year')
    
    if not academic_year or not admission_year:
        return "Не указаны необходимые параметры", 400
    
    # Получение файлов учебного плана
    plan_files = StudyPlan.get_plan_files(academic_year, admission_year)
    
    # Расчет курса, передаем год реализации
    course = StudyPlan.calculate_course(admission_year, academic_year)
    
    return render_template('dashboard/partials/plan_files.html', 
                           plan_files=plan_files, 
                           course=course)

@main_bp.route('/load_study_plan', methods=['GET'])
@login_required
def load_study_plan():
    # Получение параметров из формы
    academic_year = request.args.get('academic_year')
    admission_year = request.args.get('admission_year')
    plan_file = request.args.get('plan_file')
    show_all_disciplines = request.args.get('show_all_disciplines', '0') == '1'
    contingent = request.args.get('contingent', '1')
    
    # Получаем курс для фильтрации данных
    course_str = request.args.get('course')
    course = int(course_str) if course_str and course_str.isdigit() else None
    
    if not academic_year or not admission_year or not plan_file:
        return "Не указаны необходимые параметры", 400
    
    # Получение данных учебного плана
    plan_data = StudyPlan.get_plan_data(academic_year, admission_year, plan_file, show_all_disciplines)
    
    # Фильтрация данных по курсу (если указан)
    if course is not None:
        plan_data = StudyPlan.filter_plan_data_by_course(plan_data, course)
    
    # Извлекаем код специальности
    specialty_code = StudyPlan.extract_specialty_code(plan_file)
    
    # Получаем информацию о программе из первой записи (если она есть)
    program_info = None
    if plan_data and len(plan_data) > 0:
        program_info = {
            'academic_year': academic_year,
            'admission_year': admission_year,
            'specialty': plan_data[0][9] if len(plan_data[0]) > 9 else '',  # Титул
            'profile': plan_data[0][11] if len(plan_data[0]) > 11 else '',  # Специальность
            'department': plan_data[0][13] if len(plan_data[0]) > 13 else '',  # НазваниеПрофКафедры
            'education_form': plan_data[0][14] if len(plan_data[0]) > 14 else '',  # ФормаОбучения
            'specialty_code': specialty_code,
            'qualification': plan_data[0][8] if len(plan_data[0]) > 8 else ''  # Квалификация
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
        'Комментарии'
    ]
    
    # Определяем столбцы с тултипами
    tooltip_columns = [
        'Учитывать',
        'Недели',
        'Контингент по дисциплине',
        'Численность потока',
        'Количество подгрупп'
    ]
    
    # Индексы колонок в результате запроса для тех, что приходят из БД
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
    
    return render_template('dashboard/partials/study_plan_table.html', 
                           plan_data=plan_data, 
                           display_columns=display_columns,
                           column_indices=column_indices,
                           program_info=program_info,
                           contingent=contingent,
                           tooltip_columns=tooltip_columns)

@main_bp.route('/get_norms', methods=['GET'])
@login_required
def get_norms():
    # Получение норм из базы данных
    norms_data = Norms.get_all_norms()
    
    return render_template('dashboard/partials/norms_form.html', 
                           norms=norms_data)