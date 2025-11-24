"""
Rutas para el módulo Consolidador T25
"""

from flask import Blueprint, render_template, request, jsonify, session, send_file, redirect, url_for
from werkzeug.utils import secure_filename
import os
from datetime import datetime

from .goanywhere import GoAnywhereWebClient
from .maestra_manager import MaestraManager
from .consolidator import ConsolidadorT25
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill

# Intentar importar StatsManager, si no existe, usar versión simplificada
try:
    from utils.stats_manager import StatsManager
    stats_manager = StatsManager()
except (ImportError, ModuleNotFoundError):
    class SimpleStatsManager:
        def registrar_proceso(self, **kwargs):
            print(f"✓ Proceso registrado: {kwargs.get('tipo', 'desconocido')}")
    stats_manager = SimpleStatsManager()

# Crear blueprint
consolidador_t25_bp = Blueprint('consolidador_t25', __name__)

# Configuración
OUTPUT_FOLDER = 'output/consolidador_t25'
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Diccionario para mantener las conexiones SFTP por sesión
clientes_sftp = {}

# Instancia de maestra manager
maestra_manager = MaestraManager()


@consolidador_t25_bp.route('/')
def index():
    """Ruta principal del módulo"""
    return render_template('modules/consolidador_t25/index.html')


# ============================================
# RUTAS DE GESTIÓN DE MAESTRA
# ============================================

@consolidador_t25_bp.route('/maestra')
def maestra():
    """Página de gestión de maestra"""
    info_maestra = maestra_manager.obtener_info_maestra()
    return render_template('modules/consolidador_t25/maestra.html', maestra=info_maestra)


@consolidador_t25_bp.route('/maestra/subir', methods=['POST'])
def subir_maestra():
    """Sube una nueva maestra"""
    try:
        if 'archivo' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No se proporcionó archivo'
            }), 400
        
        archivo = request.files['archivo']
        
        if archivo.filename == '':
            return jsonify({
                'success': False,
                'error': 'No se seleccionó archivo'
            }), 400
        
        # Subir maestra
        resultado = maestra_manager.subir_maestra(archivo, archivo.filename)
        
        return jsonify(resultado), 200 if resultado['success'] else 400
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@consolidador_t25_bp.route('/maestra/info', methods=['GET'])
def info_maestra():
    """Obtiene información de la maestra actual"""
    info = maestra_manager.obtener_info_maestra()
    
    if info:
        return jsonify({
            'success': True,
            'maestra': info
        }), 200
    else:
        return jsonify({
            'success': False,
            'error': 'No hay maestra cargada'
        }), 404


@consolidador_t25_bp.route('/maestra/descargar', methods=['GET'])
def descargar_maestra():
    """Descarga la maestra actual"""
    if not maestra_manager.tiene_maestra():
        return "No hay maestra cargada", 404
    
    info = maestra_manager.obtener_info_maestra()
    
    return send_file(
        info['ruta'],
        as_attachment=True,
        download_name=info['filename']
    )


# ============================================
# RUTAS DE BÚSQUEDA DE CONTRATOS
# ============================================

@consolidador_t25_bp.route('/buscar-contrato')
def buscar_contrato_page():
    """Página de búsqueda de contratos"""
    return render_template('modules/consolidador_t25/buscar_contrato.html')


