"""
Sistema de estadísticas y tracking de procesos
"""
import json
import os
from datetime import datetime
from pathlib import Path


class StatsManager:
    """Manejador de estadísticas del sistema"""
    
    def __init__(self, stats_file='data/stats.json'):
        self.stats_file = stats_file
        self._ensure_data_dir()
        self._init_stats_file()
    
    def _ensure_data_dir(self):
        """Asegura que exista el directorio de datos"""
        data_dir = os.path.dirname(self.stats_file)
        if data_dir and not os.path.exists(data_dir):
            os.makedirs(data_dir)
    
    def _init_stats_file(self):
        """Inicializa el archivo de estadísticas si no existe"""
        if not os.path.exists(self.stats_file):
            initial_data = {
                'procesos': [],
                'totales': {
                    'archivos_procesados': 0,
                    'registros_totales': 0,
                    'procesos_exitosos': 0,
                    'procesos_fallidos': 0
                }
            }
            self._save_data(initial_data)
    
    def _load_data(self):
        """Carga los datos del archivo JSON"""
        try:
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error cargando stats: {e}")
            return {
                'procesos': [],
                'totales': {
                    'archivos_procesados': 0,
                    'registros_totales': 0,
                    'procesos_exitosos': 0,
                    'procesos_fallidos': 0
                }
            }
    
    def _save_data(self, data):
        """Guarda los datos en el archivo JSON"""
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando stats: {e}")
    
    def registrar_proceso(self, modulo, archivo_nombre, total_registros, 
                         estudios_especificos=0, estudios_generales=0, 
                         exito=True, tiempo_ejecucion=0, archivo_salida=None):
        """Registra un nuevo proceso ejecutado"""
        data = self._load_data()
        
        proceso = {
            'id': len(data['procesos']) + 1,
            'modulo': modulo,
            'archivo': archivo_nombre,
            'archivo_salida': archivo_salida,  # NUEVO: guardar archivo de salida
            'fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_registros': total_registros,
            'estudios_especificos': estudios_especificos,
            'estudios_generales': estudios_generales,
            'exito': exito,
            'tiempo_ejecucion': round(tiempo_ejecucion, 2)
        }
        
        data['procesos'].append(proceso)
        data['totales']['archivos_procesados'] += 1
        data['totales']['registros_totales'] += total_registros
        
        if exito:
            data['totales']['procesos_exitosos'] += 1
        else:
            data['totales']['procesos_fallidos'] += 1
        
        self._save_data(data)
        
        return proceso['id']  # Retornar el ID del proceso
    
    def get_proceso_by_id(self, proceso_id):
        """Obtiene un proceso por su ID"""
        data = self._load_data()
        for proceso in data['procesos']:
            if proceso['id'] == proceso_id:
                return proceso
        return None
    
    def get_dashboard_stats(self):
        """Obtiene estadísticas para el dashboard"""
        data = self._load_data()
        totales = data['totales']
        
        total_procesos = totales['procesos_exitosos'] + totales['procesos_fallidos']
        tasa_exito = 0
        if total_procesos > 0:
            tasa_exito = round((totales['procesos_exitosos'] / total_procesos) * 100, 1)
        
        procesos_activos = 0
        ahora = datetime.now()
        for proceso in reversed(data['procesos'][-10:]):
            try:
                fecha_proceso = datetime.strptime(proceso['fecha'], '%Y-%m-%d %H:%M:%S')
                diff_minutos = (ahora - fecha_proceso).total_seconds() / 60
                if diff_minutos <= 5:
                    procesos_activos += 1
            except:
                pass
        
        return {
            'total_archivos': totales['archivos_procesados'],
            'procesos_activos': procesos_activos,
            'registros_totales': totales['registros_totales'],
            'tasa_exito': tasa_exito
        }
    
    def get_actividad_reciente(self, limit=5):
        """Obtiene la actividad reciente"""
        data = self._load_data()
        procesos_recientes = data['procesos'][-limit:]
        
        actividad = []
        ahora = datetime.now()
        
        for proceso in reversed(procesos_recientes):
            try:
                fecha_proceso = datetime.strptime(proceso['fecha'], '%Y-%m-%d %H:%M:%S')
                diff = ahora - fecha_proceso
                
                if diff.total_seconds() < 60:
                    tiempo_relativo = "Hace menos de 1 minuto"
                elif diff.total_seconds() < 3600:
                    minutos = int(diff.total_seconds() / 60)
                    tiempo_relativo = f"Hace {minutos} minuto{'s' if minutos != 1 else ''}"
                elif diff.total_seconds() < 86400:
                    horas = int(diff.total_seconds() / 3600)
                    tiempo_relativo = f"Hace {horas} hora{'s' if horas != 1 else ''}"
                else:
                    dias = int(diff.total_seconds() / 86400)
                    tiempo_relativo = f"Hace {dias} día{'s' if dias != 1 else ''}"
                
                actividad.append({
                    'id': proceso['id'],  # NUEVO: incluir ID
                    'archivo': proceso['archivo'],
                    'archivo_salida': proceso.get('archivo_salida'),  # NUEVO
                    'registros': proceso['total_registros'],
                    'tiempo_relativo': tiempo_relativo,
                    'exito': proceso['exito'],
                    'modulo': proceso['modulo']
                })
            except:
                pass
        
        return actividad


# Instancia global
stats_manager = StatsManager()