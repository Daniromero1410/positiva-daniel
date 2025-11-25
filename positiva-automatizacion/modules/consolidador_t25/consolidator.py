"""
Consolidador principal para procesar contratos de GoAnywhere
VERSION CORREGIDA con logs detallados
"""

import os
from typing import Dict, List, Optional
from datetime import datetime
from .goanywhere import GoAnywhereWebClient
from .anexo_processor import AnexoProcessor
from .maestra_manager import MaestraManager

class ConsolidadorT25:
    """Consolidador principal para procesar contratos T25"""
    
    def __init__(self, goanywhere_client: GoAnywhereWebClient):
        """
        Inicializa el consolidador
        
        Args:
            goanywhere_client: Cliente GoAnywhere conectado
        """
        self.client = goanywhere_client
        self.processor = AnexoProcessor()
        self.maestra = MaestraManager()
        self.alertas = []
        self.archivos_procesados = []
        self.temp_folder = 'temp/consolidador_t25'
        os.makedirs(self.temp_folder, exist_ok=True)
        
        # Logs detallados
        self.logs = []
    
    def log(self, mensaje: str, tipo: str = 'info'):
        """Agrega log con timestamp"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {mensaje}"
        self.logs.append({'timestamp': timestamp, 'mensaje': mensaje, 'tipo': tipo})
        print(log_entry, flush=True)
    
    def agregar_alerta(self, tipo: str, mensaje: str, contrato: str = None):
        """
        Agrega una alerta al registro
        
        Args:
            tipo: Tipo de alerta (warning, error, info)
            mensaje: Mensaje de la alerta
            contrato: Numero de contrato relacionado
        """
        self.alertas.append({
            'tipo': tipo,
            'mensaje': mensaje,
            'contrato': contrato,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        self.log(f"ALERTA [{tipo.upper()}]: {mensaje}", tipo)
    
    def procesar_contrato(self, info_contrato: Dict[str, any]) -> Dict[str, any]:
        """
        Procesa un contrato completo: inicial, otrosi y actas
        
        Args:
            info_contrato: Informacion del contrato de la maestra
            
        Returns:
            Dict con resultado del procesamiento
        """
        numero_contrato = info_contrato['numero_contrato']
        
        self.log("="*70)
        self.log(f"PROCESANDO CONTRATO: {numero_contrato}")
        self.log("="*70)
        
        resultado = {
            'numero_contrato': numero_contrato,
            'success': False,
            'anexos_descargados': [],
            'servicios_consolidados': [],
            'alertas': [],
            'logs': []
        }
        
        try:
            # 1. Buscar carpeta del contrato en GoAnywhere
            self.log(f"Buscando carpeta del contrato en GoAnywhere...")
            carpeta_contrato = self._buscar_carpeta_contrato(numero_contrato)
            
            if not carpeta_contrato:
                mensaje = f"Contrato no encontrado en GoAnywhere: {numero_contrato}"
                self.agregar_alerta('error', mensaje, numero_contrato)
                resultado['error'] = mensaje
                resultado['logs'] = self.logs
                return resultado
            
            self.log(f"Carpeta encontrada: {carpeta_contrato}")
            
            # 2. Navegar a carpeta TARIFAS
            self.log(f"Navegando a carpeta TARIFAS...")
            try:
                self.client.change_directory(f"/{carpeta_contrato}/TARIFAS")
                self.log(f"Acceso a carpeta TARIFAS exitoso")
            except Exception as e:
                mensaje = f"No se encontro carpeta TARIFAS en {numero_contrato}: {str(e)}"
                self.agregar_alerta('error', mensaje, numero_contrato)
                resultado['error'] = mensaje
                resultado['logs'] = self.logs
                return resultado
            
            # 3. Listar archivos en carpeta TARIFAS
            self.log("Listando archivos en TARIFAS...")
            listado = self.client.list_directory()
            
            if not listado['success']:
                mensaje = f"Error al listar archivos en TARIFAS: {listado['error']}"
                self.agregar_alerta('error', mensaje, numero_contrato)
                resultado['error'] = mensaje
                resultado['logs'] = self.logs
                return resultado
            
            archivos = [item['nombre'] for item in listado['items'] if not item['es_directorio']]
            self.log(f"Archivos encontrados en TARIFAS: {len(archivos)}")
            for archivo in archivos[:10]:
                self.log(f"  - {archivo}")
            
            # 4. Procesar ANEXO 1 inicial o de otrosi
            self.log("Buscando ANEXO 1 inicial o de otrosi...")
            anexo_inicial_otrosi = self._procesar_anexo_inicial_otrosi(
                archivos, 
                info_contrato,
                numero_contrato
            )
            
            if anexo_inicial_otrosi:
                resultado['anexos_descargados'].append(anexo_inicial_otrosi)
                self.log(f"Anexo procesado: {anexo_inicial_otrosi['tipo']} con {anexo_inicial_otrosi['total_servicios']} servicios")
            else:
                self.log("No se encontro ANEXO 1 inicial ni de otrosi", 'warning')
            
            # 5. Procesar ACTAS DE NEGOCIACION
            self.log("Buscando ACTAS DE NEGOCIACION...")
            actas = self._procesar_actas_negociacion(
                carpeta_contrato,
                info_contrato,
                numero_contrato,
                anexo_inicial_otrosi
            )
            
            if actas:
                resultado['anexos_descargados'].extend(actas)
                self.log(f"Actas procesadas: {len(actas)}")
            
            # 6. Consolidar todos los servicios
            if resultado['anexos_descargados']:
                self.log("Consolidando servicios de todos los anexos...")
                resultado['servicios_consolidados'] = self._consolidar_servicios(
                    resultado['anexos_descargados'],
                    info_contrato
                )
                resultado['success'] = True
                self.log(f"Consolidacion exitosa: {len(resultado['servicios_consolidados'])} servicios totales")
            else:
                mensaje = "No hay anexo 1 inicial de contrato ni otrosi"
                self.agregar_alerta('warning', mensaje, numero_contrato)
                resultado['error'] = mensaje
            
            resultado['alertas'] = [a for a in self.alertas if a['contrato'] == numero_contrato]
            resultado['logs'] = self.logs
            
            return resultado
            
        except Exception as e:
            import traceback
            error_msg = f"Error critico procesando contrato {numero_contrato}: {str(e)}"
            self.log(error_msg, 'error')
            self.log(traceback.format_exc(), 'error')
            resultado['error'] = error_msg
            resultado['logs'] = self.logs
            return resultado
    
    def _buscar_carpeta_contrato(self, numero_contrato: str) -> Optional[str]:
        """
        Busca la carpeta del contrato en GoAnywhere con busqueda recursiva
        
        Args:
            numero_contrato: Numero del contrato a buscar
            
        Returns:
            Ruta de la carpeta o None
        """
        try:
            # Ir a raiz
            self.client.change_directory('/')
            self.log("Navegando a raiz de GoAnywhere")
            
            # Obtener ano del contrato (ultimos 4 digitos)
            partes = numero_contrato.split('-')
            if len(partes) >= 2:
                anio = partes[-1]
                self.log(f"Ano del contrato detectado: {anio}")
            else:
                anio = None
            
            listado = self.client.list_directory()
            
            if not listado['success']:
                self.log(f"Error listando directorio raiz: {listado['error']}", 'error')
                return None
            
            # Buscar carpeta que contenga el numero de contrato
            contrato_upper = numero_contrato.upper()
            carpetas_candidatas = []
            
            for item in listado['items']:
                if item['es_directorio']:
                    nombre_upper = item['nombre'].upper()
                    
                    # Buscar coincidencia exacta o parcial
                    if contrato_upper in nombre_upper:
                        carpetas_candidatas.append(item['nombre'])
                        self.log(f"Carpeta candidata encontrada: {item['nombre']}")
            
            if not carpetas_candidatas:
                self.log(f"No se encontraron carpetas para el contrato {numero_contrato}", 'warning')
                return None
            
            # Si hay multiples candidatas, elegir la mas especifica
            if len(carpetas_candidatas) > 1:
                self.log(f"Multiples carpetas candidatas: {carpetas_candidatas}")
                # Priorizar la que tenga el ano correcto
                for carpeta in carpetas_candidatas:
                    if anio and anio in carpeta:
                        self.log(f"Carpeta seleccionada por ano: {carpeta}")
                        return carpeta
            
            return carpetas_candidatas[0]
            
        except Exception as e:
            self.log(f"Error buscando carpeta del contrato: {str(e)}", 'error')
            return None
    
    def _procesar_anexo_inicial_otrosi(
        self, 
        archivos: List[str], 
        info_contrato: Dict[str, any],
        numero_contrato: str
    ) -> Optional[Dict[str, any]]:
        """
        Procesa ANEXO 1 inicial o de otrosi segun prioridad
        REGLA: Si existe otrosi, tomar el de mayor numero
        
        Returns:
            Informacion del anexo procesado o None
        """
        try:
            # Filtrar archivos ANEXO 1
            self.log("Filtrando archivos ANEXO 1...")
            anexos = self.processor.filtrar_archivos_anexo1(archivos)
            
            self.log(f"Anexos encontrados: {len(anexos)}")
            for anexo in anexos:
                self.log(f"  - {anexo['nombre']} (extension: {anexo['extension']}, prioridad: {anexo['prioridad']})")
            
            if not anexos:
                self.log("No se encontraron archivos ANEXO 1", 'warning')
                return None
            
            # Filtrar archivos de otrosi
            self.log("Filtrando archivos de otrosi...")
            otrosi_archivos = self.processor.filtrar_archivos_otrosi(archivos)
            
            self.log(f"Otrosi encontrados: {len(otrosi_archivos)}")
            for otrosi in otrosi_archivos:
                self.log(f"  - {otrosi['nombre']} (numero: {otrosi['numero_otrosi']})")
            
            # REGLA: Si existe otrosi, tomar el de mayor numero
            if otrosi_archivos:
                otrosi_mayor = otrosi_archivos[0]
                self.log(f"Otrosi de mayor numero: {otrosi_mayor['numero_otrosi']}")
                
                # Buscar ANEXO 1 asociado al otrosi mayor
                anexo_otrosi = None
                for anexo in anexos:
                    if self.processor.es_otrosi(anexo['nombre']):
                        num_otrosi_anexo = self.processor.extraer_numero_otrosi(anexo['nombre'])
                        if num_otrosi_anexo == otrosi_mayor['numero_otrosi']:
                            anexo_otrosi = anexo
                            self.log(f"ANEXO 1 de otrosi {otrosi_mayor['numero_otrosi']} encontrado: {anexo['nombre']}")
                            break
                
                if anexo_otrosi:
                    anexo_info = self._descargar_y_procesar_anexo(
                        anexo_otrosi['nombre'],
                        'otrosi',
                        otrosi_mayor['numero_otrosi'],
                        info_contrato,
                        numero_contrato
                    )
                    
                    if anexo_info:
                        self.log(f"Anexo de Otrosi {otrosi_mayor['numero_otrosi']} descargado y procesado exitosamente")
                        return anexo_info
                    else:
                        self.log(f"Error procesando anexo de otrosi {otrosi_mayor['numero_otrosi']}", 'error')
                else:
                    self.log(f"No se encontro ANEXO 1 para otrosi {otrosi_mayor['numero_otrosi']}", 'warning')
            
            # Si no hay otrosi, buscar anexo inicial
            self.log("Buscando anexo inicial (sin otrosi)...")
            for anexo in anexos:
                if not anexo['es_otrosi']:
                    self.log(f"Anexo inicial encontrado: {anexo['nombre']}")
                    anexo_info = self._descargar_y_procesar_anexo(
                        anexo['nombre'],
                        'inicial',
                        None,
                        info_contrato,
                        numero_contrato
                    )
                    
                    if anexo_info:
                        self.log("Anexo inicial descargado y procesado exitosamente")
                        return anexo_info
                    else:
                        self.log("Error procesando anexo inicial", 'error')
            
            self.log("No se pudo procesar ningun anexo inicial ni de otrosi", 'warning')
            return None
            
        except Exception as e:
            self.log(f"Error en _procesar_anexo_inicial_otrosi: {str(e)}", 'error')
            import traceback
            self.log(traceback.format_exc(), 'error')
            return None
    
    def _procesar_actas_negociacion(
        self,
        carpeta_contrato: str,
        info_contrato: Dict[str, any],
        numero_contrato: str,
        anexo_inicial_otrosi: Optional[Dict[str, any]]
    ) -> List[Dict[str, any]]:
        """
        Procesa actas de negociacion si existen
        
        Returns:
            Lista de actas procesadas
        """
        actas_procesadas = []
        
        try:
            # Intentar navegar a ACTAS DE NEGOCIACION
            self.log("Buscando carpeta ACTAS DE NEGOCIACION...")
            try:
                self.client.change_directory(f"/{carpeta_contrato}/TARIFAS/ACTAS DE NEGOCIACION")
                self.log("Carpeta ACTAS DE NEGOCIACION encontrada")
            except:
                self.log("No existe carpeta ACTAS DE NEGOCIACION", 'info')
                return actas_procesadas
            
            # Listar archivos
            listado = self.client.list_directory()
            
            if not listado['success']:
                self.log(f"Error listando ACTAS DE NEGOCIACION: {listado['error']}", 'error')
                return actas_procesadas
            
            archivos = [item['nombre'] for item in listado['items'] if not item['es_directorio']]
            self.log(f"Archivos en ACTAS DE NEGOCIACION: {len(archivos)}")
            
            # Filtrar ANEXO 1 de actas
            anexos_actas = self.processor.filtrar_archivos_anexo1(archivos)
            
            self.log(f"Anexos de actas encontrados: {len(anexos_actas)}")
            for anexo in anexos_actas:
                self.log(f"  - {anexo['nombre']}")
            
            if not anexos_actas:
                mensaje = "Carpeta actas de negociacion sin ningun anexo 1 asociado"
                self.agregar_alerta('warning', mensaje, numero_contrato)
                return actas_procesadas
            
            # Procesar cada acta
            for anexo in anexos_actas:
                numero_acta = self.processor.extraer_numero_acta(anexo['nombre'])
                
                if numero_acta:
                    self.log(f"Procesando acta {numero_acta}...")
                    anexo_info = self._descargar_y_procesar_anexo(
                        anexo['nombre'],
                        'acta',
                        numero_acta,
                        info_contrato,
                        numero_contrato
                    )
                    
                    if anexo_info:
                        actas_procesadas.append(anexo_info)
                        self.log(f"Acta {numero_acta} descargada y procesada")
                    else:
                        self.log(f"Error procesando acta {numero_acta}", 'error')
                else:
                    self.log(f"No se pudo extraer numero de acta de: {anexo['nombre']}", 'warning')
            
            # Validar numeracion de actas
            self._validar_numeracion_actas(actas_procesadas, info_contrato, numero_contrato)
            
            return actas_procesadas
            
        except Exception as e:
            self.log(f"Error en _procesar_actas_negociacion: {str(e)}", 'error')
            import traceback
            self.log(traceback.format_exc(), 'error')
            return actas_procesadas
    
    def _descargar_y_procesar_anexo(
        self,
        nombre_archivo: str,
        tipo: str,
        numero: Optional[int],
        info_contrato: Dict[str, any],
        numero_contrato: str
    ) -> Optional[Dict[str, any]]:
        """
        Descarga y procesa un archivo ANEXO 1
        
        Args:
            nombre_archivo: Nombre del archivo
            tipo: 'inicial', 'otrosi' o 'acta'
            numero: Numero de otrosi o acta
            info_contrato: Info del contrato de la maestra
            numero_contrato: Numero del contrato
            
        Returns:
            Informacion del anexo procesado
        """
        try:
            # Generar nombre local
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            extension = os.path.splitext(nombre_archivo)[1]
            nombre_local = f"{numero_contrato}_{tipo}_{numero if numero else ''}_{timestamp}{extension}"
            ruta_local = os.path.join(self.temp_folder, nombre_local)
            
            self.log(f"Descargando archivo: {nombre_archivo}")
            self.log(f"Ruta local: {ruta_local}")
            
            # Descargar
            descarga = self.client.download_file(nombre_archivo, ruta_local)
            
            if not descarga['success']:
                mensaje = f"Error al descargar {nombre_archivo}: {descarga['error']}"
                self.agregar_alerta('error', mensaje, numero_contrato)
                self.log(mensaje, 'error')
                return None
            
            self.log(f"Archivo descargado exitosamente")
            
            # Procesar archivo
            self.log(f"Procesando archivo descargado...")
            procesamiento = self.processor.procesar_archivo_completo(ruta_local)
            
            if not procesamiento['success']:
                self.agregar_alerta('warning', procesamiento['error'], numero_contrato)
                self.log(procesamiento['error'], 'warning')
                return None
            
            self.log(f"Archivo procesado: {procesamiento['total_sedes']} sedes, {procesamiento['total_servicios']} servicios")
            
            # Obtener fecha segun tipo
            fecha_acuerdo = self._obtener_fecha_acuerdo(tipo, numero, info_contrato)
            self.log(f"Fecha acuerdo asignada: {fecha_acuerdo}")
            
            return {
                'nombre_archivo': nombre_archivo,
                'ruta_local': ruta_local,
                'tipo': tipo,
                'numero': numero,
                'fecha_acuerdo': fecha_acuerdo,
                'sedes_info': procesamiento['sedes_info'],
                'total_servicios': procesamiento['total_servicios']
            }
            
        except Exception as e:
            self.log(f"Error en _descargar_y_procesar_anexo: {str(e)}", 'error')
            import traceback
            self.log(traceback.format_exc(), 'error')
            return None
    
    def _obtener_fecha_acuerdo(
        self,
        tipo: str,
        numero: Optional[int],
        info_contrato: Dict[str, any]
    ) -> Optional[str]:
        """
        Obtiene la fecha del acuerdo segun tipo y numero
        
        Args:
            tipo: 'inicial', 'otrosi' o 'acta'
            numero: Numero de otrosi o acta
            info_contrato: Informacion del contrato
            
        Returns:
            Fecha en formato string o None
        """
        fecha = None
        
        if tipo == 'inicial':
            fecha = info_contrato.get('fecha_inicial')
            
        elif tipo == 'otrosi':
            otrosi_list = info_contrato.get('otrosi', [])
            for otrosi in otrosi_list:
                if otrosi.get('numero') == numero:
                    fecha = otrosi.get('fecha')
                    break
        
        elif tipo == 'acta':
            actas_list = info_contrato.get('actas', [])
            for acta in actas_list:
                if acta.get('numero') == numero:
                    fecha = acta.get('fecha')
                    break
        
        # Convertir fecha a string si es datetime
        if fecha and hasattr(fecha, 'strftime'):
            return fecha.strftime('%d/%m/%Y')
        elif fecha:
            return str(fecha)
        
        return None
    
    def _validar_numeracion_actas(
        self,
        actas_procesadas: List[Dict[str, any]],
        info_contrato: Dict[str, any],
        numero_contrato: str
    ):
        """
        Valida que no falten actas en la numeracion
        
        Args:
            actas_procesadas: Lista de actas procesadas
            info_contrato: Informacion del contrato
            numero_contrato: Numero del contrato
        """
        if not actas_procesadas:
            return
        
        # Obtener numeros de actas esperadas de la maestra
        actas_esperadas = set()
        for acta in info_contrato.get('actas', []):
            if acta.get('numero'):
                actas_esperadas.add(acta['numero'])
        
        # Obtener numeros de actas procesadas
        actas_procesadas_nums = set(acta['numero'] for acta in actas_procesadas if acta['numero'])
        
        # Encontrar faltantes
        actas_faltantes = actas_esperadas - actas_procesadas_nums
        
        for num_faltante in sorted(actas_faltantes):
            mensaje = f"No hay anexo 1 del acta {num_faltante} - Contrato {numero_contrato}"
            self.agregar_alerta('warning', mensaje, numero_contrato)
    
    def _consolidar_servicios(
        self,
        anexos: List[Dict[str, any]],
        info_contrato: Dict[str, any]
    ) -> List[Dict[str, any]]:
        """
        Consolida servicios de todos los anexos procesados
        
        Args:
            anexos: Lista de anexos descargados y procesados
            info_contrato: Informacion del contrato
            
        Returns:
            Lista de servicios consolidados
        """
        servicios_consolidados = []
        numero_contrato = info_contrato['numero_contrato']
        
        self.log(f"Consolidando servicios de {len(anexos)} anexos...")
        
        for anexo in anexos:
            # Determinar origen
            if anexo['tipo'] == 'inicial':
                origen = 'Inicial'
            elif anexo['tipo'] == 'otrosi':
                origen = f"Otrosi {anexo['numero']}"
            elif anexo['tipo'] == 'acta':
                origen = f"Acta {anexo['numero']}"
            else:
                origen = 'Desconocido'
            
            self.log(f"Procesando anexo: {origen} ({len(anexo['sedes_info'])} sedes)")
            
            # Procesar cada sede
            for sede_data in anexo['sedes_info']:
                sede = sede_data['sede']
                servicios = sede_data['servicios']
                
                # Generar codigo de habilitacion completo
                codigo_hab = self._generar_codigo_habilitacion_completo(sede)
                
                self.log(f"  Sede {codigo_hab}: {len(servicios)} servicios")
                
                # Agregar servicios
                for servicio in servicios:
                    servicios_consolidados.append({
                        'codigo_cups': servicio['codigo_cups'],
                        'codigo_homologo_manual': servicio['codigo_homologo'],
                        'descripcion_del_cups': servicio['descripcion'],
                        'tarifa_unitaria_en_pesos': servicio['tarifa_unitaria'],
                        'manual_tarifario': servicio['tarifario'],
                        'porcentaje_manual_tarifario': servicio['tarifa_segun_tarifario'],
                        'observaciones': servicio['observaciones'],
                        'codigo_de_habilitacion': codigo_hab,
                        'fecha_acuerdo': anexo['fecha_acuerdo'],
                        'numero_contrato_año': numero_contrato,
                        'origen_tarifa': origen
                    })
        
        self.log(f"Consolidacion completa: {len(servicios_consolidados)} servicios totales")
        return servicios_consolidados
    
    def _generar_codigo_habilitacion_completo(self, sede: Dict[str, any]) -> str:
        """
        Genera el codigo de habilitacion completo (codigo-sede)
        
        Args:
            sede: Informacion de la sede
            
        Returns:
            Codigo completo en formato string
        """
        codigo = sede.get('codigo_habilitacion', '')
        numero = sede.get('numero_sede', '')
        
        # Formatear numero de sede
        if isinstance(numero, float):
            if numero.is_integer():
                numero_str = str(int(numero))
            else:
                numero_str = str(numero)
        elif isinstance(numero, int):
            numero_str = str(numero)
        else:
            numero_str = str(numero) if numero else ""
        
        # Agregar ceros a la izquierda si es necesario
        if numero_str and len(numero_str) == 1:
            numero_str = numero_str.zfill(2)
        
        return f"{codigo}-{numero_str}"