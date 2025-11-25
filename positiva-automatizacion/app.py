"""
POSITIVA - Sistema de Automatización
"""

from flask import Flask, render_template, redirect, url_for
import os
import socket

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

# Crear carpetas necesarias
os.makedirs('output/consolidador_t25', exist_ok=True)
os.makedirs('temp/consolidador_t25', exist_ok=True)
os.makedirs('data/maestra', exist_ok=True)

# Importar blueprints con debugging
print("\n" + "="*70)
print("CARGANDO MODULOS")
print("="*70)

try:
    from modules.especialidades.routes import especialidades_bp
    app.register_blueprint(especialidades_bp, url_prefix='/modulos/especialidades')
    print("  [OK] Modulo especialidades cargado")
except ImportError as e:
    print(f"  [ERROR] Modulo especialidades: {e}")
    import traceback
    traceback.print_exc()

try:
    from modules.consolidador.routes import consolidador_bp
    app.register_blueprint(consolidador_bp, url_prefix='/modulos/consolidador')
    print("  [OK] Modulo consolidador cargado")
except ImportError as e:
    print(f"  [ERROR] Modulo consolidador: {e}")
    import traceback
    traceback.print_exc()

try:
    from modules.consolidador_t25.routes import consolidador_t25_bp
    app.register_blueprint(consolidador_t25_bp, url_prefix='/modulos/consolidador-t25')
    print("  [OK] Modulo consolidador_t25 cargado")
except ImportError as e:
    print(f"  [ERROR] Modulo consolidador_t25: {e}")
    import traceback
    traceback.print_exc()

print("="*70 + "\n")

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


def find_free_port(start_port=4000, max_attempts=100):
    """Encuentra un puerto libre disponible"""
    for port in range(start_port, start_port + max_attempts):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('0.0.0.0', port))
            sock.close()
            return port
        except OSError:
            continue
    raise RuntimeError(f"No se encontro ningun puerto libre entre {start_port} y {start_port + max_attempts}")


if __name__ == '__main__':
    # Mostrar todos los blueprints registrados
    print("\n" + "="*70)
    print("BLUEPRINTS REGISTRADOS:")
    print("="*70)
    for blueprint_name, blueprint in app.blueprints.items():
        print(f"  - {blueprint_name}")
    print("="*70 + "\n")
    
    # Mostrar todas las rutas
    print("\n" + "="*70)
    print("RUTAS DISPONIBLES:")
    print("="*70)
    for rule in app.url_map.iter_rules():
        print(f"  {rule.endpoint:50s} {rule.rule}")
    print("="*70 + "\n")
    
    # Intentar usar el puerto 4000, si no esta disponible buscar otro
    try:
        port = find_free_port(4000)
        print(f"\n{'='*60}")
        print(f"Servidor Flask iniciando en puerto {port}")
        print(f"Accede a: http://0.0.0.0:{port}")
        print(f"{'='*60}\n")
        app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)
    except Exception as e:
        print(f"\nError iniciando servidor: {e}")
        print("Intenta cerrar otras aplicaciones que usen puertos\n")