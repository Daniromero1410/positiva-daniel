/**
 * GoAnywhere Explorer para Dashboard - MEJORADO CON COLORES Y SIN BLOQUEO
 */

let directorioActual = '/';
let isConnected = false;
let historialRutas = ['/'];
let searchTimeout = null;
let isSearching = false;
let searchAbortController = null;

// Mapa de colores por extensión
const EXTENSION_COLORS = {
    // PDF - Rojo
    '.pdf': { bg: 'bg-red-100', text: 'text-red-600', icon: 'file-text' },
    
    // Excel - Verde
    '.xlsx': { bg: 'bg-green-100', text: 'text-green-600', icon: 'file-text' },
    '.xls': { bg: 'bg-green-100', text: 'text-green-600', icon: 'file-text' },
    '.xlsm': { bg: 'bg-green-100', text: 'text-green-600', icon: 'file-text' },
    '.xlsb': { bg: 'bg-green-100', text: 'text-green-600', icon: 'file-text' },
    '.csv': { bg: 'bg-green-100', text: 'text-green-600', icon: 'file-text' },
    
    // Word - Azul
    '.docx': { bg: 'bg-blue-100', text: 'text-blue-600', icon: 'file-text' },
    '.doc': { bg: 'bg-blue-100', text: 'text-blue-600', icon: 'file-text' },
    
    // PowerPoint - Naranja
    '.pptx': { bg: 'bg-orange-100', text: 'text-orange-600', icon: 'file-text' },
    '.ppt': { bg: 'bg-orange-100', text: 'text-orange-600', icon: 'file-text' },
    
    // Imágenes - Morado
    '.jpg': { bg: 'bg-purple-100', text: 'text-purple-600', icon: 'image' },
    '.jpeg': { bg: 'bg-purple-100', text: 'text-purple-600', icon: 'image' },
    '.png': { bg: 'bg-purple-100', text: 'text-purple-600', icon: 'image' },
    '.gif': { bg: 'bg-purple-100', text: 'text-purple-600', icon: 'image' },
    '.bmp': { bg: 'bg-purple-100', text: 'text-purple-600', icon: 'image' },
    
    // Comprimidos - Gris oscuro
    '.zip': { bg: 'bg-gray-200', text: 'text-gray-700', icon: 'archive' },
    '.rar': { bg: 'bg-gray-200', text: 'text-gray-700', icon: 'archive' },
    '.7z': { bg: 'bg-gray-200', text: 'text-gray-700', icon: 'archive' },
    '.tar': { bg: 'bg-gray-200', text: 'text-gray-700', icon: 'archive' },
    '.gz': { bg: 'bg-gray-200', text: 'text-gray-700', icon: 'archive' },
    
    // Texto - Cyan
    '.txt': { bg: 'bg-cyan-100', text: 'text-cyan-600', icon: 'file-text' },
    '.log': { bg: 'bg-cyan-100', text: 'text-cyan-600', icon: 'file-text' },
    '.md': { bg: 'bg-cyan-100', text: 'text-cyan-600', icon: 'file-text' },
    
    // Default - Azul claro
    'default': { bg: 'bg-blue-100', text: 'text-blue-600', icon: 'file-text' }
};

function getFileStyle(extension, isDirectory) {
    if (isDirectory) {
        return { bg: 'bg-yellow-100', text: 'text-yellow-600', icon: 'folder' };
    }
    
    const ext = extension.toLowerCase();
    return EXTENSION_COLORS[ext] || EXTENSION_COLORS['default'];
}

// Conectar automáticamente al cargar la página
document.addEventListener('DOMContentLoaded', function() {
    verificarEstadoConexion();
    configurarBuscador();
});

function configurarBuscador() {
    const searchInput = document.getElementById('search-input');
    
    if (searchInput) {
        // Buscar al presionar Enter
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                ejecutarBusqueda();
            }
        });
        
        // Autocompletado mientras escribe
        searchInput.addEventListener('input', function(e) {
            const query = e.target.value.trim();
            
            // Limpiar timeout anterior
            if (searchTimeout) {
                clearTimeout(searchTimeout);
            }
            
            // Mostrar/ocultar botón de limpiar
            const clearBtn = document.getElementById('clear-search-btn');
            if (query.length > 0) {
                clearBtn.classList.remove('hidden');
            } else {
                clearBtn.classList.add('hidden');
                ocultarSugerencias();
            }
            
            // Obtener sugerencias después de 300ms
            if (query.length >= 2) {
                searchTimeout = setTimeout(() => {
                    obtenerSugerencias(query);
                }, 300);
            } else {
                ocultarSugerencias();
            }
        });
        
        // Ocultar sugerencias al hacer clic fuera
        document.addEventListener('click', function(e) {
            const suggestionsContainer = document.getElementById('suggestions-container');
            if (searchInput && suggestionsContainer && 
                !searchInput.contains(e.target) && 
                !suggestionsContainer.contains(e.target)) {
                ocultarSugerencias();
            }
        });
    }
}

