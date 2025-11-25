"""
Procesador de archivos ANEXO 1 en múltiples formatos - CORREGIDO
"""

import os
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import re

class AnexoProcessor:
    """Procesa archivos ANEXO 1 en múltiples formatos de Excel"""
    
    # Extensiones de Excel soportadas con prioridad
    EXTENSIONES_EXCEL = {
        '.xlsb': 1,  # Binario (prioridad más alta)
        '.xlsx': 2,  # Estándar moderno
        '.xlsm': 3,  # Con macros
        '.xls': 4,   # Formato antiguo
        '.csv': 5,   # CSV
        '.tsv': 6,   # TSV
        '.ods': 7    # OpenDocument
    }
    
    # Variaciones del nombre "ANEXO 1"
    VARIACIONES_ANEXO1 = [
        r'anexo\s*1',
        r'anexo\s*uno',
        r'anexo_1',
        r'anexo-1',
        r'anexo1'
    ]
    
    # Variaciones de "otrosí"
    VARIACIONES_OTROSI = [
        r'otros[ií]',
        r'otrosi',
        r'otro\s*s[ií]',
        r'ot\s*\d+',
        r'otros[ií]\s*\d+',
        r'otro\s*si\s*\d+'
    ]
    
    def __init__(self):
        """Inicializa el procesador"""
        pass
    
    def es_anexo1(self, nombre_archivo: str) -> bool:
        """
        Verifica si un archivo es un ANEXO 1 según su nombre
        
        Args:
            nombre_archivo: Nombre del archivo
            
        Returns:
            True si es ANEXO 1
        """
        nombre_lower = nombre_archivo.lower()
        
        for variacion in self.VARIACIONES_ANEXO1:
            if re.search(variacion, nombre_lower):
                return True
        
        return False
    
    def es_otrosi(self, nombre_archivo: str) -> bool:
        """
        Verifica si un archivo es de otrosí según su nombre
        
        Args:
            nombre_archivo: Nombre del archivo
            
        Returns:
            True si es otrosí
        """
        nombre_lower = nombre_archivo.lower()
        
        for variacion in self.VARIACIONES_OTROSI:
            if re.search(variacion, nombre_lower):
                return True
        
        return False
    
    def extraer_numero_otrosi(self, nombre_archivo: str) -> Optional[int]:
        """
        Extrae el número de otrosí del nombre del archivo
        
        Args:
            nombre_archivo: Nombre del archivo
            
        Returns:
            Número del otrosí o None si no se encuentra
        """
        nombre_lower = nombre_archivo.lower()
        
        # Buscar patrones como "otrosi 2", "ot2", "otrosí_3", etc.
        patrones = [
            r'otros[ií]\s*(\d+)',
            r'ot\s*(\d+)',
            r'otro\s*si\s*(\d+)',
            r'otrosi\s*(\d+)'
        ]
        
        for patron in patrones:
            match = re.search(patron, nombre_lower)
            if match:
                return int(match.group(1))
        
        # Si dice otrosi pero no tiene número, asumir 1
        if self.es_otrosi(nombre_archivo):
            return 1
        
        return None
    
    def extraer_numero_acta(self, nombre_archivo: str) -> Optional[int]:
        """
        Extrae el número de acta del nombre del archivo
        
        Args:
            nombre_archivo: Nombre del archivo
            
        Returns:
            Número del acta o None si no se encuentra
        """
        nombre_lower = nombre_archivo.lower()
        
        # Buscar patrones como "acta 2", "acta_3", "acta-1", etc.
        patrones = [
            r'acta\s*(\d+)',
            r'acta_(\d+)',
            r'acta-(\d+)'
        ]
        
        for patron in patrones:
            match = re.search(patron, nombre_lower)
            if match:
                return int(match.group(1))
        
        return None
    
    def es_extension_excel(self, nombre_archivo: str) -> bool:
        """
        Verifica si el archivo tiene extensión de Excel
        
        Args:
            nombre_archivo: Nombre del archivo
            
        Returns:
            True si es extensión de Excel
        """
        extension = os.path.splitext(nombre_archivo)[1].lower()
        return extension in self.EXTENSIONES_EXCEL
    
    def filtrar_archivos_anexo1(self, archivos: List[str]) -> List[Dict[str, any]]:
        """
        Filtra archivos que sean ANEXO 1 en formato Excel
        
        Args:
            archivos: Lista de nombres de archivos
            
        Returns:
            Lista de diccionarios con información de archivos encontrados
        """
        anexos_encontrados = []
        
        for archivo in archivos:
            if self.es_anexo1(archivo) and self.es_extension_excel(archivo):
                extension = os.path.splitext(archivo)[1].lower()
                prioridad = self.EXTENSIONES_EXCEL.get(extension, 99)
                
                anexos_encontrados.append({
                    'nombre': archivo,
                    'extension': extension,
                    'prioridad': prioridad,
                    'es_otrosi': self.es_otrosi(archivo),
                    'numero_otrosi': self.extraer_numero_otrosi(archivo) if self.es_otrosi(archivo) else None,
                    'numero_acta': self.extraer_numero_acta(archivo)
                })
        
        # Ordenar por prioridad (menor número = mayor prioridad)
        anexos_encontrados.sort(key=lambda x: x['prioridad'])
        
        return anexos_encontrados
    
    def filtrar_archivos_otrosi(self, archivos: List[str]) -> List[Dict[str, any]]:
        """
        Filtra y ordena archivos de otrosí
        
        Args:
            archivos: Lista de nombres de archivos
            
        Returns:
            Lista ordenada de otrosí (mayor a menor)
        """
        otrosi_encontrados = []
        
        for archivo in archivos:
            if self.es_otrosi(archivo) and self.es_extension_excel(archivo):
                numero = self.extraer_numero_otrosi(archivo)
                
                otrosi_encontrados.append({
                    'nombre': archivo,
                    'numero_otrosi': numero if numero else 1,
                    'extension': os.path.splitext(archivo)[1].lower()
                })
        
        # Ordenar por número de otrosí (mayor primero)
        otrosi_encontrados.sort(key=lambda x: x['numero_otrosi'], reverse=True)
        
        return otrosi_encontrados
    
    def leer_archivo_excel(self, ruta_archivo: str, hoja: str = None) -> Optional[pd.DataFrame]:
        """
        Lee cualquier formato de Excel y retorna DataFrame
        
        Args:
            ruta_archivo: Ruta completa del archivo
            hoja: Nombre de la hoja a leer (opcional)
            
        Returns:
            DataFrame con los datos o None si falla
        """
        extension = os.path.splitext(ruta_archivo)[1].lower()
        
        try:
            if extension == '.xlsb':
                return self._leer_xlsb(ruta_archivo, hoja)
            
            elif extension in ['.xlsx', '.xlsm']:
                if hoja:
                    return pd.read_excel(ruta_archivo, sheet_name=hoja, engine='openpyxl', header=None)
                return pd.read_excel(ruta_archivo, engine='openpyxl', header=None)
            
            elif extension == '.xls':
                if hoja:
                    return pd.read_excel(ruta_archivo, sheet_name=hoja, engine='xlrd', header=None)
                return pd.read_excel(ruta_archivo, engine='xlrd', header=None)
            
            elif extension == '.csv':
                return pd.read_csv(ruta_archivo, encoding='utf-8-sig', header=None)
            
            elif extension == '.tsv':
                return pd.read_csv(ruta_archivo, sep='\t', encoding='utf-8-sig', header=None)
            
            elif extension == '.ods':
                if hoja:
                    return pd.read_excel(ruta_archivo, sheet_name=hoja, engine='odf', header=None)
                return pd.read_excel(ruta_archivo, engine='odf', header=None)
            
            else:
                # Intento genérico
                return pd.read_excel(ruta_archivo, header=None)
        
        except Exception as e:
            print(f"❌ Error leyendo {ruta_archivo}: {e}")
            return None
    
    def _leer_xlsb(self, ruta_archivo: str, hoja_objetivo: str = None) -> Optional[pd.DataFrame]:
        """
        Lee archivo XLSB específicamente
        
        Args:
            ruta_archivo: Ruta del archivo XLSB
            hoja_objetivo: Nombre de la hoja a leer (opcional)
            
        Returns:
            DataFrame con los datos
        """
        try:
            from pyxlsb import open_workbook
            
            with open_workbook(ruta_archivo) as wb:
                # Si se especifica hoja, usarla
                if hoja_objetivo and hoja_objetivo in wb.sheets:
                    hoja_tarifas = hoja_objetivo
                else:
                    # Buscar hoja de tarifas
                    hoja_tarifas = None
                    for sheet_name in wb.sheets:
                        nombre_upper = sheet_name.upper()
                        if 'TARIFA' in nombre_upper and 'SERV' in nombre_upper:
                            hoja_tarifas = sheet_name
                            break
                    
                    if not hoja_tarifas:
                        # Usar primera hoja
                        hoja_tarifas = wb.sheets[0] if wb.sheets else None
                
                if not hoja_tarifas:
                    return None
                
                # Leer datos
                data = []
                with wb.get_sheet(hoja_tarifas) as sheet:
                    for row in sheet.rows():
                        row_values = [item.v if item.v is not None else '' for item in row]
                        data.append(row_values)
                
                # Convertir a DataFrame
                return pd.DataFrame(data)
        
        except Exception as e:
            print(f"Error leyendo XLSB: {e}")
            return None
    
    def validar_formato_positiva(self, df: pd.DataFrame, nombre_archivo: str) -> Dict[str, any]:
        """
        Valida si el DataFrame está en formato POSITIVA
        
        El formato POSITIVA debe tener:
        1. Encabezado "ANEXO 1 PACTADO DEL PRESTADOR" en las primeras filas
        2. Columnas esperadas: CUPS, DESCRIPCION, TARIFA, MANUAL, HABILITACION
        
        Args:
            df: DataFrame a validar
            nombre_archivo: Nombre del archivo (para mensajes)
            
        Returns:
            Dict con validación y detalles
        """
        if df is None or df.empty:
            return {
                'valido': False,
                'mensaje': f'No hay anexo 1 en formato + {nombre_archivo} (archivo vacío)',
                'tiene_encabezado': False,
                'columnas_correctas': False
            }
        
        resultado = {
            'valido': False,
            'mensaje': '',
            'tiene_encabezado': False,
            'columnas_correctas': False,
            'fila_encabezado': None
        }
        
        # Verificar encabezado "ANEXO 1 PACTADO DEL PRESTADOR" en las primeras filas
        for i in range(min(10, len(df))):
            fila = df.iloc[i].astype(str).str.upper()
            for val in fila:
                if 'ANEXO' in str(val) and '1' in str(val) and 'PACTADO' in str(val):
                    resultado['tiene_encabezado'] = True
                    break
            if resultado['tiene_encabezado']:
                break
        
        # Verificar columnas esperadas (buscar en primeras 15 filas)
        columnas_esperadas = [
            'CUPS',
            'DESCRIPCION',
            'TARIFA',
            'MANUAL',
            'HABILITACION'
        ]
        
        for i in range(min(15, len(df))):
            fila = df.iloc[i].astype(str).str.upper()
            matches = sum(1 for col in columnas_esperadas if any(col in str(val) for val in fila))
            
            if matches >= 3:
                resultado['columnas_correctas'] = True
                resultado['fila_encabezado'] = i
                break
        
        resultado['valido'] = resultado['tiene_encabezado'] and resultado['columnas_correctas']
        
        if not resultado['valido']:
            if not resultado['tiene_encabezado']:
                resultado['mensaje'] = f"No hay anexo 1 en formato + {nombre_archivo} (falta encabezado POSITIVA)"
            elif not resultado['columnas_correctas']:
                resultado['mensaje'] = f"No hay anexo 1 en formato + {nombre_archivo} (columnas incorrectas)"
        else:
            resultado['mensaje'] = f"✅ Formato POSITIVA válido: {nombre_archivo}"
        
        return resultado
    
    def extraer_sedes_del_encabezado(self, df: pd.DataFrame) -> List[Dict[str, any]]:
        """
        Extrae información de sedes del encabezado del ANEXO 1
        
        Maneja el caso de múltiples sedes sin discriminación de servicios
        
        Returns:
            Lista de sedes encontradas
        """
        sedes = []
        
        # Buscar filas con "CODIGO DE HABILITACIÓN"
        for idx, row in df.iterrows():
            row_str = ' '.join([str(cell).upper() for cell in row if pd.notna(cell)])
            
            if 'CODIGO DE HABILITACIÓN' in row_str or 'CÓDIGO DE HABILITACIÓN' in row_str or 'CODIGO DE HABILITACION' in row_str:
                # La fila siguiente contiene los datos de la sede
                if idx + 1 < len(df):
                    sede_row = df.iloc[idx + 1]
                    
                    codigo_hab = None
                    numero_sede = None
                    nombre_sede = None
                    municipio = None
                    
                    # Buscar valores en la fila de datos
                    for i, val in enumerate(sede_row):
                        if pd.notna(val) and str(val).strip():
                            val_str = str(val).strip()
                            
                            # Columna C suele tener código de habilitación
                            if i == 2:
                                codigo_hab = val_str
                            # Columna D suele tener número de sede
                            elif i == 3:
                                numero_sede = val
                            # Columna E suele tener nombre
                            elif i == 4:
                                nombre_sede = val_str
                            # Columna B suele tener municipio
                            elif i == 1:
                                municipio = val_str
                    
                    if codigo_hab:
                        # Formatear número de sede
                        numero_str = '01'
                        if numero_sede is not None:
                            if isinstance(numero_sede, float) and numero_sede.is_integer():
                                numero_str = str(int(numero_sede)).zfill(2)
                            elif isinstance(numero_sede, int):
                                numero_str = str(numero_sede).zfill(2)
                            else:
                                numero_str = str(numero_sede).zfill(2)
                        
                        sedes.append({
                            'codigo_habilitacion': codigo_hab,
                            'numero_sede': numero_str,
                            'codigo_completo': f"{codigo_hab}-{numero_str}",
                            'nombre_sede': nombre_sede,
                            'municipio': municipio
                        })
        
        return sedes
    
    def extraer_servicios_de_anexo(self, df: pd.DataFrame) -> Dict[str, any]:
        """
        Extrae servicios de un DataFrame de ANEXO 1
        
        Args:
            df: DataFrame con datos del ANEXO 1
            
        Returns:
            Dict con sedes y servicios extraídos
        """
        if df is None or df.empty:
            return {
                'success': False,
                'error': 'DataFrame vacío'
            }
        
        try:
            sedes_info = []
            current_sede = None
            current_servicios = []
            fila_inicio_servicios = None
            en_seccion_servicios = False
            
            # Primero, extraer todas las sedes del encabezado
            sedes_encabezado = self.extraer_sedes_del_encabezado(df)
            
            for idx, row in df.iterrows():
                row_str = ' '.join([str(cell).upper() for cell in row if pd.notna(cell)])
                
                # Detectar inicio de sede
                if 'CODIGO DE HABILITACIÓN' in row_str or 'CÓDIGO DE HABILITACIÓN' in row_str or 'CODIGO DE HABILITACION' in row_str:
                    # Guardar sede anterior si existe
                    if current_sede and current_servicios:
                        sedes_info.append({
                            'sede': current_sede,
                            'servicios': current_servicios.copy()
                        })
                    
                    # Leer información de la sede (siguiente fila)
                    current_servicios = []
                    en_seccion_servicios = False
                    fila_inicio_servicios = None
                    
                    if idx + 1 < len(df):
                        sede_row = df.iloc[idx + 1]
                        
                        codigo_hab = None
                        numero_sede = None
                        nombre_sede = None
                        municipio = None
                        
                        for i, val in enumerate(sede_row):
                            if pd.notna(val) and str(val).strip():
                                val_str = str(val).strip()
                                if i == 2:
                                    codigo_hab = val_str
                                elif i == 3:
                                    numero_sede = val
                                elif i == 4:
                                    nombre_sede = val_str
                                elif i == 1:
                                    municipio = val_str
                        
                        if codigo_hab:
                            numero_str = '01'
                            if numero_sede is not None:
                                if isinstance(numero_sede, float) and numero_sede.is_integer():
                                    numero_str = str(int(numero_sede)).zfill(2)
                                elif isinstance(numero_sede, int):
                                    numero_str = str(numero_sede).zfill(2)
                                else:
                                    numero_str = str(numero_sede).zfill(2)
                            
                            current_sede = {
                                'codigo_habilitacion': codigo_hab,
                                'numero_sede': numero_str,
                                'codigo_completo': f"{codigo_hab}-{numero_str}",
                                'nombre_sede': nombre_sede,
                                'municipio': municipio
                            }
                    
                    continue
                
                # Detectar fila de encabezados de servicios
                if not en_seccion_servicios:
                    if any(keyword in row_str for keyword in ['CODIGO CUPS', 'CÓDIGO CUPS', 'CODIGO_CUPS', 'ITEM']):
                        en_seccion_servicios = True
                        fila_inicio_servicios = idx + 1
                        continue
                
                # Extraer servicios
                if en_seccion_servicios and current_sede and idx >= (fila_inicio_servicios or 0):
                    # Verificar si es una fila de servicio válida
                    primera_celda = row.iloc[0] if len(row) > 0 else None
                    segunda_celda = row.iloc[1] if len(row) > 1 else None
                    
                    # La primera o segunda celda debe tener contenido
                    if pd.notna(primera_celda) or pd.notna(segunda_celda):
                        codigo_cups = None
                        
                        # Determinar posición del código CUPS
                        if pd.notna(segunda_celda) and str(segunda_celda).strip():
                            # Si hay ITEM en col 0, CUPS en col 1
                            codigo_cups = str(segunda_celda).strip()
                            descripcion_col = 2
                            tarifa_col = 3
                            manual_col = 4
                            porcentaje_col = 5
                            observaciones_col = 6
                        elif pd.notna(primera_celda) and str(primera_celda).strip():
                            codigo_cups = str(primera_celda).strip()
                            descripcion_col = 1
                            tarifa_col = 2
                            manual_col = 3
                            porcentaje_col = 4
                            observaciones_col = 5
                        
                        if codigo_cups:
                            # Filtrar encabezados y totales
                            codigo_upper = codigo_cups.upper()
                            if any(kw in codigo_upper for kw in ['CODIGO', 'CUPS', 'DESCRIPCION', 'TARIFA', 'MANUAL', 'TOTAL', 'ITEM']):
                                continue
                            
                            # Filtrar filas vacías o solo con número de item
                            try:
                                int(codigo_cups)
                                # Es solo un número (probablemente ITEM), buscar CUPS en siguiente columna
                                if len(row) > 1 and pd.notna(row.iloc[1]):
                                    codigo_cups = str(row.iloc[1]).strip()
                                    descripcion_col = 2
                                    tarifa_col = 3
                                    manual_col = 4
                                    porcentaje_col = 5
                                    observaciones_col = 6
                            except ValueError:
                                pass
                            
                            # Verificar que no sea encabezado
                            if codigo_cups.upper() in ['CODIGO CUPS', 'CÓDIGO CUPS', 'CUPS']:
                                continue
                            
                            servicio = {
                                'codigo_cups': codigo_cups,
                                'codigo_homologo': str(row.iloc[descripcion_col - 1]).strip() if len(row) > descripcion_col - 1 and pd.notna(row.iloc[descripcion_col - 1]) else '',
                                'descripcion': str(row.iloc[descripcion_col]).strip() if len(row) > descripcion_col and pd.notna(row.iloc[descripcion_col]) else '',
                                'tarifa_unitaria': row.iloc[tarifa_col] if len(row) > tarifa_col and pd.notna(row.iloc[tarifa_col]) else 0,
                                'tarifario': str(row.iloc[manual_col]).strip() if len(row) > manual_col and pd.notna(row.iloc[manual_col]) else '',
                                'tarifa_segun_tarifario': str(row.iloc[porcentaje_col]).strip() if len(row) > porcentaje_col and pd.notna(row.iloc[porcentaje_col]) else '',
                                'observaciones': str(row.iloc[observaciones_col]).strip() if len(row) > observaciones_col and pd.notna(row.iloc[observaciones_col]) else ''
                            }
                            
                            current_servicios.append(servicio)
            
            # Guardar última sede
            if current_sede and current_servicios:
                sedes_info.append({
                    'sede': current_sede,
                    'servicios': current_servicios.copy()
                })
            
            # CASO ESPECIAL: Múltiples sedes sin discriminación de servicios
            # Si hay múltiples sedes en el encabezado pero solo una sección de servicios
            if len(sedes_encabezado) > 1 and len(sedes_info) == 1:
                servicios_base = sedes_info[0]['servicios']
                sedes_info = []
                
                for sede in sedes_encabezado:
                    sedes_info.append({
                        'sede': sede,
                        'servicios': servicios_base.copy()
                    })
            
            # Calcular totales
            total_servicios = sum(len(sede_data['servicios']) for sede_data in sedes_info)
            
            return {
                'success': True,
                'sedes_info': sedes_info,
                'total_sedes': len(sedes_info),
                'total_servicios': total_servicios
            }
        
        except Exception as e:
            import traceback
            return {
                'success': False,
                'error': f'Error extrayendo servicios: {str(e)}',
                'traceback': traceback.format_exc()
            }
    
    def procesar_archivo_completo(self, ruta_archivo: str) -> Dict[str, any]:
        """
        Procesa un archivo ANEXO 1 completo
        
        Args:
            ruta_archivo: Ruta del archivo
            
        Returns:
            Dict con toda la información procesada
        """
        nombre_archivo = os.path.basename(ruta_archivo)
        
        # Leer archivo
        df = self.leer_archivo_excel(ruta_archivo)
        
        if df is None:
            return {
                'success': False,
                'error': f'No se pudo leer el archivo: {nombre_archivo}',
                'nombre_archivo': nombre_archivo
            }
        
        # Validar formato POSITIVA
        validacion = self.validar_formato_positiva(df, nombre_archivo)
        
        if not validacion['valido']:
            return {
                'success': False,
                'error': validacion['mensaje'],
                'nombre_archivo': nombre_archivo,
                'validacion': validacion
            }
        
        # Extraer servicios
        extraccion = self.extraer_servicios_de_anexo(df)
        
        if not extraccion['success']:
            return {
                'success': False,
                'error': extraccion.get('error', 'Error desconocido'),
                'nombre_archivo': nombre_archivo
            }
        
        return {
            'success': True,
            'nombre_archivo': nombre_archivo,
            'extension': os.path.splitext(nombre_archivo)[1],
            'validacion': validacion,
            'sedes_info': extraccion['sedes_info'],
            'total_sedes': extraccion['total_sedes'],
            'total_servicios': extraccion['total_servicios']
        }