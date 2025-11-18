"""
Lógica del Consolidador de Servicios Médicos - Anexo 1
Procesa archivos XLSB con múltiples sedes de proveedores
"""
import pandas as pd
from pyxlsb import open_workbook
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
import os
import time


def procesar_anexo1_xlsb(filepath, fecha_acuerdo=None):
    """
    Procesa archivo XLSB del Anexo 1 con múltiples sedes
    
    Args:
        filepath: Ruta del archivo XLSB
        fecha_acuerdo: Fecha del acuerdo (opcional)
        
    Returns:
        dict: Resultado con datos consolidados
    """
    inicio = time.time()
    
    try:
        # Leer archivo XLSB
        anexo_data = []
        hoja_tarifas = None
        
        with open_workbook(filepath) as wb:
            # Buscar hoja de tarifas
            for sheet_name in wb.sheets:
                if 'TARIFA' in sheet_name.upper() and 'SERV' in sheet_name.upper():
                    hoja_tarifas = sheet_name
                    break
            
            if not hoja_tarifas:
                tiempo_fin = time.time()
                return {
                    'success': False,
                    'error': 'No se encontró la hoja TARIFAS DE SERV en el archivo',
                    'tiempo_ejecucion': round(tiempo_fin - inicio, 2)
                }
            
            # Leer datos de la hoja
            with wb.get_sheet(hoja_tarifas) as sheet:
                for row in sheet.rows():
                    row_values = [item.v for item in row]
                    anexo_data.append(row_values)
        
        # Extraer información de sedes y servicios
        sedes_info = []
        current_sede = None
        current_servicios = []
        
        i = 0
        while i < len(anexo_data):
            row = anexo_data[i]
            
            # Detectar nueva sede
            if row and any(cell and isinstance(cell, str) and 'CODIGO DE HABILITACIÓN' in cell.upper() for cell in row):
                # Guardar sede anterior si existe
                if current_sede:
                    sedes_info.append({
                        'sede': current_sede,
                        'servicios': current_servicios
                    })
                
                # Leer datos de la nueva sede
                if i + 1 < len(anexo_data):
                    sede_row = anexo_data[i + 1]
                    if sede_row and len(sede_row) > 2 and sede_row[2]:
                        current_sede = {
                            'codigo_habilitacion': sede_row[2],
                            'numero_sede': sede_row[3],
                            'nombre_sede': sede_row[4] if len(sede_row) > 4 else 'N/A',
                            'municipio': sede_row[1] if len(sede_row) > 1 else 'N/A'
                        }
                        current_servicios = []
                        i += 1
            
            # Detectar servicios
            elif current_sede and row and len(row) >= 7:
                # Verificar si es una fila de servicio
                if row[0] and isinstance(row[0], (int, float, str)):
                    try:
                        codigo_cups = str(row[0]).strip() if row[0] else ""
                        
                        # Validar que tenga código CUPS
                        if codigo_cups and codigo_cups != "":
                            servicio = {
                                'codigo_cups': codigo_cups,
                                'codigo_homologo': str(row[1]).strip() if row[1] else "",
                                'descripcion': str(row[2]).strip() if row[2] else "",
                                'tarifa_unitaria': row[3] if len(row) > 3 else None,
                                'tarifario': str(row[4]).strip() if len(row) > 4 and row[4] else "",
                                'tarifa_segun_tarifario': row[5] if len(row) > 5 else None,
                                'observaciones': str(row[6]).strip() if len(row) > 6 and row[6] else ""
                            }
                            current_servicios.append(servicio)
                    except:
                        pass
            
            i += 1
        
        # Guardar última sede
        if current_sede:
            sedes_info.append({
                'sede': current_sede,
                'servicios': current_servicios
            })
        
        # Crear consolidado
        consolidado = []
        
        for sede_data in sedes_info:
            sede = sede_data['sede']
            servicios = sede_data['servicios']
            
            # Formatear número de sede
            numero_sede = sede['numero_sede']
            if isinstance(numero_sede, float):
                if numero_sede.is_integer():
                    numero_sede_str = str(int(numero_sede))
                else:
                    numero_sede_str = str(numero_sede)
            elif isinstance(numero_sede, int):
                numero_sede_str = str(numero_sede)
            else:
                numero_sede_str = str(numero_sede) if numero_sede else ""
            
            # Rellenar con cero si es de un dígito
            if numero_sede_str and len(numero_sede_str) == 1:
                numero_sede_str = numero_sede_str.zfill(2)
            
            codigo_hab_completo = f"{sede['codigo_habilitacion']}-{numero_sede_str}"
            
            for servicio in servicios:
                consolidado.append({
                    'codigo_cups': servicio['codigo_cups'],
                    'codigo_homologo_manual': servicio['codigo_homologo'],
                    'descripcion_del_cups': servicio['descripcion'],
                    'tarifa_unitaria_en_pesos': servicio['tarifa_unitaria'],
                    'manual_tarifario': servicio['tarifario'],
                    'porcentaje_manual_tarifario': servicio['tarifa_segun_tarifario'],
                    'observaciones': servicio['observaciones'],
                    'codigo_de_habilitacion': codigo_hab_completo,
                    'fecha_acuerdo': fecha_acuerdo
                })
        
        tiempo_fin = time.time()
        
        return {
            'success': True,
            'consolidado': consolidado,
            'sedes_info': sedes_info,
            'total_sedes': len(sedes_info),
            'total_servicios': len(consolidado),
            'tiempo_ejecucion': round(tiempo_fin - inicio, 2)
        }
        
    except Exception as e:
        tiempo_fin = time.time()
        return {
            'success': False,
            'error': f'Error al procesar archivo: {str(e)}',
            'tiempo_ejecucion': round(tiempo_fin - inicio, 2)
        }