@consolidador_t25_bp.route('/buscar-contrato/buscar', methods=['POST'])
def buscar_contrato():
    """Busca contratos en la maestra"""
    try:
        if not maestra_manager.tiene_maestra():
            return jsonify({
                'success': False,
                'error': 'No hay maestra cargada'
            }), 400
        
        data = request.get_json()
        termino = data.get('termino', '').strip()
        
        if not termino:
            return jsonify({
                'success': False,
                'error': 'Debe ingresar un término de búsqueda'
            }), 400
        
        # Buscar contratos
        contratos = maestra_manager.buscar_contrato(termino)
        
        return jsonify({
            'success': True,
            'contratos': contratos,
            'total': len(contratos)
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@consolidador_t25_bp.route('/buscar-contrato/procesar', methods=['POST'])
def procesar_contrato_individual():
    """Procesa un contrato individual"""
    try:
        session_id = session.get('session_id')
        
        if not session_id or session_id not in clientes_sftp:
            return jsonify({
                'success': False,
                'error': 'No hay sesión SFTP activa'
            }), 401
        
        data = request.get_json()
        numero_contrato = data.get('numero_contrato')
        
        if not numero_contrato:
            return jsonify({
                'success': False,
                'error': 'Debe proporcionar número de contrato'
            }), 400
        
        # Buscar información del contrato en la maestra
        contratos = maestra_manager.buscar_contrato(numero_contrato)
        
        if not contratos:
            return jsonify({
                'success': False,
                'error': f'Contrato {numero_contrato} no encontrado en la maestra'
            }), 404
        
        info_contrato = contratos[0]
        
        # Crear consolidador
        cliente = clientes_sftp[session_id]
        consolidador = ConsolidadorT25(cliente)
        
        # Procesar contrato
        resultado = consolidador.procesar_contrato(info_contrato)
        
        if resultado['success']:
            # Generar Excel consolidado
            archivo_consolidado = generar_excel_consolidado(
                resultado['servicios_consolidados'],
                numero_contrato
            )
            
            # Registrar estadísticas
            try:
                stats_manager.registrar_proceso(
                    tipo='consolidador_t25_individual',
                    usuario='sistema',
                    archivo=numero_contrato,
                    registros=len(resultado['servicios_consolidados']),
                    exitoso=True
                )
            except:
                pass
            
            return jsonify({
                'success': True,
                'archivo': archivo_consolidado,
                'total_servicios': len(resultado['servicios_consolidados']),
                'total_anexos': len(resultado['anexos_descargados']),
                'alertas': resultado['alertas']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': resultado.get('error', 'Error desconocido'),
                'alertas': resultado.get('alertas', [])
            }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================
# RUTAS DE CONSOLIDADO MASIVO
# ============================================

@consolidador_t25_bp.route('/consolidar-masivo')
def consolidar_masivo_page():
    """Página de consolidado masivo"""
    return render_template('modules/consolidador_t25/consolidar_masivo.html')


@consolidador_t25_bp.route('/consolidar-masivo/anios', methods=['GET'])
def obtener_anios_disponibles():
    """Obtiene los años disponibles en la maestra"""
    try:
        if not maestra_manager.tiene_maestra():
            return jsonify({
                'success': False,
                'error': 'No hay maestra cargada'
            }), 400
        
        # Leer todos los contratos
        contratos = maestra_manager.leer_contratos_prestadores_salud()
        
        # Extraer años únicos
        anios = set()
        for contrato in contratos:
            numero = str(contrato['numero_contrato'])
            # Buscar patrón de año (4 dígitos)
            import re
            match = re.search(r'20\d{2}', numero)
            if match:
                anios.add(int(match.group()))
        
        return jsonify({
            'success': True,
            'anios': sorted(list(anios), reverse=True)
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@consolidador_t25_bp.route('/consolidar-masivo/preview', methods=['POST'])
def preview_consolidado_masivo():
    """Preview de contratos a consolidar por año"""
    try:
        if not maestra_manager.tiene_maestra():
            return jsonify({
                'success': False,
                'error': 'No hay maestra cargada'
            }), 400
        
        data = request.get_json()
        anio = data.get('anio')
        
        if not anio:
            return jsonify({
                'success': False,
                'error': 'Debe proporcionar año'
            }), 400
        
        # Obtener contratos del año
        contratos = maestra_manager.obtener_contratos_por_anio(int(anio))
        
        return jsonify({
            'success': True,
            'contratos': contratos,
            'total': len(contratos)
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@consolidador_t25_bp.route('/consolidar-masivo/procesar', methods=['POST'])
def procesar_consolidado_masivo():
    """Procesa consolidado masivo por año"""
    try:
        session_id = session.get('session_id')
        
        if not session_id or session_id not in clientes_sftp:
            return jsonify({
                'success': False,
                'error': 'No hay sesión SFTP activa'
            }), 401
        
        data = request.get_json()
        anio = data.get('anio')
        
        if not anio:
            return jsonify({
                'success': False,
                'error': 'Debe proporcionar año'
            }), 400
        
        # Obtener contratos del año
        contratos = maestra_manager.obtener_contratos_por_anio(int(anio))
        
        if not contratos:
            return jsonify({
                'success': False,
                'error': f'No hay contratos para el año {anio}'
            }), 404
        
        # Crear consolidador
        cliente = clientes_sftp[session_id]
        consolidador = ConsolidadorT25(cliente)
        
        # Procesar cada contrato
        todos_servicios = []
        contratos_procesados = 0
        contratos_con_error = 0
        todas_alertas = []
        
        for idx, info_contrato in enumerate(contratos):
            print(f"\n📄 Procesando {idx+1}/{len(contratos)}: {info_contrato['numero_contrato']}")
            
            resultado = consolidador.procesar_contrato(info_contrato)
            
            if resultado['success']:
                todos_servicios.extend(resultado['servicios_consolidados'])
                contratos_procesados += 1
            else:
                contratos_con_error += 1
            
            todas_alertas.extend(resultado.get('alertas', []))
        
        # Generar Excel consolidado
        if todos_servicios:
            archivo_consolidado = generar_excel_consolidado(
                todos_servicios,
                f"CONSOLIDADO_{anio}"
            )
            
            # Generar archivo de alertas
            archivo_alertas = generar_archivo_alertas(todas_alertas, anio)
            
            # Registrar estadísticas
            try:
                stats_manager.registrar_proceso(
                    tipo='consolidador_t25_masivo',
                    usuario='sistema',
                    archivo=f'año_{anio}',
                    registros=len(todos_servicios),
                    exitoso=True
                )
            except:
                pass
            
            return jsonify({
                'success': True,
                'archivo_consolidado': archivo_consolidado,
                'archivo_alertas': archivo_alertas,
                'total_servicios': len(todos_servicios),
                'contratos_procesados': contratos_procesados,
                'contratos_con_error': contratos_con_error,
                'total_contratos': len(contratos),
                'total_alertas': len(todas_alertas)
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'No se pudieron procesar servicios',
                'alertas': todas_alertas
            }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================
# RUTAS DE CONEXIÓN SFTP (EXISTENTES)
# ============================================

@consolidador_t25_bp.route('/conectar', methods=['POST'])
def conectar():
    """Conecta al servidor GoAnywhere SFTP"""
    try:
        if 'session_id' not in session:
            session['session_id'] = os.urandom(24).hex()
        
        session_id = session['session_id']
        
        if session_id in clientes_sftp:
            clientes_sftp[session_id].disconnect()
        
        cliente = GoAnywhereWebClient()
        resultado = cliente.connect()
        
        if resultado['success']:
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
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nombre_base = secure_filename(os.path.basename(archivo))
        nombre_local = f"{timestamp}_{nombre_base}"
        ruta_local = os.path.join(OUTPUT_FOLDER, nombre_local)
        
        resultado = cliente.download_file(archivo, ruta_local)
        
        if resultado['success']:
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
        
        nombre_original = '_'.join(filename.split('_')[2:])
        
        return send_file(
            ruta_archivo,
            as_attachment=True,
            download_name=nombre_original
        )
    
    except Exception as e:
        return f"Error al descargar archivo: {str(e)}", 500


# ============================================
# FUNCIONES AUXILIARES
# ============================================

def generar_excel_consolidado(servicios: list, nombre_base: str) -> str:
    """
    Genera archivo Excel consolidado con formato POSITIVA
    
    Args:
        servicios: Lista de servicios consolidados
        nombre_base: Nombre base del archivo
        
    Returns:
        Nombre del archivo generado
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Consolidado"
    
    # Estilo del encabezado principal
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True, size=11)
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    # Escribir encabezado principal
    ws.merge_cells('A1:H1')
    ws['A1'] = 'ANEXO 1 PACTADO DEL PRESTADOR'
    ws['A1'].fill = header_fill
    ws['A1'].font = header_font
    ws['A1'].alignment = header_alignment
    
    ws.merge_cells('I1:K1')
    ws['I1'] = 'INFO ACTA O ACUERDO'
    ws['I1'].fill = header_fill
    ws['I1'].font = header_font
    ws['I1'].alignment = header_alignment
    
    # Escribir encabezados de columnas (fila 2)
    columnas = [
        'codigo_cups', 'codigo_homologo_manual', 'descripcion_del_cups',
        'tarifa_unitaria_en_pesos', 'manual_tarifario', 'porcentaje_manual_tarifario',
        'observaciones', 'codigo_de_habilitacion', 'fecha_acuerdo',
        'numero_contrato_año', 'origen_tarifa'
    ]
    
    for col_idx, col_name in enumerate(columnas, 1):
        cell = ws.cell(row=2, column=col_idx)
        cell.value = col_name
        cell.fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center", vertical="center")
    
    # Escribir datos
    for row_idx, servicio in enumerate(servicios, 3):
        for col_idx, col_name in enumerate(columnas, 1):
            ws.cell(row=row_idx, column=col_idx, value=servicio.get(col_name, ''))
    
    # Ajustar anchos de columna
    ws.column_dimensions['A'].width = 15
    ws.column_dimensions['B'].width = 20
    ws.column_dimensions['C'].width = 50
    ws.column_dimensions['D'].width = 25
    ws.column_dimensions['E'].width = 20
    ws.column_dimensions['F'].width = 30
    ws.column_dimensions['G'].width = 20
    ws.column_dimensions['H'].width = 25
    ws.column_dimensions['I'].width = 15
    ws.column_dimensions['J'].width = 20
    ws.column_dimensions['K'].width = 15
    
    # Guardar archivo
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'{nombre_base}_{timestamp}.xlsx'
    filepath = os.path.join(OUTPUT_FOLDER, filename)
    wb.save(filepath)
    
    return filename


def generar_archivo_alertas(alertas: list, anio: int) -> str:
    """
    Genera archivo de texto con todas las alertas
    
    Args:
        alertas: Lista de alertas generadas
        anio: Año del consolidado
        
    Returns:
        Nombre del archivo generado
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'ALERTAS_{anio}_{timestamp}.txt'
    filepath = os.path.join(OUTPUT_FOLDER, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"ALERTAS DEL CONSOLIDADO - AÑO {anio}\n")
        f.write(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")
        
        if not alertas:
            f.write("✅ No se generaron alertas\n")
        else:
            f.write(f"Total de alertas: {len(alertas)}\n\n")
            
            # Agrupar por tipo
            por_tipo = {}
            for alerta in alertas:
                tipo = alerta['tipo']
                if tipo not in por_tipo:
                    por_tipo[tipo] = []
                por_tipo[tipo].append(alerta)
            
            # Escribir por tipo
            for tipo, alertas_tipo in por_tipo.items():
                f.write(f"\n{'='*80}\n")
                f.write(f"{tipo.upper()}: {len(alertas_tipo)}\n")
                f.write(f"{'='*80}\n\n")
                
                for alerta in alertas_tipo:
                    f.write(f"[{alerta['timestamp']}] ")
                    if alerta.get('contrato'):
                        f.write(f"Contrato {alerta['contrato']}: ")
                    f.write(f"{alerta['mensaje']}\n")
    
    return filename