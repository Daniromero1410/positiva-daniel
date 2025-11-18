"""
"""
import os
from flask import Blueprint, render_template, request, jsonify, send_file, current_app, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime
from .logic import procesar_anexo1_xlsb, generar_excel_consolidado
from utils.stats import stats_manager

# Crear Blueprint
consolidador_bp = Blueprint('consolidador', __name__)


def allowed_file(filename):
    """Verifica si el archivo tiene una extensión permitida"""
    # Para consolidador solo aceptamos XLSB
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() == 'xlsb'


@consolidador_bp.route('/')
def index():
    """Página principal del módulo"""
    return render_template('modules/consolidador/index.html')


@consolidador_bp.route('/upload', methods=['POST'])
def upload_file():
    """
    Endpoint para subir y procesar archivo XLSB
    
    Returns:
        JSON con resultado del procesamiento
    """
    try:
        # Verificar archivo
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No se envió ningún archivo'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No se seleccionó ningún archivo'
            }), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': 'Formato no permitido. Solo se permiten archivos .xlsb'
            }), 400
        
        # Obtener fecha del acuerdo (opcional)
        fecha_acuerdo = request.form.get('fecha_acuerdo', None)
        if fecha_acuerdo and fecha_acuerdo.strip() == '':
            fecha_acuerdo = None
        
        # Guardar archivo
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename_con_timestamp = f"{timestamp}_{filename}"
        
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename_con_timestamp)
        file.save(filepath)
        
        # Procesar archivo
        resultado = procesar_anexo1_xlsb(filepath, fecha_acuerdo)
        
        if not resultado['success']:
            if os.path.exists(filepath):
                os.remove(filepath)
            
            return jsonify({
                'success': False,
                'error': resultado.get('error', 'Error al procesar el archivo')
            }), 500
        
        # Generar archivo de salida
        output_filename = f"CONSOLIDADO_ANEXO1_{timestamp}.xlsx"
        output_path = os.path.join(current_app.config['OUTPUT_FOLDER'], output_filename)
        
        if generar_excel_consolidado(resultado, output_path):
            # Eliminar archivo de entrada
            if os.path.exists(filepath):
                os.remove(filepath)
            
            # Registrar en estadísticas
            stats_manager.registrar_proceso(
                modulo='Consolidador Anexo 1',
                archivo_nombre=filename,
                total_registros=resultado['total_servicios'],
                exito=True,
                archivo_salida=output_filename
            )
            
            return jsonify({
                'success': True,
                'mensaje': 'Consolidación completada exitosamente',
                'archivo_salida': output_filename,
                'estadisticas': {
                    'total_sedes': resultado['total_sedes'],
                    'total_servicios': resultado['total_servicios'],
                    'tiempo_ejecucion': resultado['tiempo_ejecucion'],
                    'fecha_acuerdo': fecha_acuerdo or 'Sin fecha'
                }
            }), 200
        
        else:
            return jsonify({
                'success': False,
                'error': 'Error al generar archivo de resultados'
            }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error inesperado: {str(e)}'
        }), 500


@consolidador_bp.route('/validar', methods=['POST'])
def validar_archivo():
    """Valida la estructura del archivo XLSB"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No se envió ningún archivo'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No se seleccionó ningún archivo'
            }), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': 'Formato no permitido. Solo archivos .xlsb'
            }), 400
        
        # Guardar temporalmente
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        temp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f"temp_{timestamp}_{filename}")
        file.save(temp_path)
        
        # Validar
        from pyxlsb import open_workbook
        
        try:
            validacion = {
                'success': True,
                'validaciones': []
            }
            
            with open_workbook(temp_path) as wb:
                hojas_disponibles = wb.sheets
                
                # Buscar hoja de tarifas
                hoja_encontrada = False
                for sheet_name in hojas_disponibles:
                    if 'TARIFA' in sheet_name.upper() and 'SERV' in sheet_name.upper():
                        hoja_encontrada = True
                        
                        # Contar filas
                        total_filas = 0
                        with wb.get_sheet(sheet_name) as sheet:
                            for row in sheet.rows():
                                total_filas += 1
                        
                        validacion['validaciones'].append({
                            'hoja': sheet_name,
                            'valida': True,
                            'registros': total_filas
                        })
                        break
                
                if not hoja_encontrada:
                    validacion['validaciones'].append({
                        'hoja': 'TARIFAS DE SERV',
                        'valida': False,
                        'error': 'No se encontró la hoja requerida'
                    })
                    validacion['success'] = False
            
            # Eliminar temporal
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            return jsonify(validacion), 200
        
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            return jsonify({
                'success': False,
                'error': f'Error al leer archivo: {str(e)}'
            }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error inesperado: {str(e)}'
        }), 500


@consolidador_bp.route('/resultados')
def resultados():
    """Vista de resultados"""
    archivo = request.args.get('archivo', '')
    sedes = request.args.get('sedes', 0, type=int)
    servicios = request.args.get('servicios', 0, type=int)
    tiempo = request.args.get('tiempo', 0, type=float)
    fecha = request.args.get('fecha', 'Sin fecha')
    
    if not archivo:
        return redirect(url_for('consolidador.index'))
    
    file_path = os.path.join(current_app.config['OUTPUT_FOLDER'], archivo)
    if not os.path.exists(file_path):
        return redirect(url_for('consolidador.index'))
    
    estadisticas = {
        'total_sedes': sedes,
        'total_servicios': servicios,
        'tiempo_ejecucion': tiempo,
        'fecha_acuerdo': fecha,
        'archivo_salida': archivo
    }
    
    return render_template('modules/consolidador/resultados.html', stats=estadisticas)


@consolidador_bp.route('/download/<filename>')
def download_file(filename):
    """Descarga archivo procesado"""
    try:
        file_path = os.path.join(current_app.config['OUTPUT_FOLDER'], filename)
        
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': 'Archivo no encontrado'
            }), 404
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error al descargar: {str(e)}'
        }), 500
