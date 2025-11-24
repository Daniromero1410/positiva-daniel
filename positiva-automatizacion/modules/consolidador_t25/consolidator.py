"""
Consolidador principal para procesar contratos de GoAnywhere
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
    
    def agregar_alerta(self, tipo: str, mensaje: str, contrato: str = None):
        """
        Agrega una alerta al registro
        
        Args:
            tipo: Tipo de alerta (warning, error, info)
            mensaje: Mensaje de la alerta
            contrato: Número de contrato relacionado
        """
        self.alertas.append({
            'tipo': tipo,
            'mensaje': mensaje,
            'contrato': contrato,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    def procesar_contrato(self, info_contrato: Dict[str, any]) -> Dict[str, any]:
        """
        Procesa un contrato completo: inicial, otrosí y actas
        
        Args:
            info_contrato: Información del contrato de la maestra
            
        Returns:
            Dict con resultado del procesamiento
        """
        numero_contrato = info_contrato['numero_contrato']
        
        print(f"\n{'='*70}")
        print(f"📄 PROCESANDO CONTRATO: {numero_contrato}")
        print(f"{'='*70}")
        
        resultado = {
            'numero_contrato': numero_contrato,
            'success': False,
            'anexos_descargados': [],
            'servicios_consolidados': [],
            'alertas': []
        }
        
        # 1. Buscar carpeta del contrato en GoAnywhere
        carpeta_contrato = self._buscar_carpeta_contrato(numero_contrato)
        
        if not carpeta_contrato:
            mensaje = f"Contrato no encontrado en GoAnywhere: {numero_contrato}"
            self.agregar_alerta('error', mensaje, numero_contrato)
            resultado['error'] = mensaje
            return resultado
        
        print(f"✅ Carpeta encontrada: {carpeta_contrato}")
        
        # 2. Navegar a carpeta TARIFAS
        try:
            self.client.change_directory(f"{carpeta_contrato}/TARIFAS")
            print(f"✅ Accediendo a carpeta TARIFAS")
        except:
            mensaje = f"No se encontró carpeta TARIFAS en {numero_contrato}"
            self.agregar_alerta('error', mensaje, numero_contrato)
            resultado['error'] = mensaje
            return resultado
        
        # 3. Listar archivos en carpeta TARIFAS
        listado = self.client.list_directory()
        
        if not listado['success']:
            mensaje = f"Error al listar archivos en TARIFAS: {listado['error']}"
            self.agregar_alerta('error', mensaje, numero_contrato)
            resultado['error'] = mensaje
            return resultado
        
        archivos = [item['nombre'] for item in listado['items'] if not item['es_directorio']]
        
        # 4. Procesar ANEXO 1 inicial o de otrosí
        anexo_inicial_otrosi = self._procesar_anexo_inicial_otrosi(
            archivos, 
            info_contrato,
            numero_contrato
        )
        
        if anexo_inicial_otrosi:
            resultado['anexos_descargados'].append(anexo_inicial_otrosi)
        
        # 5. Procesar ACTAS DE NEGOCIACIÓN
        actas = self._procesar_actas_negociacion(
            carpeta_contrato,
            info_contrato,
            numero_contrato,
            anexo_inicial_otrosi
        )
        
        if actas:
            resultado['anexos_descargados'].extend(actas)
        
        # 6. Consolidar todos los servicios
        if resultado['anexos_descargados']:
            resultado['servicios_consolidados'] = self._consolidar_servicios(
                resultado['anexos_descargados'],
                info_contrato
            )
            resultado['success'] = True
        else:
            mensaje = "No hay anexo 1 inicial de contrato ni otrosí"
            self.agregar_alerta('warning', mensaje, numero_contrato)
            resultado['error'] = mensaje
        
        resultado['alertas'] = [a for a in self.alertas if a['contrato'] == numero_contrato]
        
        return resultado
    
    def _buscar_carpeta_contrato(self, numero_contrato: str) -> Optional[str]:
        """
        Busca la carpeta del contrato en GoAnywhere
        
        Args:
            numero_contrato: Número del contrato a buscar
            
        Returns:
            Ruta de la carpeta o None
        """
        # Ir a raíz
        self.client.change_directory('/')
        
        listado = self.client.list_directory()
        
        if not listado['success']:
            return None
        
        # Buscar carpeta que contenga el número de contrato
        for item in listado['items']:
            if item['es_directorio']:
                nombre_upper = item['nombre'].upper()
                contrato_upper = numero_contrato.upper()
                
                if contrato_upper in nombre_upper:
                    return item['nombre']
        
        return None
    
    def _procesar_anexo_inicial_otrosi(
        self, 
        archivos: List[str], 
        info_contrato: Dict[str, any],
        numero_contrato: str
    ) -> Optional[Dict[str, any]]:
        """
        Procesa ANEXO 1 inicial o de otrosí según prioridad
        
        Returns:
            Información del anexo procesado o None
        """
        # Filtrar archivos ANEXO 1
        anexos = self.processor.filtrar_archivos_anexo1(archivos)
        
        if not anexos:
            return None
        
        # Filtrar archivos de otrosí
        otrosi_archivos = self.processor.filtrar_archivos_otrosi(archivos)
        
        # REGLA: Si existe otrosí, tomar el de mayor número
        if otrosi_archivos:
            otrosi_mayor = otrosi_archivos[0]  # Ya está ordenado (mayor primero)
            
            # Buscar ANEXO 1 asociado al otrosí mayor
            anexo_otrosi = None
            for anexo in anexos:
                if otrosi_mayor['numero_otrosi'] == self.processor.extraer_numero_otrosi(anexo['nombre']):
                    anexo_otrosi = anexo
                    break
            
            if anexo_otrosi:
                # Descargar anexo del otrosí
                anexo_info = self._descargar_y_procesar_anexo(
                    anexo_otrosi['nombre'],
                    'otrosi',
                    otrosi_mayor['numero_otrosi'],
                    info_contrato,
                    numero_contrato
                )
                
                if anexo_info:
                    print(f"✅ Anexo de Otrosí {otrosi_mayor['numero_otrosi']} descargado")
                    return anexo_info
        
        # Si no hay otrosí, buscar anexo inicial
        for anexo in anexos:
            if not anexo['es_otrosi']:
                anexo_info = self._descargar_y_procesar_anexo(
                    anexo['nombre'],
                    'inicial',
                    None,
                    info_contrato,
                    numero_contrato
                )
                
                if anexo_info:
                    print(f"✅ Anexo inicial descargado")
                    return anexo_info
        
        return None
    
    def _procesar_actas_negociacion(
        self,
        carpeta_contrato: str,
        info_contrato: Dict[str, any],
        numero_contrato: str,
        anexo_inicial_otrosi: Optional[Dict[str, any]]
    ) -> List[Dict[str, any]]:
        """
        Procesa actas de negociación si existen
        
        Returns:
            Lista de actas procesadas
        """
        actas_procesadas = []
        
        # Intentar navegar a ACTAS DE NEGOCIACIÓN
        try:
            self.client.change_directory(f"/{carpeta_contrato}/TARIFAS/ACTAS DE NEGOCIACIÓN")
        except:
            # No existe carpeta de actas
            return actas_procesadas
        
        print(f"📁 Carpeta ACTAS DE NEGOCIACIÓN encontrada")
        
        # Listar archivos
        listado = self.client.list_directory()
        
        if not listado['success']:
            return actas_procesadas
        
        archivos = [item['nombre'] for item in listado['items'] if not item['es_directorio']]
        
        # Filtrar ANEXO 1 de actas
        anexos_actas = self.processor.filtrar_archivos_anexo1(archivos)
        
        if not anexos_actas:
            mensaje = "Carpeta actas de negociación sin ningún anexo 1 asociado"
            self.agregar_alerta('warning', mensaje, numero_contrato)
            return actas_procesadas
        
        # Procesar cada acta
        for anexo in anexos_actas:
            numero_acta = self.processor.extraer_numero_acta(anexo['nombre'])
            
            if numero_acta:
                anexo_info = self._descargar_y_procesar_anexo(
                    anexo['nombre'],
                    'acta',
                    numero_acta,
                    info_contrato,
                    numero_contrato
                )
                
                if anexo_info:
                    actas_procesadas.append(anexo_info)
                    print(f"✅ Acta {numero_acta} descargada")
        
        # Validar numeración de actas
        self._validar_numeracion_actas(actas_procesadas, info_contrato, numero_contrato)
        
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
            numero: Número de otrosí o acta
            info_contrato: Info del contrato de la maestra
            numero_contrato: Número del contrato
            
        Returns:
            Información del anexo procesado
        """
        # Generar nombre local
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        extension = os.path.splitext(nombre_archivo)[1]
        nombre_local = f"{numero_contrato}_{tipo}_{numero if numero else ''}_{timestamp}{extension}"
        ruta_local = os.path.join(self.temp_folder, nombre_local)
        
        # Descargar
        descarga = self.client.download_file(nombre_archivo, ruta_local)
        
        if not descarga['success']:
            mensaje = f"Error al descargar {nombre_archivo}: {descarga['error']}"
            self.agregar_alerta('error', mensaje, numero_contrato)
            return None
        
        # Procesar archivo
        procesamiento = self.processor.procesar_archivo_completo(ruta_local)
        
        if not procesamiento['success']:
            self.agregar_alerta('warning', procesamiento['error'], numero_contrato)
            return None
        
        # Obtener fecha según tipo
        fecha_acuerdo = self._obtener_fecha_acuerdo(tipo, numero, info_contrato)
        
        return {
            'nombre_archivo': nombre_archivo,
            'ruta_local': ruta_local,
            'tipo': tipo,
            'numero': numero,
            'fecha_acuerdo': fecha_acuerdo,
            'sedes_info': procesamiento['sedes_info'],
            'total_servicios': procesamiento['total_servicios']
        }
    
    def _obtener_fecha_acuerdo(
        self,
        tipo: str,
        numero: Optional[int],
        info_contrato: Dict[str, any]
    ) -> Optional[str]:
        """
        Obtiene la fecha del acuerdo según tipo y número
        
        Args:
            tipo: 'inicial', 'otrosi' o 'acta'
            numero: Número de otrosí o acta
            info_contrato: Información del contrato
            
        Returns:
            Fecha en formato string o None
        """
        if tipo == 'inicial':
            fecha = info_contrato.get('fecha_inicial')
            
        elif tipo == 'otrosi':
            otrosi_list = info_contrato.get('otrosi', [])
            for otrosi in otrosi_list:
                if otrosi['numero'] == numero:
                    fecha = otrosi['fecha']
                    break
            else:
                fecha = None
        
        elif tipo == 'acta':
            actas_list = info_contrato.get('actas', [])
            for acta in actas_list:
                if acta['numero'] == numero:
                    fecha = acta['fecha']
                    break
            else:
                fecha = None
        else:
            fecha = None
        
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
        Valida que no falten actas en la numeración
        
        Args:
            actas_procesadas: Lista de actas procesadas
            info_contrato: Información del contrato
            numero_contrato: Número del contrato
        """
        if not actas_procesadas:
            return
        
        # Obtener números de actas esperadas de la maestra
        actas_esperadas = set()
        for acta in info_contrato.get('actas', []):
            if acta.get('numero'):
                actas_esperadas.add(acta['numero'])
        
        # Obtener números de actas procesadas
        actas_procesadas_nums = set(acta['numero'] for acta in actas_procesadas if acta['numero'])
        
        # Encontrar faltantes
        actas_faltantes = actas_esperadas - actas_procesadas_nums
        
        for num_faltante in sorted(actas_faltantes):
            mensaje = f"No hay anexo 1 del acta {num_faltante} – Contrato {numero_contrato}"
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
            info_contrato: Información del contrato
            
        Returns:
            Lista de servicios consolidados
        """
        servicios_consolidados = []
        numero_contrato = info_contrato['numero_contrato']
        
        for anexo in anexos:
            # Determinar origen
            if anexo['tipo'] == 'inicial':
                origen = 'Inicial'
            elif anexo['tipo'] == 'otrosi':
                origen = f"Otrosí {anexo['numero']}"
            elif anexo['tipo'] == 'acta':
                origen = f"Acta {anexo['numero']}"
            else:
                origen = 'Desconocido'
            
            # Procesar cada sede
            for sede_data in anexo['sedes_info']:
                sede = sede_data['sede']
                servicios = sede_data['servicios']
                
                # Generar código de habilitación completo
                codigo_hab = self._generar_codigo_habilitacion_completo(sede)
                
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
        
        return servicios_consolidados
    
    def _generar_codigo_habilitacion_completo(self, sede: Dict[str, any]) -> str:
        """
        Genera el código de habilitación completo (codigo-sede)
        
        Args:
            sede: Información de la sede
            
        Returns:
            Código completo en formato string
        """
        codigo = sede.get('codigo_habilitacion', '')
        numero = sede.get('numero_sede', '')
        
        # Formatear número de sede
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