async function verificarEstadoConexion() {
    try {
        const response = await fetch('/modulos/consolidador-t25/estado');
        const data = await response.json();
        
        if (data.conectado) {
            isConnected = true;
            actualizarUIConectado();
            cargarDirectorioActual();
        }
    } catch (error) {
        console.log('No hay conexión activa');
    }
}

async function conectarGoAnywhere() {
    const connectBtn = document.getElementById('connect-btn');
    const statusDot = document.getElementById('status-dot');
    const statusLabel = document.getElementById('status-label');
    
    connectBtn.disabled = true;
    connectBtn.innerHTML = '<i data-feather="loader" class="w-4 h-4 inline mr-1 animate-spin"></i>Conectando...';
    feather.replace();
    
    statusLabel.textContent = 'Conectando...';
    statusDot.className = 'w-2 h-2 bg-yellow-400 rounded-full animate-pulse';
    
    try {
        const response = await fetch('/modulos/consolidador-t25/conectar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            isConnected = true;
            directorioActual = data.directorio_actual;
            historialRutas = [directorioActual];
            
            showNotification('✅ Conectado a GoAnywhere exitosamente', 'success');
            
            actualizarUIConectado();
            await cargarDirectorioActual();
        } else {
            showNotification('❌ Error al conectar: ' + data.error, 'error');
            
            connectBtn.disabled = false;
            connectBtn.innerHTML = '<i data-feather="wifi" class="w-4 h-4 inline mr-1"></i>Conectar';
            statusLabel.textContent = 'Error de conexión';
            statusDot.className = 'w-2 h-2 bg-red-400 rounded-full';
            feather.replace();
        }
        
    } catch (error) {
        showNotification('Error de conexión: ' + error.message, 'error');
        
        connectBtn.disabled = false;
        connectBtn.innerHTML = '<i data-feather="wifi" class="w-4 h-4 inline mr-1"></i>Conectar';
        statusLabel.textContent = 'Error';
        statusDot.className = 'w-2 h-2 bg-red-400 rounded-full';
        feather.replace();
    }
}

function actualizarUIConectado() {
    const statusDot = document.getElementById('status-dot');
    const statusLabel = document.getElementById('status-label');
    const connectBtn = document.getElementById('connect-btn');
    
    statusLabel.textContent = 'Conectado';
    statusDot.className = 'w-2 h-2 bg-green-400 rounded-full';
    
    connectBtn.innerHTML = '<i data-feather="wifi-off" class="w-4 h-4 inline mr-1"></i>Desconectar';
    connectBtn.onclick = desconectarGoAnywhere;
    connectBtn.disabled = false;
    connectBtn.className = 'px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-smooth text-sm font-medium';
    
    feather.replace();
    
    document.getElementById('not-connected-state').classList.add('hidden');
    document.getElementById('path-breadcrumb').classList.remove('hidden');
    document.getElementById('search-container').classList.remove('hidden');
}

async function desconectarGoAnywhere() {
    try {
        await fetch('/modulos/consolidador-t25/desconectar', {
            method: 'POST'
        });
        
        isConnected = false;
        historialRutas = ['/'];
        
        showNotification('Desconectado de GoAnywhere', 'info');
        
        // Resetear UI
        const statusDot = document.getElementById('status-dot');
        const statusLabel = document.getElementById('status-label');
        const connectBtn = document.getElementById('connect-btn');
        
        statusLabel.textContent = 'Desconectado';
        statusDot.className = 'w-2 h-2 bg-gray-400 rounded-full';
        
        connectBtn.innerHTML = '<i data-feather="wifi" class="w-4 h-4 inline mr-1"></i>Conectar';
        connectBtn.onclick = conectarGoAnywhere;
        connectBtn.className = 'px-4 py-2 bg-indigo-500 text-white rounded-lg hover:bg-indigo-600 transition-smooth text-sm font-medium';
        
        document.getElementById('not-connected-state').classList.remove('hidden');
        document.getElementById('path-breadcrumb').classList.add('hidden');
        document.getElementById('search-container').classList.add('hidden');
        document.getElementById('files-list').classList.add('hidden');
        document.getElementById('empty-state').classList.add('hidden');
        document.getElementById('search-results').classList.add('hidden');
        
        feather.replace();
        
    } catch (error) {
        console.error('Error al desconectar:', error);
    }
}

