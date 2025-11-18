"""
Rutas del módulo de Asignación de Especialidades
"""
import os
from flask import Blueprint, render_template, request, jsonify, send_file, current_app, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime
from .logic import procesar_excel, generar_excel_resultado
from utils.stats import stats_manager

# Crear Blueprint
especialidades_bp = Blueprint('especialidades', __name__)


def allowed_file(filename):
    """Verifica si el archivo tiene una extensión permitida"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


@especialidades_bp.route('/')
def index():
    """Página principal del módulo"""
    return render_template('modules/especialidades/index.html')


@especialidades_bp.route('/upload', methods=['POST'])
def upload_file():
    """
    Endpoint para subir y procesar archivo Excel
    
    Returns:
        JSON con resultado del procesamiento
    """
    try:
        # Verificar que se envió un archivo
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No se envió ningún archivo'
            }), 400
        
        file = request.files['file']
        
        # Verificar que el archivo tenga nombre
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No se seleccionó ningún archivo'
            }), 400
        
        # Verificar extensión
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': 'Formato de archivo no permitido. Solo se permiten .xlsx y .xls'
            }), 400
        
        # Generar nombre seguro para el archivo
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename_con_timestamp = f"{timestamp}_{filename}"
        
        # Guardar archivo
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename_con_timestamp)
        file.save(filepath)
        
        # Procesar archivo
        resultados = procesar_excel(filepath)
        
        if not resultados['success']:
            # Eliminar archivo si hubo error
            if os.path.exists(filepath):
                os.remove(filepath)
            
            return jsonify({
                'success': False,
                'error': resultados.get('error', 'Error desconocido al procesar el archivo'),
                'errores': resultados.get('errores', [])
            }), 500
        
        # Generar archivo de salida
        output_filename = f"resultado_{timestamp}_{filename}"
        output_path = os.path.join(current_app.config['OUTPUT_FOLDER'], output_filename)
        
        if generar_excel_resultado(resultados, output_path):
            # Eliminar archivo de entrada (ya no se necesita)
            if os.path.exists(filepath):
                os.remove(filepath)
            
            # Registrar en estadísticas
            stats_manager.registrar_proceso(
                modulo='Asignación de Especialidades',
                archivo_nombre=filename,
                total_registros=resultados['total_estudios'],
                estudios_especificos=resultados['estudios_especificos'],
                estudios_generales=resultados['estudios_generales'],
                exito=True,
                tiempo_ejecucion=resultados.get('tiempo_ejecucion', 0),
                archivo_salida=output_filename
            )
            
            # Preparar vista previa de datos (primeros 10 registros)
            vista_previa = []
            
            if resultados['datos_imagenes'] is not None:
                df_preview = resultados['datos_imagenes'].head(10)
                for _, row in df_preview.iterrows():
                    vista_previa.append({
                        'codigo': str(row['Servicio_Principal']),
                        'nombre': str(row['Nombre_Servicio_Principal_ajust']),
                        'especialidades': str(row['Nombre Especialidad principal']),
                        'tipo': 'Imagen'
                    })
            
            if resultados['datos_laboratorio'] is not None:
                df_preview = resultados['datos_laboratorio'].head(10)
                for _, row in df_preview.iterrows():
                    vista_previa.append({
                        'codigo': str(row['Servicio_Principal']),
                        'nombre': str(row['Nombre_Servicio_Principal_ajust']),
                        'especialidades': str(row['especialidad principal']),
                        'tipo': 'Laboratorio'
                    })
            
            # Retornar resultado exitoso
            return jsonify({
                'success': True,
                'mensaje': 'Archivo procesado exitosamente',
                'archivo_salida': output_filename,
                'estadisticas': {
                    'total_estudios': resultados['total_estudios'],
                    'estudios_especificos': resultados['estudios_especificos'],
                    'estudios_generales': resultados['estudios_generales'],
                    'hojas_procesadas': resultados['hojas_procesadas'],
                    'tiempo_ejecucion': resultados.get('tiempo_ejecucion', 0)
                },
                'vista_previa': vista_previa[:10]  # Máximo 10 registros
            }), 200
        
        else:
            return jsonify({
                'success': False,
                'error': 'Error al generar el archivo de resultados'
            }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error inesperado: {str(e)}'
        }), 500


@especialidades_bp.route('/download/<filename>')
def download_file(filename):
    """
    Endpoint para descargar archivo procesado
    
    Args:
        filename: Nombre del archivo a descargar
        
    Returns:
        Archivo Excel para descarga
    """
    try:
        # Validar que el archivo existe
        file_path = os.path.join(current_app.config['OUTPUT_FOLDER'], filename)
        
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': 'Archivo no encontrado'
            }), 404
        
        # Enviar archivo
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error al descargar archivo: {str(e)}'
        }), 500


@especialidades_bp.route('/validar', methods=['POST'])
def validar_archivo():
    """
    Endpoint para validar estructura del archivo sin procesarlo
    
    Returns:
        JSON con resultado de validación
    """
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
                'error': 'Formato no permitido'
            }), 400
        
        # Guardar temporalmente
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        temp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f"temp_{timestamp}_{filename}")
        file.save(temp_path)
        
        # Validar estructura
        import pandas as pd
        
        try:
            xls = pd.ExcelFile(temp_path)
            hojas_encontradas = xls.sheet_names
            
            validacion = {
                'success': True,
                'hojas_encontradas': hojas_encontradas,
                'validaciones': []
            }
            
            # Validar hoja "Imagenes"
            if 'Imagenes' in hojas_encontradas:
                df = pd.read_excel(temp_path, sheet_name='Imagenes')
                columnas_requeridas = ['Servicio_Principal', 'Nombre_Servicio_Principal_ajust']
                columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
                
                if columnas_faltantes:
                    validacion['validaciones'].append({
                        'hoja': 'Imagenes',
                        'valida': False,
                        'error': f'Faltan columnas: {", ".join(columnas_faltantes)}'
                    })
                else:
                    validacion['validaciones'].append({
                        'hoja': 'Imagenes',
                        'valida': True,
                        'registros': len(df)
                    })
            else:
                validacion['validaciones'].append({
                    'hoja': 'Imagenes',
                    'valida': False,
                    'error': 'Hoja no encontrada'
                })
            
            # Validar hoja "Laboratorio Clinico"
            if 'Laboratorio Clinico' in hojas_encontradas:
                df = pd.read_excel(temp_path, sheet_name='Laboratorio Clinico')
                columnas_requeridas = ['Servicio_Principal', 'Nombre_Servicio_Principal_ajust']
                columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
                
                if columnas_faltantes:
                    validacion['validaciones'].append({
                        'hoja': 'Laboratorio Clinico',
                        'valida': False,
                        'error': f'Faltan columnas: {", ".join(columnas_faltantes)}'
                    })
                else:
                    validacion['validaciones'].append({
                        'hoja': 'Laboratorio Clinico',
                        'valida': True,
                        'registros': len(df)
                    })
            else:
                validacion['validaciones'].append({
                    'hoja': 'Laboratorio Clinico',
                    'valida': False,
                    'error': 'Hoja no encontrada'
                })
            
            # Eliminar archivo temporal
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


@especialidades_bp.route('/resultados')
def resultados():
    """
    Vista de resultados del procesamiento
    """
    # Obtener parámetros de la URL
    archivo = request.args.get('archivo', '')
    total = request.args.get('total', 0, type=int)
    especificos = request.args.get('especificos', 0, type=int)
    generales = request.args.get('generales', 0, type=int)
    tiempo = request.args.get('tiempo', 0, type=float)
    
    if not archivo:
        return redirect(url_for('especialidades.index'))
    
    # Verificar que el archivo existe
    file_path = os.path.join(current_app.config['OUTPUT_FOLDER'], archivo)
    if not os.path.exists(file_path):
        return redirect(url_for('especialidades.index'))
    
    # Calcular porcentajes
    tasa_especificos = round((especificos / total * 100), 1) if total > 0 else 0
    tasa_generales = round((generales / total * 100), 1) if total > 0 else 0
    
    estadisticas = {
        'total_estudios': total,
        'estudios_especificos': especificos,
        'estudios_generales': generales,
        'tiempo_ejecucion': tiempo,
        'tasa_especificos': tasa_especificos,
        'tasa_generales': tasa_generales,
        'archivo_salida': archivo
    }
    
    return render_template('modules/especialidades/resultados.html', stats=estadisticas)