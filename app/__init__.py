from flask import Flask
from flask_session import Session
from config import Config
import os

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Инициализация Flask-Session
    Session(app)
    
    # Создание необходимых папок
    services_path = os.path.join(app.root_path, 'services')
    if not os.path.exists(services_path):
        os.makedirs(services_path)
    
    # Создание папки для сессий, если используется файловая система
    if app.config.get('SESSION_TYPE') == 'filesystem':
        session_dir = app.config.get('SESSION_FILE_DIR', './flask_session/')
        if not os.path.exists(session_dir):
            os.makedirs(session_dir)
    
    # Регистрация маршрутов
    from app.controllers.auth_controller import auth_bp
    from app.controllers.main_controller import main_bp
    from app.controllers.settings_controller import settings_bp
    from app.controllers.calculation_controller import calculation_bp
    from app.controllers.formula_controller import formulas_bp
    from app.controllers.workload_controller import workload_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(calculation_bp)
    app.register_blueprint(formulas_bp)
    app.register_blueprint(workload_bp)
    
    return app