def generar_excel_consolidado(resultado, output_path):
    """
    Genera archivo Excel con formato POSITIVA
    
    Args:
        resultado: Diccionario con datos consolidados
        output_path: Ruta del archivo de salida
        
    Returns:
        bool: True si se generó exitosamente
    """
    try:
        consolidado = resultado['consolidado']
        
        if not consolidado:
            return False
        
        # Crear workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Hoja1"
        
        # Estilos del encabezado principal
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True, size=11)
        header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        
        # Escribir encabezado principal
        ws.merge_cells('A1:H1')
        ws['A1'] = 'ANEXO 1 PACTADO DEL PRESTADOR'
        ws['A1'].fill = header_fill
        ws['A1'].font = header_font
        ws['A1'].alignment = header_alignment
        
        ws['I1'] = 'INFO ACTA O ACUERDO'
        ws['I1'].fill = header_fill
        ws['I1'].font = header_font
        ws['I1'].alignment = header_alignment
        
        # Encabezados de columnas (fila 2)
        columnas = [
            'codigo_cups', 'codigo_homologo_manual', 'descripcion_del_cups',
            'tarifa_unitaria_en_pesos', 'manual_tarifario', 'porcentaje_manual_tarifario',
            'observaciones', 'codigo_de_habilitacion', 'fecha_acuerdo'
        ]
        
        column_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
        column_font = Font(bold=True)
        column_alignment = Alignment(horizontal="center", vertical="center")
        
        for col_idx, col_name in enumerate(columnas, 1):
            cell = ws.cell(row=2, column=col_idx)
            cell.value = col_name
            cell.fill = column_fill
            cell.font = column_font
            cell.alignment = column_alignment
        
        # Escribir datos
        for row_idx, row_data in enumerate(consolidado, 3):
            for col_idx, col_name in enumerate(columnas, 1):
                ws.cell(row=row_idx, column=col_idx, value=row_data[col_name])
        
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
        
        # Guardar
        wb.save(output_path)
        return True
        
    except Exception as e:
        print(f"Error al generar Excel: {e}")
        return False
