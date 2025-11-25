"""
Gestor de la Maestra de Contratos Vigentes - CORREGIDO
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
    
    def __init__(self):
        """Inicializa el gestor y crea carpetas necesarias"""
        os.makedirs(self.MAESTRA_FOLDER, exist_ok=True)
        self.maestra = None
        self.ultima_carga = None
        self._tipo_proveedor_col = None
        
        # Intentar cargar maestra existente
        if self.tiene_maestra():
            self._cargar_maestra_automatica()
    
    def _cargar_maestra_automatica(self):
        """Carga la maestra automáticamente si existe"""
        ruta = os.path.join(self.MAESTRA_FOLDER, self.MAESTRA_FILENAME)
        if os.path.exists(ruta):
            try:
                resultado = self.cargar_maestra(ruta)
                if resultado['success']:
                    print(f"Maestra cargada automáticamente: {resultado['total_contratos']} contratos")
            except Exception as e:
                print(f"Error cargando maestra automáticamente: {e}")
    
    def cargar_maestra(self, filepath: str) -> Dict[str, any]:
        """
        Carga la maestra desde un archivo XLSB
        
        Args:
            filepath: Ruta del archivo a cargar
            
        Returns:
            Dict con success, total_contratos, total_prestadores
        """
        try:
            from pyxlsb import open_workbook
            
            with open_workbook(filepath) as wb:
                # Buscar hoja de contratos vigentes
                hoja_contratos = None
                for sheet_name in wb.sheets:
                    if 'CONTRATO' in sheet_name.upper() and 'VIGENTE' in sheet_name.upper():
                        hoja_contratos = sheet_name
                        break
                
                if not hoja_contratos:
                    # Intentar con primera hoja
                    hoja_contratos = wb.sheets[0] if wb.sheets else None
                
                if not hoja_contratos:
                    return {
                        'success': False,
                        'error': 'No se encontró la hoja de contratos vigentes'
                    }
                
                # Leer datos
                data = []
                with wb.get_sheet(hoja_contratos) as sheet:
                    for row in sheet.rows():
                        data.append([item.v if item.v is not None else '' for item in row])
                
                if len(data) < 2:
                    return {
                        'success': False,
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
                        'success': False,
                        'error': 'No se encontró la columna "TIPO DE PROVEEDOR"'
                    }
                
                self._tipo_proveedor_col = tipo_proveedor_col
                
                # Contar contratos y prestadores de salud
                total_contratos = len(data) - 1  # Excluir encabezado
                prestadores_salud = 0
                
                for row in data[1:]:  # Saltar encabezado
                    if len(row) > tipo_proveedor_col:
                        tipo = str(row[tipo_proveedor_col]).upper()
                        if 'PRESTADOR' in tipo and 'SALUD' in tipo:
                            prestadores_salud += 1
                
                # Guardar datos en memoria
                self.maestra = data
                self.ultima_carga = datetime.now()
                
                return {
                    'success': True,
                    'total_contratos': total_contratos,
                    'total_prestadores': prestadores_salud
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Error al cargar maestra: {str(e)}'
            }
    
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
            backup_path = None
            
            if os.path.exists(ruta_maestra):
                backup_name = f"maestra_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsb"
                backup_path = os.path.join(self.MAESTRA_FOLDER, backup_name)
                shutil.copy2(ruta_maestra, backup_path)
            
            # Guardar nueva maestra
            archivo_stream.save(ruta_maestra)
            
            # Cargar y validar
            resultado = self.cargar_maestra(ruta_maestra)
            
            if not resultado['success']:
                # Restaurar backup si falla
                if backup_path and os.path.exists(backup_path):
                    shutil.copy2(backup_path, ruta_maestra)
                
                return {
                    'success': False,
                    'error': f'Maestra inválida: {resultado["error"]}'
                }
            
            return {
                'success': True,
                'mensaje': 'Maestra actualizada exitosamente',
                'total_contratos': resultado['total_contratos'],
                'total_prestadores': resultado['total_prestadores'],
                'metadata': {
                    'filename': self.MAESTRA_FILENAME,
                    'fecha_actualizacion': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'total_contratos': resultado['total_contratos'],
                    'prestadores_salud': resultado['total_prestadores']
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error al subir maestra: {str(e)}'
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
            
            # Si no está cargada en memoria, cargarla
            if self.maestra is None:
                self.cargar_maestra(ruta_maestra)
            
            total_contratos = len(self.maestra) - 1 if self.maestra else 0
            prestadores_salud = len(self.obtener_contratos_prestadores()) if self.maestra else 0
            
            return {
                'filename': self.MAESTRA_FILENAME,
                'ruta': ruta_maestra,
                'fecha_modificacion': fecha_modificacion.strftime('%Y-%m-%d %H:%M:%S'),
                'tamano_kb': round(tamano_kb, 2),
                'total_contratos': total_contratos,
                'prestadores_salud': prestadores_salud,
                'valida': True
            }
            
        except Exception as e:
            return {
                'filename': self.MAESTRA_FILENAME,
                'error': str(e),
                'valida': False
            }
    
    def obtener_contratos_prestadores(self) -> List[Dict[str, any]]:
        """
        Obtiene todos los contratos de prestadores de salud
        
        Returns:
            Lista de diccionarios con información de contratos
        """
        if self.maestra is None:
            if self.tiene_maestra():
                ruta = os.path.join(self.MAESTRA_FOLDER, self.MAESTRA_FILENAME)
                self.cargar_maestra(ruta)
            else:
                return []
        
        if self.maestra is None or self._tipo_proveedor_col is None:
            return []
        
        contratos = []
        
        # Columna L = índice 11, Columna M = índice 12
        numero_contrato_col = 11
        fecha_inicial_col = 12
        
        for idx, row in enumerate(self.maestra[1:], start=2):  # Empezar desde fila 2
            if len(row) <= self._tipo_proveedor_col:
                continue
            
            tipo = str(row[self._tipo_proveedor_col]).upper()
            
            if 'PRESTADOR' in tipo and 'SALUD' in tipo:
                # Extraer información del contrato
                numero_contrato = str(row[numero_contrato_col]) if len(row) > numero_contrato_col and row[numero_contrato_col] else ''
                fecha_inicial = row[fecha_inicial_col] if len(row) > fecha_inicial_col else None
                
                # Formatear fecha
                if fecha_inicial:
                    if hasattr(fecha_inicial, 'strftime'):
                        fecha_inicial = fecha_inicial.strftime('%d/%m/%Y')
                    else:
                        fecha_inicial = str(fecha_inicial)
                
                if numero_contrato:
                    contrato_info = {
                        'fila': idx,
                        'numero_contrato': numero_contrato,
                        'fecha_inicial': fecha_inicial,
                        'tipo_proveedor': row[self._tipo_proveedor_col],
                        'datos_fila': row,
                        'otrosi': self._extraer_otrosi(row),
                        'actas': self._extraer_actas(row)
                    }
                    
                    contratos.append(contrato_info)
        
        return contratos
    
    def buscar_contrato(self, termino_busqueda: str) -> List[Dict[str, any]]:
        """
        Busca contratos por número
        
        Args:
            termino_busqueda: Término a buscar
            
        Returns:
            Lista de contratos que coinciden
        """
        contratos = self.obtener_contratos_prestadores()
        
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
        contratos = self.obtener_contratos_prestadores()
        
        contratos_anio = []
        for contrato in contratos:
            numero = str(contrato['numero_contrato'])
            
            if str(anio) in numero:
                contratos_anio.append(contrato)
        
        return contratos_anio
    
    def obtener_anios_disponibles(self) -> List[int]:
        """
        Obtiene los años disponibles en la maestra
        
        Returns:
            Lista de años ordenados
        """
        contratos = self.obtener_contratos_prestadores()
        
        anios = set()
        for contrato in contratos:
            numero = str(contrato['numero_contrato'])
            # Buscar año en el número de contrato (formato: XXXX-2024)
            partes = numero.split('-')
            if len(partes) >= 2:
                try:
                    anio = int(partes[-1])
                    if 2000 <= anio <= 2100:
                        anios.add(anio)
                except ValueError:
                    pass
        
        return sorted(anios, reverse=True)
    
    def _extraer_otrosi(self, row: list) -> List[Dict[str, any]]:
        """
        Extrae información de otrosí de una fila
        
        Columnas de otrosí según la maestra:
        - P (15): Número Otrosí 1, Q (16): Fecha Otrosí 1
        - S (18): Número Otrosí 2, T (19): Fecha Otrosí 2
        - V (21): Número Otrosí 3, W (22): Fecha Otrosí 3
        - Y (24): Número Otrosí 4, Z (25): Fecha Otrosí 4
        """
        otrosi_list = []
        
        # Columnas de otrosí (índice 0-based)
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
                
                # Solo agregar si hay algún dato
                if numero or fecha:
                    # Formatear fecha
                    if fecha:
                        if hasattr(fecha, 'strftime'):
                            fecha = fecha.strftime('%d/%m/%Y')
                        else:
                            fecha = str(fecha)
                    
                    otrosi_list.append({
                        'numero': idx,
                        'numero_otrosi': numero,
                        'fecha': fecha
                    })
        
        return otrosi_list
    
    def _extraer_actas(self, row: list) -> List[Dict[str, any]]:
        """
        Extrae información de actas de negociación de una fila
        
        Columnas de actas según la maestra:
        - BU (72): Número Acta 1, BV (73): Fecha Acta 1
        - BY (76): Número Acta 2, BZ (77): Fecha Acta 2
        - CC (80): Número Acta 3, CD (81): Fecha Acta 3
        - CG (84): Número Acta 4, CH (85): Fecha Acta 4
        - CK (88): Número Acta 5, CL (89): Fecha Acta 5
        """
        actas_list = []
        
        # Columnas de actas (índice 0-based)
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
                
                # Solo agregar si hay algún dato
                if numero or fecha:
                    # Formatear fecha
                    if fecha:
                        if hasattr(fecha, 'strftime'):
                            fecha = fecha.strftime('%d/%m/%Y')
                        else:
                            fecha = str(fecha)
                    
                    actas_list.append({
                        'numero': idx,
                        'numero_acta': numero,
                        'fecha': fecha
                    })
        
        return actas_list