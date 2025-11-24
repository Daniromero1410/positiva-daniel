"""
Procesador de archivos ANEXO 1 en múltiples formatos
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
            r'otro\s*si\s*(\d+)'
        ]
        
        for patron in patrones:
            match = re.search(patron, nombre_lower)
            if match:
                return int(match.group(1))
        
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
    
    def leer_archivo_excel(self, ruta_archivo: str) -> Optional[pd.DataFrame]:
        """
        Lee cualquier formato de Excel y retorna DataFrame
        
        Args:
            ruta_archivo: Ruta completa del archivo
            
        Returns:
            DataFrame con los datos o None si falla
        """
        extension = os.path.splitext(ruta_archivo)[1].lower()
        
        try:
            if extension == '.xlsb':
                return self._leer_xlsb(ruta_archivo)
            
            elif extension in ['.xlsx', '.xlsm']:
                return pd.read_excel(ruta_archivo, engine='openpyxl', header=None)
            
            elif extension == '.xls':
                return pd.read_excel(ruta_archivo, engine='xlrd', header=None)
            
            elif extension == '.csv':
                return pd.read_csv(ruta_archivo, encoding='utf-8-sig', header=None)
            
            elif extension == '.tsv':
                return pd.read_csv(ruta_archivo, sep='\t', encoding='utf-8-sig', header=None)
            
            elif extension == '.ods':
                return pd.read_excel(ruta_archivo, engine='odf', header=None)
            
            else:
                # Intento genérico
                return pd.read_excel(ruta_archivo, header=None)
        
        except Exception as e:
            print(f"❌ Error leyendo {ruta_archivo}: {e}")
            return None
    
    def _leer_xlsb(self, ruta_archivo: str) -> Optional[pd.DataFrame]:
        """
        Lee archivo XLSB específicamente
        
        Args:
            ruta_archivo: Ruta del archivo XLSB
            
        Returns:
            DataFrame con los datos
        """
        try:
            from pyxlsb import open_workbook
            
            with open_workbook(ruta_archivo) as wb:
                # Buscar hoja de tarifas
                hoja_tarifas = None
                for sheet_name in wb.sheets:
                    nombre_upper = sheet_name.upper()
                    if 'TARIFA' in nombre_upper and 'SERV' in nombre_upper:
                        hoja_tarifas = sheet_name
                        break
                
                if not hoja_tarifas:
                    # Usar primera hoja
                    hoja_tarifas = wb.sheets[0]
                
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
            'hoja_nombre': None
        }
        
        # Verificar encabezado "ANEXO 1 PACTADO DEL PRESTADOR" en las primeras filas
        for i in range(min(5, len(df))):
            fila = df.iloc[i].astype(str).str.upper()
            if any('ANEXO' in str(val) and '1' in str(val) and 'PACTADO' in str(val) for val in fila):
                resultado['tiene_encabezado'] = True
                break
        
        # Verificar columnas esperadas (buscar en primeras 10 filas)
        columnas_esperadas = [
            'CUPS',
            'DESCRIPCION',
            'TARIFA',
            'MANUAL',
            'HABILITACION'
        ]
        
        for i in range(min(10, len(df))):
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
            # Buscar sedes (códigos de habilitación)
            sedes_info = []
            current_sede = None
            current_servicios = []
            
            fila_inicio_servicios = None
            
            for idx, row in df.iterrows():
                row_str = ' '.join([str(cell).upper() for cell in row if pd.notna(cell)])
                
                # Detectar inicio de sede
                if 'CODIGO DE HABILITACIÓN' in row_str or 'CÓDIGO DE HABILITACIÓN' in row_str:
                    # Guardar sede anterior si existe
                    if current_sede and current_servicios:
                        sedes_info.append({
                            'sede': current_sede,
                            'servicios': current_servicios
                        })
                    
                    # Leer información de la sede (siguiente fila)
                    if idx + 1 < len(df):
                        sede_row = df.iloc[idx + 1]
                        
                        # Buscar código de habilitación y número de sede
                        codigo_hab = None
                        numero_sede = None
                        nombre_sede = None
                        municipio = None
                        
                        for i, val in enumerate(sede_row):
                            if pd.notna(val) and str(val).strip():
                                if i == 2:  # Columna C suele tener código
                                    codigo_hab = str(val).strip()
                                elif i == 3:  # Columna D suele tener número
                                    numero_sede = val
                                elif i == 4:  # Columna E suele tener nombre
                                    nombre_sede = str(val).strip()
                                elif i == 1:  # Columna B suele tener municipio
                                    municipio = str(val).strip()
                        
                        current_sede = {
                            'codigo_habilitacion': codigo_hab,
                            'numero_sede': numero_sede,
                            'nombre_sede': nombre_sede,
                            'municipio': municipio
                        }
                        current_servicios = []
                
                # Detectar fila de encabezados de servicios
                if any(keyword in row_str for keyword in ['CODIGO CUPS', 'CÓDIGO CUPS', 'CODIGO_CUPS']):
                    fila_inicio_servicios = idx + 1
                    continue
                
                # Extraer servicios
                if fila_inicio_servicios and idx >= fila_inicio_servicios and current_sede:
                    # Verificar si es una fila de servicio (tiene código CUPS)
                    if pd.notna(row.iloc[0]) and str(row.iloc[0]).strip():
                        codigo_cups = str(row.iloc[0]).strip()
                        
                        # Ignorar filas que no parecen servicios
                        if len(codigo_cups) > 2 and not codigo_cups.upper().startswith('TOTAL'):
                            servicio = {
                                'codigo_cups': codigo_cups,
                                'codigo_homologo': str(row.iloc[1]) if len(row) > 1 and pd.notna(row.iloc[1]) else '',
                                'descripcion': str(row.iloc[2]) if len(row) > 2 and pd.notna(row.iloc[2]) else '',
                                'tarifa_unitaria': row.iloc[3] if len(row) > 3 and pd.notna(row.iloc[3]) else 0,
                                'tarifario': str(row.iloc[4]) if len(row) > 4 and pd.notna(row.iloc[4]) else '',
                                'tarifa_segun_tarifario': str(row.iloc[5]) if len(row) > 5 and pd.notna(row.iloc[5]) else '',
                                'observaciones': str(row.iloc[6]) if len(row) > 6 and pd.notna(row.iloc[6]) else ''
                            }
                            current_servicios.append(servicio)
            
            # Guardar última sede
            if current_sede and current_servicios:
                sedes_info.append({
                    'sede': current_sede,
                    'servicios': current_servicios
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
            return {
                'success': False,
                'error': f'Error extrayendo servicios: {str(e)}'
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
        
        # Validar formato
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
                'error': extraccion['error'],
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