from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models.user import User
from functools import wraps

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Пожалуйста, авторизуйтесь для доступа к этой странице', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Пожалуйста, авторизуйтесь для доступа к этой странице', 'error')
            return redirect(url_for('auth.login'))
        
        user_dict = session['user']
        if not user_dict.get('is_admin', False):
            flash('У вас нет доступа к этой странице', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')
        
        if not login or not password:
            flash('Пожалуйста, заполните все поля', 'error')
            return render_template('auth/login.html')
        
        user = User.authenticate(login, password)
        
        if user:
            # Преобразуем user.to_dict() в JSON-сериализуемые типы данных
            user_dict = {
                'id': user.id,
                'login': user.login,
                'full_name': user.full_name,
                'is_admin': user.is_admin
            }
            session['user'] = user_dict
            session.permanent = True  # Делаем сессию постоянной
            flash(f'Добро пожаловать, {user.full_name}!', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Неверный логин или пароль', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    session.pop('user', None)
    session.clear()  # Полная очистка сессии
    flash('Вы успешно вышли из системы', 'success')
    return redirect(url_for('auth.login'))