async function cargarDirectorioActual() {
    const loadingEl = document.getElementById('loading-files');
    const filesListEl = document.getElementById('files-list');
    const emptyStateEl = document.getElementById('empty-state');
    
    loadingEl.classList.remove('hidden');
    filesListEl.classList.add('hidden');
    emptyStateEl.classList.add('hidden');
    filesListEl.innerHTML = '';
    
    try {
        const response = await fetch('/modulos/consolidador-t25/listar');
        const data = await response.json();
        
        loadingEl.classList.add('hidden');
        
        if (data.success) {
            directorioActual = data.directorio_actual;
            actualizarBreadcrumb(directorioActual);
            
            const items = data.items;
            
            if (items.length === 0) {
                emptyStateEl.classList.remove('hidden');
            } else {
                filesListEl.classList.remove('hidden');
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
    
    // Obtener extensión y estilo
    const extension = item.nombre.includes('.') ? '.' + item.nombre.split('.').pop().toLowerCase() : '';
    const style = getFileStyle(extension, item.es_directorio);
    
    // Hacer todo el elemento clickeable
    if (item.es_directorio) {
        div.onclick = () => abrirDirectorio(item.nombre);
        div.className = 'flex items-center justify-between p-4 bg-white border border-neutral-200 rounded-xl hover:bg-indigo-50 hover:border-indigo-300 transition-smooth cursor-pointer';
    } else {
        div.onclick = () => descargarArchivo(item.nombre);
        div.className = 'flex items-center justify-between p-4 bg-white border border-neutral-200 rounded-xl hover:bg-green-50 hover:border-green-300 transition-smooth cursor-pointer';
    }
    
    const tamano = item.es_directorio ? '-' : formatBytes(item.tamano);
    
    div.innerHTML = `
        <div class="flex items-center space-x-4 flex-1 min-w-0">
            <div class="w-10 h-10 ${style.bg} rounded-lg flex items-center justify-center flex-shrink-0">
                <i data-feather="${style.icon}" class="w-5 h-5 ${style.text}"></i>
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
                `<div class="px-3 py-2 bg-indigo-100 text-indigo-700 rounded-lg text-sm font-medium">
                    <i data-feather="chevron-right" class="w-4 h-4 inline"></i>
                </div>` :
                `<div class="px-3 py-2 bg-green-100 text-green-700 rounded-lg text-sm font-medium">
                    <i data-feather="download" class="w-4 h-4 inline"></i>
                </div>`
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

async function navegarARuta(rutaCompleta) {
    try {
        const response = await fetch('/modulos/consolidador-t25/navegar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ path: rutaCompleta })
        });
        
        const data = await response.json();
        
        if (data.success) {
            await cargarDirectorioActual();
        } else {
            showNotification('Error al navegar: ' + data.error, 'error');
        }
        
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    }
}

async function irRaiz() {
    await navegarARuta('/');
}

function refrescarDirectorio() {
    cargarDirectorioActual();
}

function actualizarBreadcrumb(path) {
    const breadcrumbContainer = document.getElementById('breadcrumb-items');
    breadcrumbContainer.innerHTML = '';
    
    // Dividir la ruta en partes
    const partes = path.split('/').filter(p => p !== '');
    
    // Agregar raíz
    const raizBtn = document.createElement('button');
    raizBtn.onclick = () => navegarARuta('/');
    raizBtn.className = 'inline-flex items-center px-3 py-1.5 bg-white hover:bg-indigo-50 border border-neutral-200 hover:border-indigo-300 rounded-lg text-xs font-medium text-neutral-700 hover:text-indigo-700 transition-smooth';
    raizBtn.innerHTML = '<i data-feather="home" class="w-3 h-3 mr-1"></i> Inicio';
    breadcrumbContainer.appendChild(raizBtn);
    
    // Agregar cada parte de la ruta
    let rutaAcumulada = '';
    partes.forEach((parte, index) => {
        rutaAcumulada += '/' + parte;
        
        // Separador
        const separador = document.createElement('span');
        separador.className = 'text-neutral-400 mx-1';
        separador.innerHTML = '<i data-feather="chevron-right" class="w-3 h-3"></i>';
        breadcrumbContainer.appendChild(separador);
        
        // Botón de carpeta
        const carpetaBtn = document.createElement('button');
        const rutaFinal = rutaAcumulada;
        carpetaBtn.onclick = () => navegarARuta(rutaFinal);
        
        // Última carpeta tiene estilo diferente (activa)
        if (index === partes.length - 1) {
            carpetaBtn.className = 'inline-flex items-center px-3 py-1.5 bg-indigo-100 border border-indigo-300 rounded-lg text-xs font-semibold text-indigo-700';
        } else {
            carpetaBtn.className = 'inline-flex items-center px-3 py-1.5 bg-white hover:bg-indigo-50 border border-neutral-200 hover:border-indigo-300 rounded-lg text-xs font-medium text-neutral-700 hover:text-indigo-700 transition-smooth';
        }
        
        carpetaBtn.innerHTML = `<i data-feather="folder" class="w-3 h-3 mr-1"></i> ${parte}`;
        breadcrumbContainer.appendChild(carpetaBtn);
    });
    
    feather.replace();
}

async function descargarArchivo(nombreArchivo) {
    mostrarModalDescarga('Descargando desde GoAnywhere...');
    
    try {
        const response = await fetch('/modulos/consolidador-t25/descargar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ archivo: nombreArchivo })
        });
        
        const data = await response.json();
        
        if (data.success) {
            actualizarModalDescarga('Preparando descarga...');
            
            setTimeout(() => {
                ocultarModalDescarga();
                
                // Descargar archivo
                window.location.href = `/modulos/consolidador-t25/download/${data.archivo}`;
                
                showNotification('✅ Archivo descargado exitosamente', 'success');
            }, 500);
        } else {
            ocultarModalDescarga();
            showNotification('Error al descargar: ' + data.error, 'error');
        }
        
    } catch (error) {
        ocultarModalDescarga();
        showNotification('Error: ' + error.message, 'error');
    }
}

function mostrarModalDescarga(mensaje) {
    const modal = document.getElementById('download-modal');
    const mensajeEl = document.getElementById('download-message');
    
    mensajeEl.textContent = mensaje;
    modal.classList.remove('hidden');
    feather.replace();
}

function actualizarModalDescarga(mensaje) {
    const mensajeEl = document.getElementById('download-message');
    mensajeEl.textContent = mensaje;
}

function ocultarModalDescarga() {
    const modal = document.getElementById('download-modal');
    modal.classList.add('hidden');
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// ============================================
// FUNCIONES DE BÚSQUEDA MEJORADAS
// ============================================

async function obtenerSugerencias(query) {
    try {
        const response = await fetch('/modulos/consolidador-t25/sugerencias', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query })
        });
        
        const data = await response.json();
        
        if (data.success && data.sugerencias.length > 0) {
            mostrarSugerencias(data.sugerencias);
        } else {
            ocultarSugerencias();
        }
        
    } catch (error) {
        console.error('Error al obtener sugerencias:', error);
    }
}

function mostrarSugerencias(sugerencias) {
    const container = document.getElementById('suggestions-container');
    container.innerHTML = '';
    
    sugerencias.forEach(sug => {
        const div = document.createElement('div');
        div.className = 'flex items-center space-x-3 p-3 hover:bg-indigo-50 cursor-pointer transition-smooth border-b border-neutral-100 last:border-0';
        div.onclick = () => {
            if (sug.es_directorio) {
                navegarARuta(sug.ruta);
            } else {
                document.getElementById('search-input').value = sug.nombre;
                ejecutarBusqueda();
            }
            ocultarSugerencias();
        };
        
        const extension = sug.nombre.includes('.') ? '.' + sug.nombre.split('.').pop().toLowerCase() : '';
        const style = getFileStyle(extension, sug.es_directorio);
        
        div.innerHTML = `
            <i data-feather="${style.icon}" class="w-4 h-4 ${style.text}"></i>
            <span class="text-sm text-neutral-900 flex-1">${sug.nombre}</span>
            <i data-feather="corner-down-left" class="w-3 h-3 text-neutral-400"></i>
        `;
        
        container.appendChild(div);
    });
    
    container.classList.remove('hidden');
    feather.replace();
}

function ocultarSugerencias() {
    const container = document.getElementById('suggestions-container');
    container.classList.add('hidden');
}

async function ejecutarBusqueda() {
    const searchInput = document.getElementById('search-input');
    const query = searchInput.value.trim();
    
    if (query.length < 2) {
        showNotification('⚠️ La búsqueda debe tener al menos 2 caracteres', 'warning');
        return;
    }
    
    if (isSearching) {
        showNotification('⚠️ Ya hay una búsqueda en progreso', 'warning');
        return;
    }
    
    isSearching = true;
    ocultarSugerencias();
    
    // Crear AbortController para cancelar búsqueda
    searchAbortController = new AbortController();
    
    // Mostrar loading SIN BLOQUEAR
    const loadingEl = document.getElementById('loading-files');
    const loadingText = document.getElementById('loading-text');
    const filesListEl = document.getElementById('files-list');
    const searchResultsEl = document.getElementById('search-results');
    const pathBreadcrumbEl = document.getElementById('path-breadcrumb');
    
    loadingEl.classList.remove('hidden');
    loadingText.innerHTML = `
        Buscando "<strong>${query}</strong>" en todas las carpetas...<br>
        <span class="text-xs text-neutral-500 mt-2 inline-block">Esto puede tomar hasta 30 segundos</span><br>
        <button onclick="cancelarBusqueda()" class="mt-3 px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg text-sm font-medium transition-smooth">
            <i data-feather="x" class="w-4 h-4 inline mr-1"></i>
            Cancelar búsqueda
        </button>
    `;
    feather.replace();
    
    filesListEl.classList.add('hidden');
    searchResultsEl.classList.add('hidden');
    pathBreadcrumbEl.classList.add('hidden');
    
    try {
        const response = await fetch('/modulos/consolidador-t25/buscar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                query,
                max_results: 100
            }),
            signal: searchAbortController.signal
        });
        
        const data = await response.json();
        
        loadingEl.classList.add('hidden');
        isSearching = false;
        searchAbortController = null;
        
        if (data.success) {
            if (data.timeout) {
                showNotification(`⏱️ Búsqueda detenida por timeout. Se encontraron ${data.total} resultados en ${data.carpetas_visitadas} carpetas`, 'warning');
            }
            mostrarResultadosBusqueda(data.resultados, query);
        } else {
            showNotification('❌ Error al buscar: ' + data.error, 'error');
            filesListEl.classList.remove('hidden');
            pathBreadcrumbEl.classList.remove('hidden');
        }
        
    } catch (error) {
        loadingEl.classList.add('hidden');
        isSearching = false;
        searchAbortController = null;
        
        if (error.name === 'AbortError') {
            showNotification('🛑 Búsqueda cancelada', 'info');
            filesListEl.classList.remove('hidden');
            pathBreadcrumbEl.classList.remove('hidden');
        } else {
            showNotification('❌ Error de conexión: ' + error.message, 'error');
            filesListEl.classList.remove('hidden');
            pathBreadcrumbEl.classList.remove('hidden');
        }
    }
}

function cancelarBusqueda() {
    if (searchAbortController) {
        searchAbortController.abort();
        isSearching = false;
        searchAbortController = null;
        
        document.getElementById('loading-files').classList.add('hidden');
        document.getElementById('files-list').classList.remove('hidden');
        document.getElementById('path-breadcrumb').classList.remove('hidden');
    }
}

function mostrarResultadosBusqueda(resultados, query) {
    const searchResultsEl = document.getElementById('search-results');
    const searchResultsList = document.getElementById('search-results-list');
    const searchCount = document.getElementById('search-count');
    
    searchCount.textContent = `${resultados.length} resultado${resultados.length !== 1 ? 's' : ''}`;
    searchResultsList.innerHTML = '';
    
    if (resultados.length === 0) {
        searchResultsList.innerHTML = `
            <div class="text-center py-12">
                <i data-feather="search" class="w-16 h-16 text-neutral-300 mx-auto mb-4"></i>
                <p class="text-neutral-600">No se encontraron resultados para "<strong>${query}</strong>"</p>
                <p class="text-xs text-neutral-500 mt-2">Intenta con otros términos de búsqueda</p>
            </div>
        `;
        feather.replace();
    } else {
        resultados.forEach(item => {
            const div = crearElementoResultado(item, query);
            searchResultsList.appendChild(div);
        });
        feather.replace();
    }
    
    searchResultsEl.classList.remove('hidden');
}

function crearElementoResultado(item, query) {
    const div = document.createElement('div');
    
    // Obtener extensión y estilo
    const extension = item.extension || '';
    const style = getFileStyle(extension, item.es_directorio);
    
    // Hacer clickeable
    if (item.es_directorio) {
        div.onclick = () => {
            volverANavegacion();
            navegarARuta(item.ruta);
        };
        div.className = 'flex items-center justify-between p-4 bg-white border border-neutral-200 rounded-xl hover:bg-indigo-50 hover:border-indigo-300 transition-smooth cursor-pointer';
    } else {
        div.onclick = () => descargarArchivoDesdeRuta(item.ruta, item.nombre);
        div.className = 'flex items-center justify-between p-4 bg-white border border-neutral-200 rounded-xl hover:bg-green-50 hover:border-green-300 transition-smooth cursor-pointer';
    }
    
    const tamano = item.es_directorio ? '-' : formatBytes(item.tamano);
    
    // Resaltar término de búsqueda en el nombre
    const nombreResaltado = item.nombre.replace(
        new RegExp(`(${query})`, 'gi'),
        '<mark class="bg-yellow-200 px-1 rounded font-semibold">$1</mark>'
    );
    
    div.innerHTML = `
        <div class="flex items-center space-x-4 flex-1 min-w-0">
            <div class="w-10 h-10 ${style.bg} rounded-lg flex items-center justify-center flex-shrink-0">
                <i data-feather="${style.icon}" class="w-5 h-5 ${style.text}"></i>
            </div>
            <div class="flex-1 min-w-0">
                <p class="text-sm font-semibold text-neutral-900 mb-1">${nombreResaltado}</p>
                <p class="text-xs text-neutral-500 truncate">
                    <i data-feather="folder" class="w-3 h-3 inline mr-1"></i>
                    ${item.ruta}
                </p>
                <p class="text-xs text-neutral-400 mt-1">
                    ${tamano} • ${item.fecha_modificacion}
                </p>
            </div>
        </div>
        <div class="flex items-center space-x-2 ml-4">
            ${item.es_directorio ? 
                `<div class="px-3 py-2 bg-indigo-100 text-indigo-700 rounded-lg text-sm font-medium">
                    <i data-feather="folder-open" class="w-4 h-4 inline mr-1"></i>
                    Ir
                </div>` :
                `<div class="px-3 py-2 bg-green-100 text-green-700 rounded-lg text-sm font-medium">
                    <i data-feather="download" class="w-4 h-4 inline"></i>
                </div>`
            }
        </div>
    `;
    
    return div;
}

async function descargarArchivoDesdeRuta(rutaCompleta, nombreArchivo) {
    mostrarModalDescarga('Descargando desde GoAnywhere...');
    
    try {
        const response = await fetch('/modulos/consolidador-t25/descargar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ archivo: rutaCompleta })
        });
        
        const data = await response.json();
        
        if (data.success) {
            actualizarModalDescarga('Preparando descarga...');
            
            setTimeout(() => {
                ocultarModalDescarga();
                window.location.href = `/modulos/consolidador-t25/download/${data.archivo}`;
                showNotification('✅ Archivo descargado exitosamente', 'success');
            }, 500);
        } else {
            ocultarModalDescarga();
            showNotification('Error al descargar: ' + data.error, 'error');
        }
        
    } catch (error) {
        ocultarModalDescarga();
        showNotification('Error: ' + error.message, 'error');
    }
}

function limpiarBusqueda() {
    const searchInput = document.getElementById('search-input');
    searchInput.value = '';
    document.getElementById('clear-search-btn').classList.add('hidden');
    ocultarSugerencias();
    volverANavegacion();
}

function volverANavegacion() {
    document.getElementById('search-results').classList.add('hidden');
    document.getElementById('files-list').classList.remove('hidden');
    document.getElementById('path-breadcrumb').classList.remove('hidden');
}