import os
from flask import Flask, render_template, redirect, url_for
from config import config
from utils.stats import stats_manager

def create_app(config_name='default'):
    """Factory function para crear la aplicación Flask"""
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Asegurar que existan las carpetas necesarias
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
    os.makedirs('data', exist_ok=True)
    
    # Registrar blueprints (módulos)
    from modules.especialidades.routes import especialidades_bp
    app.register_blueprint(especialidades_bp, url_prefix='/modulos/especialidades')
    
    from modules.consolidador.routes import consolidador_bp
    app.register_blueprint(consolidador_bp, url_prefix='/modulos/consolidador')
    
    # IMPORTANTE: Registrar módulo Consolidador T25
    from modules.consolidador_t25.routes import consolidador_t25_bp
    app.register_blueprint(consolidador_t25_bp, url_prefix='/modulos/consolidador-t25')
    
    # Ruta principal
    @app.route('/')
    def index():
        return redirect(url_for('dashboard'))
    
    # Dashboard con estadísticas REALES
    @app.route('/dashboard')
    def dashboard():
        # Obtener estadísticas reales del sistema
        stats = stats_manager.get_dashboard_stats()
        
        # Obtener actividad reciente
        actividad_reciente = stats_manager.get_actividad_reciente(limit=5)
        
        return render_template('dashboard.html', 
                             stats=stats, 
                             actividad_reciente=actividad_reciente)
    
    # Manejador de errores 404
    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404
    
    # Manejador de errores 500
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500
    
    return app


if __name__ == '__main__':
    app = create_app('development')
    app.run(host='0.0.0.0', port=5000, debug=True)