"""
Gestor de la Maestra de Contratos Vigentes
"""

import os
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
from werkzeug.utils import secure_filename
import shutil

class MaestraManager:
    """Gestiona la carga, actualización y lectura de la maestra de contratos"""
    
    # Carpeta donde se almacenan las maestras
    MAESTRA_FOLDER = 'data/maestra'
    MAESTRA_FILENAME = 'maestra_contratos_vigentes.xlsb'
    
    # Columnas esperadas en la maestra
    COLUMNAS_IMPORTANTES = {
        'numero_contrato': 'L',  # Número de contrato + año
        'fecha_inicial': 'M',     # Fecha inicial del contrato
        'tipo_proveedor': None,   # Se detecta automáticamente
        # Otrosí
        'otrosi_1_numero': 'P',
        'otrosi_1_fecha': 'Q',
        'otrosi_2_numero': 'S',
        'otrosi_2_fecha': 'T',
        'otrosi_3_numero': 'V',
        'otrosi_3_fecha': 'W',
        'otrosi_4_numero': 'Y',
        'otrosi_4_fecha': 'Z',
        # Actas de negociación
        'acta_1_numero': 'BU',
        'acta_1_fecha': 'BV',
        'acta_2_numero': 'BY',
        'acta_2_fecha': 'BZ',
        'acta_3_numero': 'CC',
        'acta_3_fecha': 'CD',
        'acta_4_numero': 'CG',
        'acta_4_fecha': 'CH',
        'acta_5_numero': 'CK',
        'acta_5_fecha': 'CL',
    }
    
    def __init__(self):
        """Inicializa el gestor y crea carpetas necesarias"""
        os.makedirs(self.MAESTRA_FOLDER, exist_ok=True)
    
    def subir_maestra(self, archivo_stream, filename: str) -> Dict[str, any]:
        """
        Sube y guarda una nueva maestra
        
        Args:
            archivo_stream: Stream del archivo subido
            filename: Nombre original del archivo
            
        Returns:
            Dict con success, mensaje y metadata
        """
        try:
            # Validar extensión
            if not filename.lower().endswith('.xlsb'):
                return {
                    'success': False,
                    'error': 'El archivo debe ser formato .xlsb'
                }
            
            # Hacer backup de maestra anterior si existe
            ruta_maestra = os.path.join(self.MAESTRA_FOLDER, self.MAESTRA_FILENAME)
            if os.path.exists(ruta_maestra):
                backup_name = f"maestra_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsb"
                backup_path = os.path.join(self.MAESTRA_FOLDER, backup_name)
                shutil.copy2(ruta_maestra, backup_path)
            
            # Guardar nueva maestra
            archivo_stream.save(ruta_maestra)
            
            # Validar que se pueda leer
            validacion = self.validar_maestra(ruta_maestra)
            
            if not validacion['valida']:
                # Restaurar backup si falla
                if os.path.exists(backup_path):
                    shutil.copy2(backup_path, ruta_maestra)
                
                return {
                    'success': False,
                    'error': f'Maestra inválida: {validacion["error"]}'
                }
            
            return {
                'success': True,
                'mensaje': 'Maestra actualizada exitosamente',
                'metadata': {
                    'filename': self.MAESTRA_FILENAME,
                    'fecha_actualizacion': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'total_contratos': validacion['total_contratos'],
                    'prestadores_salud': validacion['prestadores_salud']
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error al subir maestra: {str(e)}'
            }
    
    def validar_maestra(self, ruta_archivo: str) -> Dict[str, any]:
        """
        Valida que la maestra tenga el formato correcto
        
        Args:
            ruta_archivo: Ruta del archivo a validar
            
        Returns:
            Dict con validación y estadísticas
        """
        try:
            # Leer con pyxlsb
            from pyxlsb import open_workbook
            
            with open_workbook(ruta_archivo) as wb:
                # Buscar hoja de contratos vigentes
                hoja_contratos = None
                for sheet_name in wb.sheets:
                    if 'CONTRATO' in sheet_name.upper() and 'VIGENTE' in sheet_name.upper():
                        hoja_contratos = sheet_name
                        break
                
                if not hoja_contratos:
                    return {
                        'valida': False,
                        'error': 'No se encontró la hoja de contratos vigentes'
                    }
                
                # Leer datos
                data = []
                with wb.get_sheet(hoja_contratos) as sheet:
                    for row in sheet.rows():
                        data.append([item.v if item.v is not None else '' for item in row])
                
                if len(data) < 2:
                    return {
                        'valida': False,
                        'error': 'La maestra no contiene datos'
                    }
                
                # Buscar columna "TIPO DE PROVEEDOR"
                encabezados = data[0] if data else []
                tipo_proveedor_col = None
                
                for idx, header in enumerate(encabezados):
                    if header and 'TIPO' in str(header).upper() and 'PROVEEDOR' in str(header).upper():
                        tipo_proveedor_col = idx
                        break
                
                if tipo_proveedor_col is None:
                    return {
                        'valida': False,
                        'error': 'No se encontró la columna "TIPO DE PROVEEDOR"'
                    }
                
                # Contar contratos y prestadores de salud
                total_contratos = len(data) - 1  # Excluir encabezado
                prestadores_salud = 0
                
                for row in data[1:]:  # Saltar encabezado
                    if len(row) > tipo_proveedor_col:
                        tipo = str(row[tipo_proveedor_col]).upper()
                        if 'PRESTADOR' in tipo and 'SALUD' in tipo:
                            prestadores_salud += 1
                
                return {
                    'valida': True,
                    'total_contratos': total_contratos,
                    'prestadores_salud': prestadores_salud,
                    'tipo_proveedor_col': tipo_proveedor_col
                }
                
        except Exception as e:
            return {
                'valida': False,
                'error': f'Error al validar: {str(e)}'
            }
    
    def tiene_maestra(self) -> bool:
        """Verifica si existe una maestra cargada"""
        ruta_maestra = os.path.join(self.MAESTRA_FOLDER, self.MAESTRA_FILENAME)
        return os.path.exists(ruta_maestra)
    
    def obtener_info_maestra(self) -> Optional[Dict[str, any]]:
        """
        Obtiene información de la maestra actual
        
        Returns:
            Dict con información o None si no existe
        """
        if not self.tiene_maestra():
            return None
        
        ruta_maestra = os.path.join(self.MAESTRA_FOLDER, self.MAESTRA_FILENAME)
        
        try:
            # Obtener metadata del archivo
            stat_info = os.stat(ruta_maestra)
            fecha_modificacion = datetime.fromtimestamp(stat_info.st_mtime)
            tamano_kb = stat_info.st_size / 1024
            
            # Validar y obtener estadísticas
            validacion = self.validar_maestra(ruta_maestra)
            
            return {
                'filename': self.MAESTRA_FILENAME,
                'ruta': ruta_maestra,
                'fecha_modificacion': fecha_modificacion.strftime('%Y-%m-%d %H:%M:%S'),
                'tamano_kb': round(tamano_kb, 2),
                'total_contratos': validacion.get('total_contratos', 0),
                'prestadores_salud': validacion.get('prestadores_salud', 0),
                'valida': validacion.get('valida', False)
            }
            
        except Exception as e:
            return {
                'filename': self.MAESTRA_FILENAME,
                'error': str(e),
                'valida': False
            }
    
    def leer_contratos_prestadores_salud(self) -> List[Dict[str, any]]:
        """
        Lee la maestra y retorna solo contratos de prestadores de salud
        
        Returns:
            Lista de diccionarios con información de contratos
        """
        if not self.tiene_maestra():
            return []
        
        ruta_maestra = os.path.join(self.MAESTRA_FOLDER, self.MAESTRA_FILENAME)
        
        try:
            from pyxlsb import open_workbook
            
            with open_workbook(ruta_maestra) as wb:
                # Buscar hoja de contratos
                hoja_contratos = None
                for sheet_name in wb.sheets:
                    if 'CONTRATO' in sheet_name.upper() and 'VIGENTE' in sheet_name.upper():
                        hoja_contratos = sheet_name
                        break
                
                if not hoja_contratos:
                    return []
                
                # Leer datos
                data = []
                with wb.get_sheet(hoja_contratos) as sheet:
                    for row in sheet.rows():
                        data.append([item.v if item.v is not None else '' for item in row])
                
                if len(data) < 2:
                    return []
                
                # Buscar índice de columna "TIPO DE PROVEEDOR"
                encabezados = data[0]
                tipo_proveedor_col = None
                
                for idx, header in enumerate(encabezados):
                    if header and 'TIPO' in str(header).upper() and 'PROVEEDOR' in str(header).upper():
                        tipo_proveedor_col = idx
                        break
                
                if tipo_proveedor_col is None:
                    return []
                
                # Convertir columna L a índice (L = columna 12, índice 11)
                numero_contrato_col = 11  # Columna L (0-indexed)
                fecha_inicial_col = 12     # Columna M
                
                # Filtrar prestadores de salud
                contratos = []
                
                for idx, row in enumerate(data[1:], start=2):  # Empezar desde fila 2
                    if len(row) <= tipo_proveedor_col:
                        continue
                    
                    tipo = str(row[tipo_proveedor_col]).upper()
                    
                    if 'PRESTADOR' in tipo and 'SALUD' in tipo:
                        # Extraer información del contrato
                        numero_contrato = str(row[numero_contrato_col]) if len(row) > numero_contrato_col else ''
                        fecha_inicial = row[fecha_inicial_col] if len(row) > fecha_inicial_col else None
                        
                        if numero_contrato:
                            contrato_info = {
                                'fila': idx,
                                'numero_contrato': numero_contrato,
                                'fecha_inicial': fecha_inicial,
                                'tipo_proveedor': row[tipo_proveedor_col],
                                'datos_fila': row  # Guardar toda la fila para extraer otrosí y actas después
                            }
                            
                            # Extraer otrosí
                            contrato_info['otrosi'] = self._extraer_otrosi(row)
                            
                            # Extraer actas
                            contrato_info['actas'] = self._extraer_actas(row)
                            
                            contratos.append(contrato_info)
                
                return contratos
                
        except Exception as e:
            print(f"Error leyendo maestra: {e}")
            return []
    
    def _extraer_otrosi(self, row: list) -> List[Dict[str, any]]:
        """
        Extrae información de otrosí de una fila
        
        Args:
            row: Fila de datos de la maestra
            
        Returns:
            Lista de otrosí con número y fecha
        """
        otrosi_list = []
        
        # Columnas de otrosí (P, S, V, Y = índices 15, 18, 21, 24)
        otrosi_cols = [
            (15, 16),  # P, Q (Otrosí 1)
            (18, 19),  # S, T (Otrosí 2)
            (21, 22),  # V, W (Otrosí 3)
            (24, 25),  # Y, Z (Otrosí 4)
        ]
        
        for idx, (num_col, fecha_col) in enumerate(otrosi_cols, start=1):
            if len(row) > fecha_col:
                numero = row[num_col] if row[num_col] else None
                fecha = row[fecha_col] if row[fecha_col] else None
                
                if numero or fecha:
                    otrosi_list.append({
                        'numero': idx,
                        'numero_otrosi': numero,
                        'fecha': fecha
                    })
        
        return otrosi_list
    
    def _extraer_actas(self, row: list) -> List[Dict[str, any]]:
        """
        Extrae información de actas de negociación de una fila
        
        Args:
            row: Fila de datos de la maestra
            
        Returns:
            Lista de actas con número y fecha
        """
        actas_list = []
        
        # Columnas de actas (BU, BY, CC, CG, CK = índices 72, 76, 80, 84, 88)
        # BU es la columna 73, entonces índice 72
        actas_cols = [
            (72, 73),   # BU, BV (Acta 1)
            (76, 77),   # BY, BZ (Acta 2)
            (80, 81),   # CC, CD (Acta 3)
            (84, 85),   # CG, CH (Acta 4)
            (88, 89),   # CK, CL (Acta 5)
        ]
        
        for idx, (num_col, fecha_col) in enumerate(actas_cols, start=1):
            if len(row) > fecha_col:
                numero = row[num_col] if row[num_col] else None
                fecha = row[fecha_col] if row[fecha_col] else None
                
                if numero or fecha:
                    actas_list.append({
                        'numero': idx,
                        'numero_acta': numero,
                        'fecha': fecha
                    })
        
        return actas_list
    
    def buscar_contrato(self, termino_busqueda: str) -> List[Dict[str, any]]:
        """
        Busca contratos por número, año o proveedor
        
        Args:
            termino_busqueda: Término a buscar
            
        Returns:
            Lista de contratos que coinciden
        """
        contratos = self.leer_contratos_prestadores_salud()
        
        if not termino_busqueda:
            return contratos
        
        termino_lower = termino_busqueda.lower().strip()
        
        resultados = []
        for contrato in contratos:
            numero = str(contrato['numero_contrato']).lower()
            
            if termino_lower in numero:
                resultados.append(contrato)
        
        return resultados
    
    def obtener_contratos_por_anio(self, anio: int) -> List[Dict[str, any]]:
        """
        Obtiene todos los contratos de un año específico
        
        Args:
            anio: Año a filtrar (ej: 2024, 2025)
            
        Returns:
            Lista de contratos del año
        """
        contratos = self.leer_contratos_prestadores_salud()
        
        contratos_anio = []
        for contrato in contratos:
            numero = str(contrato['numero_contrato'])
            
            # Buscar año en el número de contrato (formato: XXXX-2024)
            if str(anio) in numero:
                contratos_anio.append(contrato)
        
        return contratos_anio