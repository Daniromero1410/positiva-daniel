/**
 * Módulo Consolidador T25 - JavaScript
 */

// Variables globales
let directorioActual = '/';
let archivoSeleccionado = null;

// ============================================
// FUNCIONES DE CONEXIÓN
// ============================================

async function conectar() {
    const password = document.getElementById('password-input').value;
    const connectBtn = document.getElementById('connect-btn');
    
    if (!password) {
        showNotification('Por favor ingresa la contraseña', 'warning');
        return;
    }
    
    // Deshabilitar botón
    connectBtn.disabled = true;
    connectBtn.innerHTML = '<i data-feather="loader" class="w-5 h-5 mr-2 animate-spin"></i>Conectando...';
    feather.replace();
    
    try {
        const response = await fetch('/modulos/consolidador-t25/conectar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ password })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('✅ ' + data.mensaje, 'success');
            directorioActual = data.directorio_actual;
            
            // Redirigir al explorador
            setTimeout(() => {
                window.location.href = '/modulos/consolidador-t25/explorador';
            }, 1000);
        } else {
            showNotification('❌ ' + data.error, 'error');
            connectBtn.disabled = false;
            connectBtn.innerHTML = '<i data-feather="log-in" class="w-5 h-5 mr-2"></i>Conectar al Servidor';
            feather.replace();
        }
        
    } catch (error) {
        showNotification('Error de conexión: ' + error.message, 'error');
        connectBtn.disabled = false;
        connectBtn.innerHTML = '<i data-feather="log-in" class="w-5 h-5 mr-2"></i>Conectar al Servidor';
        feather.replace();
    }
}

async function desconectar() {
    try {
        const response = await fetch('/modulos/consolidador-t25/desconectar', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Desconectado exitosamente', 'success');
            setTimeout(() => {
                window.location.href = '/modulos/consolidador-t25/';
            }, 500);
        }
    } catch (error) {
        console.error('Error al desconectar:', error);
        window.location.href = '/modulos/consolidador-t25/';
    }
}

function desconectarYVolver() {
    if (confirm('¿Deseas desconectar y volver al inicio?')) {
        desconectar();
    }
}

// ============================================
// FUNCIONES DEL EXPLORADOR
// ============================================

async function verificarConexion() {
    try {
        const response = await fetch('/modulos/consolidador-t25/estado');
        const data = await response.json();
        
        if (!data.conectado) {
            showNotification('Sesión expirada. Redirigiendo...', 'warning');
            setTimeout(() => {
                window.location.href = '/modulos/consolidador-t25/';
            }, 1500);
        }
    } catch (error) {
        console.error('Error al verificar conexión:', error);
    }
}

async function cargarDirectorioActual() {
    const loadingEl = document.getElementById('loading-files');
    const filesListEl = document.getElementById('files-list');
    const emptyStateEl = document.getElementById('empty-state');
    const totalItemsEl = document.getElementById('total-items');
    
    // Mostrar loading
    loadingEl.classList.remove('hidden');
    filesListEl.innerHTML = '';
    emptyStateEl.classList.add('hidden');
    
    try {
        const response = await fetch('/modulos/consolidador-t25/listar');
        const data = await response.json();
        
        loadingEl.classList.add('hidden');
        
        if (data.success) {
            directorioActual = data.directorio_actual;
            actualizarBreadcrumb(directorioActual);
            
            const items = data.items;
            totalItemsEl.textContent = `${items.length} elementos`;
            
            if (items.length === 0) {
                emptyStateEl.classList.remove('hidden');
            } else {
                items.forEach(item => {
                    const itemEl = crearElementoArchivo(item);
                    filesListEl.appendChild(itemEl);
                });
                feather.replace();
            }
        } else {
            showNotification('Error al listar directorio: ' + data.error, 'error');
        }
        
    } catch (error) {
        loadingEl.classList.add('hidden');
        showNotification('Error de conexión: ' + error.message, 'error');
    }
}

function crearElementoArchivo(item) {
    const div = document.createElement('div');
    div.className = 'flex items-center justify-between p-4 bg-white border border-neutral-200 rounded-xl hover:bg-neutral-50 transition-smooth';
    
    const icono = item.es_directorio ? 'folder' : 'file-text';
    const color = item.es_directorio ? 'text-yellow-600' : 'text-blue-600';
    const tamano = item.es_directorio ? '-' : formatBytes(item.tamano);
    
    div.innerHTML = `
        <div class="flex items-center space-x-4 flex-1 min-w-0">
            <div class="w-10 h-10 bg-neutral-100 rounded-lg flex items-center justify-center flex-shrink-0">
                <i data-feather="${icono}" class="w-5 h-5 ${color}"></i>
            </div>
            <div class="flex-1 min-w-0">
                <p class="text-sm font-semibold text-neutral-900 truncate">${item.nombre}</p>
                <p class="text-xs text-neutral-500">
                    ${tamano} • ${item.fecha_modificacion}
                </p>
            </div>
        </div>
        <div class="flex items-center space-x-2 ml-4">
            ${item.es_directorio ? 
                `<button onclick="abrirDirectorio('${item.nombre}')" class="px-3 py-2 bg-indigo-50 text-indigo-600 rounded-lg hover:bg-indigo-100 transition-smooth text-sm font-medium">
                    <i data-feather="folder-open" class="w-4 h-4 inline mr-1"></i>
                    Abrir
                </button>` :
                `<button onclick="descargarYProcesar('${item.nombre}')" class="px-3 py-2 bg-green-50 text-green-600 rounded-lg hover:bg-green-100 transition-smooth text-sm font-medium">
                    <i data-feather="download" class="w-4 h-4 inline mr-1"></i>
                    Procesar
                </button>`
            }
        </div>
    `;
    
    return div;
}

