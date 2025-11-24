"""
POSITIVA - Sistema de Automatización
"""

from flask import Flask, render_template, redirect, url_for
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

# Crear carpetas necesarias
os.makedirs('output/consolidador_t25', exist_ok=True)
os.makedirs('temp/consolidador_t25', exist_ok=True)
os.makedirs('data/maestra', exist_ok=True)

# Importar blueprints
try:
    from modules.especialidades.routes import especialidades_bp
    app.register_blueprint(especialidades_bp, url_prefix='/modulos/especialidades')
except ImportError:
    pass

try:
    from modules.consolidador.routes import consolidador_bp
    app.register_blueprint(consolidador_bp, url_prefix='/modulos/consolidador')
except ImportError:
    pass

try:
    from modules.consolidador_t25.routes import consolidador_t25_bp
    app.register_blueprint(consolidador_t25_bp, url_prefix='/modulos/consolidador-t25')
except ImportError:
    pass

@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    stats = {
        'total_archivos': 0,
        'procesos_activos': 0,
        'registros_totales': 0,
        'tasa_exito': 0
    }
    return render_template('dashboard.html', stats=stats)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000, debug=True)