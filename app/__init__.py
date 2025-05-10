from flask import Flask
from config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Создание необходимых папок
    import os
    services_path = os.path.join(app.root_path, 'services')
    if not os.path.exists(services_path):
        os.makedirs(services_path)
    
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