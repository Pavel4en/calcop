from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify
from app.controllers.auth_controller import login_required
from app.models.saved_workload import SavedWorkload
from app.models.settings import Settings
from app.models.norms import Norms
from app.models.formulas import Formula
from app.services.formula_executor import FormulaExecutor

workload_bp = Blueprint('workload', __name__, url_prefix='/workload')

@workload_bp.route('/save', methods=['POST'])
@login_required
def save_workload():
    """Сохранение расчета нагрузки в личный кабинет"""
    user_dict = session.get('user', {})
    user_id = user_dict.get('id')
    
    if not user_id:
        flash('Пожалуйста, авторизуйтесь для сохранения расчета', 'error')
        return redirect(url_for('auth.login'))
    
    # Получаем данные из формы
    title = request.form.get('workload_title', 'Расчёт нагрузки')
    comment = request.form.get('workload_comment', '')
    
    # Получаем данные из сессии (последний расчет)
    calculated_data = session.get('calculated_data', [])
    workload_summary = session.get('workload_summary', {})
    program_info = session.get('program_info', {})
    contingent = session.get('contingent', 0)
    course = session.get('course', None)
    
    # Собираем все данные в один словарь
    data = {
        'calculated_data': calculated_data,
        'workload_summary': workload_summary,
        'program_info': program_info,
        'contingent': contingent,
        'course': course
    }
    
    try:
        # Сохраняем расчет в БД
        workload_id = SavedWorkload.save_workload(user_id, title, data, comment)
        
        # Очищаем данные из сессии после успешного сохранения
        session.pop('calculated_data', None)
        session.pop('workload_summary', None)
        session.pop('program_info', None)
        session.pop('contingent', None)
        session.pop('course', None)
        session.modified = True  # Помечаем сессию как измененную
        
        flash(f'Расчет "{title}" успешно сохранен', 'success')
        return redirect(url_for('workload.my_workloads'))
    except Exception as e:
        flash(f'Ошибка при сохранении расчета: {str(e)}', 'error')
        return redirect(url_for('main.index'))

@workload_bp.route('/my-workloads')
@login_required
def my_workloads():
    """Страница со списком сохраненных расчетов"""
    user_dict = session.get('user', {})
    user_id = user_dict.get('id')
    
    # Получаем сохраненные расчеты пользователя
    workloads = SavedWorkload.get_user_workloads(user_id)
    
    # Загружаем настройки для боковой панели
    settings = Settings.get_all_settings()
    
    return render_template('dashboard/workload/my_workloads.html', 
                           user=user_dict, 
                           workloads=workloads,
                           settings=settings)

@workload_bp.route('/view/<int:workload_id>')
@login_required
def view_workload(workload_id):
    """Просмотр сохраненного расчета нагрузки"""
    user_dict = session.get('user', {})
    
    # Получаем данные расчета
    workload_data = SavedWorkload.get_workload_by_id(workload_id)
    
    if not workload_data:
        flash('Расчет не найден', 'error')
        return redirect(url_for('workload.my_workloads'))
    
    # Загружаем настройки для боковой панели
    settings = Settings.get_all_settings()
    
    return render_template('dashboard/workload/view_workload.html',
                           user=user_dict,
                           program_info=workload_data.get('program_info', {}),
                           workload_summary=workload_data.get('workload_summary', {}),
                           calculated_data=workload_data.get('calculated_data', []),
                           workload=workload_data,
                           contingent=workload_data.get('contingent', 0),
                           settings=settings)

@workload_bp.route('/delete/<int:workload_id>', methods=['POST'])
@login_required
def delete_workload(workload_id):
    """Удаление сохраненного расчета"""
    user_dict = session.get('user', {})
    user_id = user_dict.get('id')
    
    # Проверяем права пользователя
    workload_data = SavedWorkload.get_workload_by_id(workload_id)
    
    if not workload_data:
        return jsonify({'success': False, 'error': 'Расчет не найден'})
    
    if workload_data['user_id'] != user_id and not user_dict.get('is_admin', False):
        return jsonify({'success': False, 'error': 'У вас нет прав на удаление этого расчета'})
    
    # Удаляем расчет
    success = SavedWorkload.delete_workload(workload_id)
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Ошибка при удалении расчета'})

