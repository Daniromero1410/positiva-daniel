"""
Rutas para el módulo Consolidador T25
"""

from flask import Blueprint, render_template, request, jsonify, session, send_file, redirect, url_for
from werkzeug.utils import secure_filename
import os
from datetime import datetime

from .goanywhere import GoAnywhereWebClient

# Intentar importar StatsManager, si no existe, usar versión simplificada
try:
    from utils.stats_manager import StatsManager
    stats_manager = StatsManager()
except (ImportError, ModuleNotFoundError):
    # Versión simplificada si no existe el módulo
    class SimpleStatsManager:
        def registrar_proceso(self, **kwargs):
            """Registro simplificado de estadísticas"""
            print(f"✓ Proceso registrado: {kwargs.get('tipo', 'desconocido')}")
    
    stats_manager = SimpleStatsManager()

# Crear blueprint
consolidador_t25_bp = Blueprint('consolidador_t25', __name__)

# Configuración
OUTPUT_FOLDER = 'output/consolidador_t25'
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Diccionario para mantener las conexiones SFTP por sesión
clientes_sftp = {}


@consolidador_t25_bp.route('/')
def index():
    """Ruta principal - redirige al dashboard"""
    return redirect(url_for('dashboard'))


@consolidador_t25_bp.route('/conectar', methods=['POST'])
def conectar():
    """Conecta al servidor GoAnywhere SFTP"""
    try:
        # Obtener o crear session_id
        if 'session_id' not in session:
            session['session_id'] = os.urandom(24).hex()
        
        session_id = session['session_id']
        
        # Si ya existe una conexión para esta sesión, desconectar
        if session_id in clientes_sftp:
            clientes_sftp[session_id].disconnect()
        
        # Crear nuevo cliente y conectar (usa credenciales por defecto)
        cliente = GoAnywhereWebClient()
        resultado = cliente.connect()
        
        if resultado['success']:
            # Guardar cliente en el diccionario de sesiones
            clientes_sftp[session_id] = cliente
            
            return jsonify({
                'success': True,
                'mensaje': 'Conexión exitosa',
                'directorio_actual': resultado['directorio_actual']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': resultado['error']
            }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@consolidador_t25_bp.route('/desconectar', methods=['POST'])
def desconectar():
    """Desconecta del servidor SFTP"""
    try:
        session_id = session.get('session_id')
        
        if session_id and session_id in clientes_sftp:
            clientes_sftp[session_id].disconnect()
            del clientes_sftp[session_id]
        
        return jsonify({
            'success': True,
            'mensaje': 'Desconectado exitosamente'
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@consolidador_t25_bp.route('/estado', methods=['GET'])
def estado():
    """Obtiene el estado de la conexión"""
    try:
        session_id = session.get('session_id')
        
        if session_id and session_id in clientes_sftp:
            cliente = clientes_sftp[session_id]
            status = cliente.get_connection_status()
            return jsonify(status), 200
        else:
            return jsonify({
                'conectado': False,
                'directorio_actual': None
            }), 200
    
    except Exception as e:
        return jsonify({
            'conectado': False,
            'error': str(e)
        }), 500


@consolidador_t25_bp.route('/listar', methods=['GET'])
def listar():
    """Lista el contenido del directorio actual"""
    try:
        session_id = session.get('session_id')
        
        if not session_id or session_id not in clientes_sftp:
            return jsonify({
                'success': False,
                'error': 'No hay sesión SFTP activa'
            }), 401
        
        cliente = clientes_sftp[session_id]
        resultado = cliente.list_directory()
        
        return jsonify(resultado), 200 if resultado['success'] else 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@consolidador_t25_bp.route('/navegar', methods=['POST'])
def navegar():
    """Navega a un directorio específico"""
    try:
        session_id = session.get('session_id')
        
        if not session_id or session_id not in clientes_sftp:
            return jsonify({
                'success': False,
                'error': 'No hay sesión SFTP activa'
            }), 401
        
        data = request.get_json()
        path = data.get('path', '.')
        
        cliente = clientes_sftp[session_id]
        resultado = cliente.change_directory(path)
        
        return jsonify(resultado), 200 if resultado['success'] else 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@consolidador_t25_bp.route('/buscar', methods=['POST'])
def buscar():
    """Busca archivos recursivamente en el servidor"""
    try:
        session_id = session.get('session_id')
        
        if not session_id or session_id not in clientes_sftp:
            return jsonify({
                'success': False,
                'error': 'No hay sesión SFTP activa'
            }), 401
        
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query or len(query) < 2:
            return jsonify({
                'success': False,
                'error': 'La búsqueda debe tener al menos 2 caracteres'
            }), 400
        
        cliente = clientes_sftp[session_id]
        
        # Obtener ruta de búsqueda (por defecto el directorio actual)
        search_path = cliente.get_current_directory() or '/'
        max_results = data.get('max_results', 100)
        
        resultado = cliente.search_files(query, search_path, max_results)
        
        return jsonify(resultado), 200 if resultado['success'] else 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@consolidador_t25_bp.route('/sugerencias', methods=['POST'])
def sugerencias():
    """Obtiene sugerencias de autocompletado"""
    try:
        session_id = session.get('session_id')
        
        if not session_id or session_id not in clientes_sftp:
            return jsonify({
                'success': False,
                'error': 'No hay sesión SFTP activa'
            }), 401
        
        data = request.get_json()
        partial_query = data.get('query', '').strip()
        
        if not partial_query or len(partial_query) < 1:
            return jsonify({
                'success': True,
                'sugerencias': []
            }), 200
        
        cliente = clientes_sftp[session_id]
        current_path = cliente.get_current_directory() or '/'
        
        resultado = cliente.get_suggestions(partial_query, current_path, limit=10)
        
        return jsonify(resultado), 200 if resultado['success'] else 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@consolidador_t25_bp.route('/descargar', methods=['POST'])
def descargar():
    """Descarga un archivo desde el servidor SFTP"""
    try:
        session_id = session.get('session_id')
        
        if not session_id or session_id not in clientes_sftp:
            return jsonify({
                'success': False,
                'error': 'No hay sesión SFTP activa'
            }), 401
        
        data = request.get_json()
        archivo = data.get('archivo')
        
        if not archivo:
            return jsonify({
                'success': False,
                'error': 'No se especificó el archivo'
            }), 400
        
        cliente = clientes_sftp[session_id]
        
        # Generar nombre de archivo local con timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nombre_base = secure_filename(os.path.basename(archivo))
        nombre_local = f"{timestamp}_{nombre_base}"
        ruta_local = os.path.join(OUTPUT_FOLDER, nombre_local)
        
        # Descargar archivo
        resultado = cliente.download_file(archivo, ruta_local)
        
        if resultado['success']:
            # Registrar en estadísticas
            try:
                stats_manager.registrar_proceso(
                    tipo='consolidador_t25_descarga',
                    usuario='sistema',
                    archivo=nombre_base,
                    registros=1,
                    exitoso=True
                )
            except Exception as e:
                print(f"⚠ No se pudo registrar estadística: {e}")
            
            return jsonify({
                'success': True,
                'mensaje': 'Archivo descargado exitosamente',
                'archivo': nombre_local
            }), 200
        else:
            return jsonify(resultado), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@consolidador_t25_bp.route('/download/<filename>')
def download_file(filename):
    """Envía el archivo descargado al navegador"""
    try:
        ruta_archivo = os.path.join(OUTPUT_FOLDER, filename)
        
        if not os.path.exists(ruta_archivo):
            return "Archivo no encontrado", 404
        
        # Obtener el nombre original (sin timestamp)
        nombre_original = '_'.join(filename.split('_')[2:])
        
        return send_file(
            ruta_archivo,
            as_attachment=True,
            download_name=nombre_original
        )
    
    except Exception as e:
        return f"Error al descargar archivo: {str(e)}", 500