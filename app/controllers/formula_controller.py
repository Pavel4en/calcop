from flask import Blueprint, render_template, request, jsonify, session
from app.controllers.auth_controller import admin_required
from app.models.formulas import Formula
from app.services.formula_executor import FormulaExecutor
import json

formulas_bp = Blueprint('formulas', __name__, url_prefix='/formulas')

@formulas_bp.route('/')
@admin_required
def index():
    """Страница управления формулами"""
    user_dict = session.get('user', {})
    return render_template('dashboard/formulas/index.html', user=user_dict)

# API для управления формулами
@formulas_bp.route('/api/formulas', methods=['GET'])
@admin_required
def get_all_formulas_api():
    """API для получения всех формул"""
    formulas_data = Formula.get_all_formulas()
    return jsonify(formulas_data)

@formulas_bp.route('/api/formulas/<int:formula_id>', methods=['GET'])
@admin_required
def get_formula_api(formula_id):
    """API для получения конкретной формулы по ID"""
    formula = Formula.get_formula_by_id(formula_id)
    if not formula:
        return jsonify({'error': 'Формула не найдена'}), 404
    return jsonify(formula)

@formulas_bp.route('/api/formulas', methods=['POST'])
@admin_required
def create_formula_api():
    """API для создания новой формулы"""
    if not request.is_json:
        return jsonify({'error': 'Неверный формат данных'}), 400
        
    data = request.json
    name = data.get('name')
    condition_code = data.get('condition_code')
    condition = data.get('condition')
    formula = data.get('formula')
    order_point = data.get('order_point')
    comment = data.get('comment')
    selection_condition = data.get('selection_condition')
    
    if not name or not condition_code or not condition or not formula:
        return jsonify({'error': 'Не указаны обязательные параметры'}), 400
    
    try:
        formula_id = Formula.create_formula(
            name, condition_code, condition, formula, order_point, comment, selection_condition
        )
        return jsonify({'id': formula_id, 'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@formulas_bp.route('/api/formulas/<int:formula_id>', methods=['PUT'])
@admin_required
def update_formula_api(formula_id):
    """API для обновления существующей формулы"""
    if not request.is_json:
        return jsonify({'error': 'Неверный формат данных'}), 400
        
    data = request.json
    name = data.get('name')
    condition_code = data.get('condition_code')
    condition = data.get('condition')
    formula = data.get('formula')
    order_point = data.get('order_point')
    comment = data.get('comment')
    selection_condition = data.get('selection_condition')
    
    try:
        success = Formula.update_formula(
            formula_id, name, condition_code, condition, formula, order_point, comment, selection_condition
        )
        if not success:
            return jsonify({'error': 'Формула не найдена'}), 404
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@formulas_bp.route('/api/formulas/<int:formula_id>', methods=['DELETE'])
@admin_required
def delete_formula_api(formula_id):
    """API для удаления формулы"""
    try:
        success = Formula.delete_formula(formula_id)
        if not success:
            return jsonify({'error': 'Формула не найдена'}), 404
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@formulas_bp.route('/api/test-formula', methods=['POST'])
@admin_required
def test_formula_api():
    """API для тестирования формулы на конкретных данных"""
    if not request.is_json:
        return jsonify({'error': 'Неверный формат данных'}), 400
        
    data = request.json
    formula = data.get('formula')
    test_data = data.get('test_data')
    norms_data = data.get('norms_data', {})
    
    if not formula or not test_data:
        return jsonify({'error': 'Не указаны обязательные параметры'}), 400
    
    try:
        # Преобразование строки JSON в словарь
        if isinstance(test_data, str):
            test_data = json.loads(test_data)
        if isinstance(norms_data, str):
            norms_data = json.loads(norms_data)
            
        # Выполнение формулы
        result = FormulaExecutor._execute_formula(formula, test_data, norms_data)
        return jsonify({'result': result, 'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@formulas_bp.route('/api/test-condition', methods=['POST'])
@admin_required
def test_condition_api():
    """API для тестирования условия выбора формулы на конкретных данных"""
    if not request.is_json:
        return jsonify({'error': 'Неверный формат данных'}), 400
        
    data = request.json
    condition = data.get('condition')
    test_data = data.get('test_data')
    
    if not condition or not test_data:
        return jsonify({'error': 'Не указаны обязательные параметры'}), 400
    
    try:
        # Преобразование строки JSON в словарь
        if isinstance(test_data, str):
            test_data = json.loads(test_data)
            
        # Выполнение условия
        result = FormulaExecutor._evaluate_selection_condition(test_data, condition)
        return jsonify({'result': result, 'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500