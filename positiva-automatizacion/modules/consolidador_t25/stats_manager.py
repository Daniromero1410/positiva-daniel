"""
Gestor de estadísticas para el Consolidador T25
"""

import json
import os
from datetime import datetime


class StatsManager:
    """Gestiona las estadísticas del módulo Consolidador T25"""
    
    STATS_FILE = 'data/stats_consolidador_t25.json'
    
    def __init__(self):
        """Inicializa el gestor de estadísticas"""
        os.makedirs(os.path.dirname(self.STATS_FILE), exist_ok=True)
        self._init_stats_file()
    
    def _init_stats_file(self):
        """Inicializa el archivo de estadísticas si no existe"""
        if not os.path.exists(self.STATS_FILE):
            initial_data = {
                'procesos': [],
                'totales': {
                    'total_procesos': 0,
                    'total_registros': 0,
                    'procesos_exitosos': 0,
                    'procesos_fallidos': 0
                }
            }
            self._save_data(initial_data)
    
    def _load_data(self):
        """Carga los datos del archivo JSON"""
        try:
            with open(self.STATS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error cargando stats: {e}")
            return {
                'procesos': [],
                'totales': {
                    'total_procesos': 0,
                    'total_registros': 0,
                    'procesos_exitosos': 0,
                    'procesos_fallidos': 0
                }
            }
    
    def _save_data(self, data):
        """Guarda los datos en el archivo JSON"""
        try:
            with open(self.STATS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando stats: {e}")
    
    def registrar_proceso(self, tipo, usuario, archivo, registros, exitoso=True, alertas=None):
        """
        Registra un proceso ejecutado
        
        Args:
            tipo: Tipo de proceso (consolidador_t25_individual, consolidador_t25_masivo)
            usuario: Usuario que ejecutó el proceso
            archivo: Archivo o contrato procesado
            registros: Número de registros procesados
            exitoso: Si el proceso fue exitoso
            alertas: Lista de alertas generadas
        """
        data = self._load_data()
        
        proceso = {
            'id': len(data['procesos']) + 1,
            'tipo': tipo,
            'usuario': usuario,
            'archivo': archivo,
            'registros': registros,
            'exitoso': exitoso,
            'alertas': alertas or [],
            'fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        data['procesos'].append(proceso)
        data['totales']['total_procesos'] += 1
        data['totales']['total_registros'] += registros
        
        if exitoso:
            data['totales']['procesos_exitosos'] += 1
        else:
            data['totales']['procesos_fallidos'] += 1
        
        self._save_data(data)
        
        return proceso['id']
    
    def obtener_estadisticas(self, modulo=None):
        """
        Obtiene estadísticas del módulo
        
        Args:
            modulo: Nombre del módulo (opcional)
            
        Returns:
            Dict con estadísticas
        """
        data = self._load_data()
        totales = data['totales']
        
        total = totales['procesos_exitosos'] + totales['procesos_fallidos']
        tasa_exito = 0
        if total > 0:
            tasa_exito = round((totales['procesos_exitosos'] / total) * 100, 1)
        
        return {
            'total_procesos': totales['total_procesos'],
            'total_registros': totales['total_registros'],
            'tasa_exito': tasa_exito,
            'procesos_exitosos': totales['procesos_exitosos'],
            'procesos_fallidos': totales['procesos_fallidos']
        }
    
    def obtener_procesos_recientes(self, limit=10):
        """
        Obtiene los procesos más recientes
        
        Args:
            limit: Número máximo de procesos a retornar
            
        Returns:
            Lista de procesos recientes
        """
        data = self._load_data()
        return list(reversed(data['procesos'][-limit:]))