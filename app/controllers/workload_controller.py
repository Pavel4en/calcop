from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify
from app.controllers.auth_controller import login_required
from app.models.saved_workload import SavedWorkload
from app.models.settings import Settings

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