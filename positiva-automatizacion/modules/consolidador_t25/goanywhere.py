"""
Cliente para conectarse al servidor GoAnywhere SFTP
"""

import paramiko
from datetime import datetime
from typing import Dict, List, Optional
import stat
import os

class GoAnywhereWebClient:
    """Cliente SFTP para GoAnywhere"""
    
    # Credenciales por defecto
    DEFAULT_HOST = 'mft.positiva.gov.co'
    DEFAULT_PORT = 2243
    DEFAULT_USERNAME = 'G_medica'
    DEFAULT_PASSWORD = ''
    
    def __init__(self, host: str = None, port: int = None, username: str = None):
        """
        Inicializa el cliente GoAnywhere
        
        Args:
            host: Servidor SFTP (por defecto DEFAULT_HOST)
            port: Puerto SFTP (por defecto DEFAULT_PORT)
            username: Usuario SFTP (por defecto DEFAULT_USERNAME)
        """
        self.host = host or self.DEFAULT_HOST
        self.port = port or self.DEFAULT_PORT
        self.username = username or self.DEFAULT_USERNAME
        
        self.ssh_client = None
        self.sftp = None
        self.is_connected = False
        self.current_directory = '/'
    
    def connect(self, password: str = None) -> Dict[str, any]:
        """
        Conecta al servidor SFTP
        
        Args:
            password: Contraseña (por defecto usa DEFAULT_PASSWORD)
            
        Returns:
            Dict con success (bool) y mensaje/error
        """
        try:
            # Usar contraseña por defecto si no se proporciona
            pwd = password or self.DEFAULT_PASSWORD
            
            # Crear cliente SSH
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Conectar
            self.ssh_client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=pwd,
                timeout=30
            )
            
            # Abrir canal SFTP
            self.sftp = self.ssh_client.open_sftp()
            self.is_connected = True
            
            # Obtener directorio actual
            self.current_directory = self.sftp.getcwd() or '/'
            
            return {
                'success': True,
                'mensaje': 'Conexión exitosa',
                'directorio_actual': self.current_directory
            }
            
        except paramiko.AuthenticationException:
            return {
                'success': False,
                'error': 'Error de autenticación. Verifica las credenciales.'
            }
        except paramiko.SSHException as e:
            return {
                'success': False,
                'error': f'Error SSH: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error de conexión: {str(e)}'
            }
    
    def disconnect(self):
        """Cierra la conexión SFTP"""
        try:
            if self.sftp:
                self.sftp.close()
            if self.ssh_client:
                self.ssh_client.close()
            self.is_connected = False
            self.current_directory = '/'
        except Exception as e:
            print(f"Error al desconectar: {e}")
    
    def list_directory(self, path: str = '.') -> Dict[str, any]:
        """
        Lista el contenido de un directorio
        
        Args:
            path: Ruta del directorio (por defecto el actual)
            
        Returns:
            Dict con success, items (lista de archivos/carpetas) y directorio_actual
        """
        if not self.is_connected or not self.sftp:
            return {
                'success': False,
                'error': 'No hay conexión SFTP activa'
            }
        
        try:
            # Obtener lista de archivos con atributos
            items = []
            for attr in self.sftp.listdir_attr(path):
                item_info = {
                    'nombre': attr.filename,
                    'es_directorio': self._is_directory(attr),
                    'tamano': attr.st_size,
                    'fecha_modificacion': datetime.fromtimestamp(attr.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    'permisos': oct(attr.st_mode)[-3:]
                }
                items.append(item_info)
            
            # Ordenar: directorios primero, luego archivos
            items.sort(key=lambda x: (not x['es_directorio'], x['nombre'].lower()))
            
            return {
                'success': True,
                'items': items,
                'directorio_actual': self.sftp.getcwd() or '/'
            }
            
        except FileNotFoundError:
            return {
                'success': False,
                'error': 'Directorio no encontrado'
            }
        except PermissionError:
            return {
                'success': False,
                'error': 'Sin permisos para acceder al directorio'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error al listar directorio: {str(e)}'
            }
    
    def change_directory(self, path: str) -> Dict[str, any]:
        """
        Cambia el directorio actual
        
        Args:
            path: Ruta del nuevo directorio
            
        Returns:
            Dict con success, directorio_actual
        """
        if not self.is_connected or not self.sftp:
            return {
                'success': False,
                'error': 'No hay conexión SFTP activa'
            }
        
        try:
            self.sftp.chdir(path)
            self.current_directory = self.sftp.getcwd() or '/'
            
            return {
                'success': True,
                'directorio_actual': self.current_directory
            }
            
        except FileNotFoundError:
            return {
                'success': False,
                'error': 'Directorio no encontrado'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error al cambiar directorio: {str(e)}'
            }
    
    def download_file(self, remote_path: str, local_path: str) -> Dict[str, any]:
        """
        Descarga un archivo del servidor SFTP
        
        Args:
            remote_path: Ruta del archivo en el servidor
            local_path: Ruta local donde guardar el archivo
            
        Returns:
            Dict con success y ruta local del archivo
        """
        if not self.is_connected or not self.sftp:
            return {
                'success': False,
                'error': 'No hay conexión SFTP activa'
            }
        
        try:
            self.sftp.get(remote_path, local_path)
            
            return {
                'success': True,
                'mensaje': 'Archivo descargado exitosamente',
                'ruta_local': local_path
            }
            
        except FileNotFoundError:
            return {
                'success': False,
                'error': 'Archivo no encontrado en el servidor'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error al descargar archivo: {str(e)}'
            }
    
    def get_connection_status(self) -> Dict[str, any]:
        """
        Obtiene el estado de la conexión
        
        Returns:
            Dict con conectado (bool) y directorio_actual
        """
        return {
            'conectado': self.is_connected,
            'directorio_actual': self.current_directory if self.is_connected else None
        }
    
    def get_current_directory(self) -> Optional[str]:
        """
        Obtiene el directorio actual
        
        Returns:
            String con la ruta del directorio actual o None si no está conectado
        """
        if self.is_connected and self.sftp:
            return self.sftp.getcwd() or '/'
        return None
    
    def search_files(self, query: str, search_path: str = '.', max_results: int = 100, max_time: int = 30) -> Dict[str, any]:
        """
        Busca archivos recursivamente en el servidor con timeout
        
        Args:
            query: Término de búsqueda
            search_path: Ruta donde iniciar la búsqueda
            max_results: Máximo número de resultados
            max_time: Tiempo máximo de búsqueda en segundos
            
        Returns:
            Dict con success, resultados (lista) y total
        """
        if not self.is_connected or not self.sftp:
            return {
                'success': False,
                'error': 'No hay conexión SFTP activa'
            }
        
        try:
            import time
            resultados = []
            query_lower = query.lower()
            start_time = time.time()
            carpetas_visitadas = 0
            max_carpetas = 200  # Límite de carpetas para evitar bloqueos
            
            def buscar_recursivo(path, depth=0, max_depth=4):
                nonlocal carpetas_visitadas
                
                # Verificar timeout
                if time.time() - start_time > max_time:
                    return True  # Timeout alcanzado
                
                if depth > max_depth or len(resultados) >= max_results or carpetas_visitadas >= max_carpetas:
                    return False
                
                try:
                    carpetas_visitadas += 1
                    
                    for attr in self.sftp.listdir_attr(path):
                        # Verificar timeout en cada iteración
                        if time.time() - start_time > max_time:
                            return True
                        
                        if len(resultados) >= max_results:
                            break
                        
                        nombre = attr.filename
                        
                        # Ignorar archivos/carpetas ocultas
                        if nombre.startswith('.'):
                            continue
                        
                        ruta_completa = f"{path}/{nombre}".replace('//', '/')
                        
                        # Si es directorio, buscar recursivamente
                        if self._is_directory(attr):
                            # También buscar en nombres de carpetas
                            if query_lower in nombre.lower():
                                resultados.append({
                                    'nombre': nombre,
                                    'ruta': ruta_completa,
                                    'tipo': 'directorio',
                                    'extension': '',
                                    'tamano': 0,
                                    'fecha_modificacion': datetime.fromtimestamp(attr.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                                    'es_directorio': True
                                })
                            
                            # Buscar dentro del directorio
                            timeout_reached = buscar_recursivo(ruta_completa, depth + 1, max_depth)
                            if timeout_reached:
                                return True
                        else:
                            # Buscar en nombres de archivos
                            if query_lower in nombre.lower():
                                # Obtener extensión
                                extension = os.path.splitext(nombre)[1].lower()
                                
                                resultados.append({
                                    'nombre': nombre,
                                    'ruta': ruta_completa,
                                    'tipo': 'archivo',
                                    'extension': extension,
                                    'tamano': attr.st_size,
                                    'fecha_modificacion': datetime.fromtimestamp(attr.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                                    'es_directorio': False
                                })
                except PermissionError:
                    # Ignorar errores de permisos
                    pass
                except Exception as e:
                    # Ignorar otros errores y continuar
                    pass
                
                return False
            
            # Iniciar búsqueda recursiva
            timeout_reached = buscar_recursivo(search_path)
            
            return {
                'success': True,
                'resultados': resultados,
                'total': len(resultados),
                'query': query,
                'timeout': timeout_reached,
                'carpetas_visitadas': carpetas_visitadas
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error al buscar: {str(e)}'
            }
    
    def get_suggestions(self, partial_query: str, current_path: str = '.', limit: int = 10) -> Dict[str, any]:
        """
        Obtiene sugerencias de autocompletado basadas en el directorio actual
        
        Args:
            partial_query: Texto parcial ingresado
            current_path: Directorio actual
            limit: Número máximo de sugerencias
            
        Returns:
            Dict con success y lista de sugerencias
        """
        if not self.is_connected or not self.sftp:
            return {
                'success': False,
                'error': 'No hay conexión SFTP activa'
            }
        
        try:
            sugerencias = []
            query_lower = partial_query.lower()
            
            # Buscar en directorio actual
            for attr in self.sftp.listdir_attr(current_path):
                if len(sugerencias) >= limit:
                    break
                
                nombre = attr.filename
                if query_lower in nombre.lower():
                    sugerencias.append({
                        'nombre': nombre,
                        'es_directorio': self._is_directory(attr),
                        'ruta': f"{current_path}/{nombre}".replace('//', '/')
                    })
            
            return {
                'success': True,
                'sugerencias': sugerencias
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error al obtener sugerencias: {str(e)}'
            }
    
    def _is_directory(self, attr) -> bool:
        """
        Verifica si un atributo representa un directorio
        
        Args:
            attr: Atributo de paramiko
            
        Returns:
            True si es directorio, False si no
        """
        return stat.S_ISDIR(attr.st_mode)
    
    def __del__(self):
        """Destructor: cierra la conexión al eliminar el objeto"""
        self.disconnect()