async function abrirDirectorio(nombreCarpeta) {
    try {
        const response = await fetch('/modulos/consolidador-t25/navegar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ path: nombreCarpeta })
        });
        
        const data = await response.json();
        
        if (data.success) {
            await cargarDirectorioActual();
        } else {
            showNotification('Error al cambiar directorio: ' + data.error, 'error');
        }
        
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    }
}

async function subirNivel() {
    await abrirDirectorio('..');
}

async function irRaiz() {
    try {
        const response = await fetch('/modulos/consolidador-t25/navegar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ path: '/' })
        });
        
        const data = await response.json();
        
        if (data.success) {
            await cargarDirectorioActual();
        } else {
            showNotification('Error: ' + data.error, 'error');
        }
        
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    }
}

function refrescarDirectorio() {
    cargarDirectorioActual();
}

function actualizarBreadcrumb(path) {
    const breadcrumbEl = document.getElementById('path-breadcrumb');
    breadcrumbEl.innerHTML = `
        <i data-feather="folder-open" class="w-4 h-4 text-neutral-400"></i>
        <span class="text-sm font-mono text-neutral-700">${path}</span>
    `;
    feather.replace();
}

// ============================================
// FUNCIONES DE PROCESAMIENTO
// ============================================

async function descargarYProcesar(nombreArchivo) {
    if (!confirm(`¿Deseas descargar y procesar el archivo "${nombreArchivo}"?`)) {
        return;
    }
    
    mostrarModalProcesamiento('Descargando desde GoAnywhere...', 20);
    
    try {
        // Paso 1: Descargar archivo
        const responseDescarga = await fetch('/modulos/consolidador-t25/descargar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ archivo: nombreArchivo })
        });
        
        const dataDescarga = await responseDescarga.json();
        
        if (!dataDescarga.success) {
            ocultarModalProcesamiento();
            showNotification('Error al descargar: ' + dataDescarga.error, 'error');
            return;
        }
        
        actualizarModalProcesamiento('Procesando archivo T25...', 50);
        
        // Paso 2: Procesar archivo
        const responseProcesar = await fetch('/modulos/consolidador-t25/procesar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ archivo: dataDescarga.nombre_archivo })
        });
        
        const dataProcesar = await responseProcesar.json();
        
        actualizarModalProcesamiento('Generando Excel consolidado...', 90);
        
        setTimeout(() => {
            ocultarModalProcesamiento();
            
            if (dataProcesar.success) {
                showNotification('✅ Archivo procesado exitosamente', 'success');
                
                // Redirigir a resultados
                setTimeout(() => {
                    window.location.href = '/modulos/consolidador-t25/resultados?' + new URLSearchParams({
                        archivo: dataProcesar.archivo_salida,
                        registros: dataProcesar.estadisticas.total_registros,
                        tiempo: dataProcesar.estadisticas.tiempo_ejecucion
                    });
                }, 1000);
            } else {
                showNotification('Error al procesar: ' + dataProcesar.error, 'error');
            }
        }, 500);
        
    } catch (error) {
        ocultarModalProcesamiento();
        showNotification('Error: ' + error.message, 'error');
    }
}

// ============================================
// FUNCIONES DE UI
// ============================================

function mostrarModalProcesamiento(mensaje, progreso) {
    const modal = document.getElementById('processing-modal');
    const mensajeEl = document.getElementById('processing-message');
    const progressBar = document.getElementById('processing-progress');
    const progressPercent = document.getElementById('processing-percent');
    
    mensajeEl.textContent = mensaje;
    progressBar.style.width = progreso + '%';
    progressPercent.textContent = progreso + '%';
    
    modal.classList.remove('hidden');
    feather.replace();
}

function actualizarModalProcesamiento(mensaje, progreso) {
    const mensajeEl = document.getElementById('processing-message');
    const progressBar = document.getElementById('processing-progress');
    const progressPercent = document.getElementById('processing-percent');
    
    mensajeEl.textContent = mensaje;
    progressBar.style.width = progreso + '%';
    progressPercent.textContent = progreso + '%';
}

function ocultarModalProcesamiento() {
    const modal = document.getElementById('processing-modal');
    modal.classList.add('hidden');
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Enter key para conectar
document.addEventListener('DOMContentLoaded', function() {
    const passwordInput = document.getElementById('password-input');
    if (passwordInput) {
        passwordInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                conectar();
            }
        });
    }
});