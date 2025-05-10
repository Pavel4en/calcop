from flask import Blueprint, render_template, request, jsonify, session
from app.controllers.auth_controller import admin_required
from app.models.norms import Norms
from app.models.settings import Settings

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

@settings_bp.route('/')
@admin_required
def index():
    """Страница настроек"""
    user_dict = session.get('user', {})
    
    # Создаем таблицу настроек, если она не существует
    Settings.create_settings_table()
    
    return render_template('dashboard/settings.html', user=user_dict)

# API для управления нормами
@settings_bp.route('/api/norms', methods=['GET'])
@admin_required
def get_all_norms_api():
    """API для получения всех норм"""
    norms_data = Norms.get_all_norms()
    return jsonify(norms_data)

@settings_bp.route('/api/norms/<int:norm_id>', methods=['GET'])
@admin_required
def get_norm_api(norm_id):
    """API для получения конкретной нормы по ID"""
    norm = Norms.get_norm_by_id(norm_id)
    if not norm:
        return jsonify({'error': 'Норма не найдена'}), 404
    return jsonify(norm)

@settings_bp.route('/api/norms', methods=['POST'])
@admin_required
def create_norm_api():
    """API для создания новой нормы"""
    if not request.is_json:
        return jsonify({'error': 'Неверный формат данных'}), 400
        
    data = request.json
    name = data.get('name')
    value = data.get('value')
    locked = data.get('locked', False)
    
    if not name or value is None:
        return jsonify({'error': 'Не указаны обязательные параметры'}), 400
    
    try:
        norm_id = Norms.create_norm(name, value, locked)
        return jsonify({'id': norm_id, 'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/api/norms/<int:norm_id>', methods=['PUT'])
@admin_required
def update_norm_api(norm_id):
    """API для обновления существующей нормы"""
    if not request.is_json:
        return jsonify({'error': 'Неверный формат данных'}), 400
        
    data = request.json
    name = data.get('name')
    value = data.get('value')
    locked = data.get('locked')
    
    if not name and value is None and locked is None:
        return jsonify({'error': 'Не указаны параметры для обновления'}), 400
    
    try:
        success = Norms.update_norm(norm_id, name, value, locked)
        if not success:
            return jsonify({'error': 'Норма не найдена'}), 404
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/api/norms/<int:norm_id>', methods=['DELETE'])
@admin_required
def delete_norm_api(norm_id):
    """API для удаления нормы"""
    try:
        success = Norms.delete_norm(norm_id)
        if not success:
            return jsonify({'error': 'Норма не найдена'}), 404
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API для управления настройками
@settings_bp.route('/api/settings', methods=['GET'])
@admin_required
def get_all_settings_api():
    """API для получения всех настроек калькулятора"""
    settings_data = Settings.get_all_settings()
    return jsonify(settings_data)

@settings_bp.route('/api/settings/<string:key>', methods=['GET'])
@admin_required
def get_setting_api(key):
    """API для получения конкретной настройки по ключу"""
    value = Settings.get_setting(key)
    if value is None:
        return jsonify({'error': 'Настройка не найдена'}), 404
    return jsonify({key: value})

@settings_bp.route('/api/settings', methods=['POST'])
@admin_required
def update_settings_api():
    """API для обновления настроек калькулятора"""
    if not request.is_json:
        return jsonify({'error': 'Неверный формат данных'}), 400
        
    data = request.json
    results = {}
    
    try:
        for key, value in data.items():
            success = Settings.update_setting(key, value)
            results[key] = success
        
        return jsonify({"success": True, "results": results})
    except Exception as e:
        return jsonify({'error': str(e)}), 500