@workload_bp.route('/get_full_data/<int:workload_id>')
@login_required
def get_full_data(workload_id):
    """Получение полных данных расчета (включая скрытые строки)"""
    workload_data = SavedWorkload.get_workload_by_id(workload_id, include_hidden=True)
    
    if not workload_data:
        return jsonify({'success': False, 'error': 'Расчет не найден'})
    
    return jsonify({
        'success': True,
        'calculated_data': workload_data.get('calculated_data', [])
    })

@workload_bp.route('/recalculate/<int:workload_id>', methods=['POST'])
@login_required
def recalculate_workload(workload_id):
    """Пересчет нагрузки с новыми параметрами"""
    try:
        # Получаем существующий расчет
        workload_data = SavedWorkload.get_workload_by_id(workload_id)
        
        if not workload_data:
            return jsonify({'success': False, 'error': 'Расчет не найден'})
        
        # Получаем данные из формы
        form_data = request.form.to_dict()
        
        # Получаем нормы из БД
        norms_data = Norms.get_all_norms()
        norms = {norm['name']: norm['value'] for norm in norms_data}
        
        # Получаем формулы из БД
        formulas = Formula.get_all_formulas()
        
        # Обновляем данные расчета из формы
        calculated_data = workload_data.get('calculated_data', [])
        
        # Обработка данных формы и пересчет
        total_workload = 0
        total_zet_hours = 0
        
        for row in calculated_data:
            row_id = f"{row['Индекс дисциплины']}_{row['Вид работы']}_{row['Семестр']}"
            
            # Обновляем данные из формы
            if f'consider_{row_id}' in form_data:
                row['Учитывать'] = form_data.get(f'consider_{row_id}', 'off') == 'on'
            
            if row['Учитывать']:
                # Обновляем параметры из формы
                if f'contingent_{row_id}' in form_data:
                    row['Контингент по дисциплине'] = int(form_data.get(f'contingent_{row_id}', 1))
                if f'stream_{row_id}' in form_data:
                    row['Численность потока'] = int(form_data.get(f'stream_{row_id}', 1))
                if f'subgroups_{row_id}' in form_data:
                    row['Количество подгрупп'] = int(form_data.get(f'subgroups_{row_id}', 1))
                if f'with_ppe_{row_id}' in form_data:
                    row['С непосредственным участием ППС'] = form_data.get(f'with_ppe_{row_id}', 'off')
                
                # Пересчитываем нагрузку
                workload = FormulaExecutor.calculate_workload(row, norms, formulas)
                order_point = FormulaExecutor.get_order_point(row, formulas)
                
                row['Нагрузка'] = workload
                row['Пункт приказа'] = order_point
                
                total_workload += workload
                
                # Подсчет часов ЗЕТ
                if row['Вид работы'] == 'Руководство (ЗЕТ)':
                    hours = float(row['Часы']) if row['Часы'] else 0
                    total_zet_hours += hours
            else:
                row['Нагрузка'] = 0
                row['Пункт приказа'] = ""
        
        # Обновляем итоговые показатели
        norm_hours_per_position = float(norms.get('Норма времени на одну штатную единицу', 900))
        calculated_positions = round(total_workload / norm_hours_per_position, 2)
        contingent = workload_data.get('contingent', 1)
        cost_coefficient = round((contingent * norm_hours_per_position) / total_workload, 2) if total_workload > 0 else 0
        
        workload_summary = {
            'total_workload': round(total_workload, 2),
            'calculated_positions': calculated_positions,
            'cost_coefficient': cost_coefficient,
            'total_zet_hours': round(total_zet_hours, 2),
            'norm_hours_per_position': norm_hours_per_position
        }
        
        # Обновляем данные в сессии для временного использования
        session['recalc_data'] = {
            'calculated_data': calculated_data,
            'workload_summary': workload_summary
        }
        session.modified = True
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@workload_bp.route('/update/<int:workload_id>', methods=['POST'])
@login_required
def update_workload(workload_id):
    """Обновление расчета нагрузки с новыми данными"""
    user_dict = session.get('user', {})
    user_id = user_dict.get('id')
    
    try:
        # Получаем существующий расчет
        workload_data = SavedWorkload.get_workload_by_id(workload_id)
        
        if not workload_data:
            return jsonify({'success': False, 'error': 'Расчет не найден'})
        
        # Проверяем права пользователя
        if workload_data['user_id'] != user_id and not user_dict.get('is_admin', False):
            return jsonify({'success': False, 'error': 'У вас нет прав на редактирование этого расчета'})
        
        # Получаем данные из формы
        form_data = request.form.to_dict()
        
        # Получаем нормы из БД
        norms_data = Norms.get_all_norms()
        norms = {norm['name']: norm['value'] for norm in norms_data}
        
        # Получаем формулы из БД
        formulas = Formula.get_all_formulas()
        
        # Обновляем данные расчета из формы
        calculated_data = workload_data.get('calculated_data', [])
        
        # Обработка данных формы и пересчет
        total_workload = 0
        total_zet_hours = 0
        total_credits = 0
        
        for row in calculated_data:
            row_id = f"{row['Индекс дисциплины']}_{row['Вид работы']}_{row['Семестр']}"
            
            # Обновляем данные из формы
            if f'consider_{row_id}' in form_data:
                row['Учитывать'] = form_data.get(f'consider_{row_id}', 'off') == 'on'
            
            if row['Учитывать']:
                # Обновляем параметры из формы
                if f'contingent_{row_id}' in form_data:
                    row['Контингент по дисциплине'] = int(form_data.get(f'contingent_{row_id}', 1))
                if f'stream_{row_id}' in form_data:
                    row['Численность потока'] = int(form_data.get(f'stream_{row_id}', 1))
                if f'subgroups_{row_id}' in form_data:
                    row['Количество подгрупп'] = int(form_data.get(f'subgroups_{row_id}', 1))
                if f'with_ppe_{row_id}' in form_data:
                    row['С непосредственным участием ППС'] = form_data.get(f'with_ppe_{row_id}', 'off')
                if f'comment_{row_id}' in form_data:
                    row['Комментарии'] = form_data.get(f'comment_{row_id}', '')
                
                # Пересчитываем нагрузку
                workload = FormulaExecutor.calculate_workload(row, norms, formulas)
                order_point = FormulaExecutor.get_order_point(row, formulas)
                
                row['Нагрузка'] = workload
                row['Пункт приказа'] = order_point
                
                total_workload += workload
                
                # Подсчет часов ЗЕТ
                if row['Вид работы'] == 'Руководство (ЗЕТ)':
                    hours = float(row['Часы']) if row['Часы'] else 0
                    total_zet_hours += hours
                
                # Учитываем кредиты для дисциплин
                if row['Вид работы'] in ['Лекционные занятия', 'Практические занятия', 'Лабораторные занятия']:
                    total_credits += float(row['ЗЕТ']) if row.get('ЗЕТ') else 0
            else:
                row['Нагрузка'] = 0
                row['Пункт приказа'] = ""
        
        # Обновляем итоговые показатели
        norm_hours_per_position = float(norms.get('Норма времени на одну штатную единицу', 900))
        calculated_positions = round(total_workload / norm_hours_per_position, 2)
        contingent = workload_data.get('contingent', 1)
        cost_coefficient = round((contingent * norm_hours_per_position) / total_workload, 2) if total_workload > 0 else 0
        
        workload_summary = {
            'total_workload': round(total_workload, 2),
            'calculated_positions': calculated_positions,
            'cost_coefficient': cost_coefficient,
            'total_credits': round(total_credits, 2),
            'total_zet_hours': round(total_zet_hours, 2),
            'norm_hours_per_position': norm_hours_per_position,
            'zet_hours_warning': total_zet_hours > 60
        }
        
        # Обновляем данные для сохранения
        updated_data = {
            'calculated_data': calculated_data,
            'workload_summary': workload_summary,
            'program_info': workload_data.get('program_info', {}),
            'contingent': contingent,
            'course': workload_data.get('course', None)
        }
        
        # Обновляем расчет в БД
        success = SavedWorkload.update_workload(workload_id, updated_data)
        
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Ошибка при обновлении расчета'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})