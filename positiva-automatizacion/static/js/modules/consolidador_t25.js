/**
 * CONSOLIDADOR T25 - Frontend
 * Manejo de conexiones GoAnywhere, búsqueda de contratos y procesamiento
 */

// Estado global
let isConnected = false;
let maestraCargada = false;
let contratoSeleccionado = null;
let archivoConsolidado = null;

// ============================================================================
// INICIALIZACIÓN
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('Módulo Consolidador T25 cargado');
    
    // Verificar estado inicial
    verificarEstadoMaestra();
    verificarEstadoGoAnywhere();
    cargarEstadisticas();
    
    // Event listeners
    setupEventListeners();
    
    // Reemplazar iconos de Feather
    feather.replace();
});

function setupEventListeners() {
    // Maestra
    document.getElementById('btn-cargar-maestra').addEventListener('click', () => {
        document.getElementById('input-maestra').click();
    });
    
    document.getElementById('input-maestra').addEventListener('change', subirMaestra);
    
    // GoAnywhere
    document.getElementById('btn-conectar-goanywhere').addEventListener('click', conectarGoAnywhere);
    document.getElementById('btn-desconectar-goanywhere').addEventListener('click', desconectarGoAnywhere);
    
    // Búsqueda de contratos
    document.getElementById('btn-buscar-contrato').addEventListener('click', buscarContrato);
    document.getElementById('input-numero-contrato').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            buscarContrato();
        }
    });
    
    // Procesamiento
    document.getElementById('btn-procesar').addEventListener('click', procesarContrato);
    document.getElementById('btn-procesar-masivo').addEventListener('click', procesarMasivo);
    
    // Descarga
    document.getElementById('btn-descargar').addEventListener('click', descargarArchivo);
    
    // Modales
    document.getElementById('btn-cerrar-procesamiento').addEventListener('click', () => {
        document.getElementById('modal-procesamiento').classList.add('hidden');
    });
    
    document.getElementById('btn-cerrar-resultado').addEventListener('click', () => {
        document.getElementById('modal-resultado').classList.add('hidden');
    });
}

// ============================================================================
// GESTIÓN DE MAESTRA
// ============================================================================

async function verificarEstadoMaestra() {
    try {
        const response = await fetch('/modulos/consolidador-t25/maestra/estado');
        const data = await response.json();
        
        maestraCargada = data.cargada;
        
        const statusMaestra = document.getElementById('status-maestra');
        const btnCargar = document.getElementById('btn-cargar-maestra');
        
        if (data.cargada) {
            statusMaestra.innerHTML = `
                <div class="flex items-center space-x-2">
                    <i data-feather="check-circle" class="w-5 h-5 text-green-600"></i>
                    <span class="text-green-700">Maestra cargada (${data.total_contratos} contratos)</span>
                </div>
            `;
            btnCargar.innerHTML = '<i data-feather="refresh-cw" class="w-4 h-4 mr-2"></i>Recargar maestra';
            btnCargar.classList.remove('bg-blue-600', 'hover:bg-blue-700');
            btnCargar.classList.add('bg-gray-600', 'hover:bg-gray-700');
        } else {
            statusMaestra.innerHTML = `
                <div class="flex items-center space-x-2">
                    <i data-feather="alert-circle" class="w-5 h-5 text-yellow-600"></i>
                    <span class="text-yellow-700">No hay maestra cargada</span>
                </div>
            `;
            btnCargar.innerHTML = '<i data-feather="upload" class="w-4 h-4 mr-2"></i>Cargar maestra';
        }
        
        feather.replace();
    } catch (error) {
        console.error('Error verificando estado de maestra:', error);
    }
}

async function subirMaestra(event) {
    const archivo = event.target.files[0];
    
    if (!archivo) return;
    
    if (!archivo.name.endsWith('.xlsb')) {
        showNotification('Solo se permiten archivos .xlsb', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('archivo', archivo);
    
    const btnCargar = document.getElementById('btn-cargar-maestra');
    btnCargar.disabled = true;
    btnCargar.innerHTML = '<i data-feather="loader" class="w-4 h-4 mr-2 animate-spin"></i>Cargando...';
    feather.replace();
    
    try {
        const response = await fetch('/modulos/consolidador-t25/maestra/subir', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(`Maestra cargada: ${data.total_contratos} contratos, ${data.total_prestadores} prestadores`, 'success');
            verificarEstadoMaestra();
            cargarEstadisticas();
        } else {
            showNotification('Error al cargar maestra: ' + data.error, 'error');
        }
        
    } catch (error) {
        showNotification('Error de conexión al cargar maestra', 'error');
        console.error('Error:', error);
    } finally {
        btnCargar.disabled = false;
        verificarEstadoMaestra();
    }
}

// ============================================================================
// CONEXIÓN A GOANYWHERE
// ============================================================================

async function verificarEstadoGoAnywhere() {
    try {
        const response = await fetch('/modulos/consolidador-t25/goanywhere/estado');
        const data = await response.json();
        
        isConnected = data.conectado;
        actualizarEstadoConexion();
        
    } catch (error) {
        console.error('Error verificando estado de GoAnywhere:', error);
        isConnected = false;
        actualizarEstadoConexion();
    }
}

async function conectarGoAnywhere() {
    const btnConectar = document.getElementById('btn-conectar-goanywhere');
    btnConectar.disabled = true;
    btnConectar.innerHTML = '<i data-feather="loader" class="w-4 h-4 mr-2 animate-spin"></i>Conectando...';
    feather.replace();
    
    try {
        const response = await fetch('/modulos/consolidador-t25/goanywhere/conectar', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            isConnected = true;
            showNotification('Conectado a GoAnywhere exitosamente', 'success');
            actualizarEstadoConexion();
        } else {
            showNotification('Error al conectar: ' + data.error, 'error');
        }
        
    } catch (error) {
        showNotification('Error de conexión a GoAnywhere', 'error');
        console.error('Error:', error);
    } finally {
        btnConectar.disabled = false;
        verificarEstadoGoAnywhere();
    }
}

async function desconectarGoAnywhere() {
    const btnDesconectar = document.getElementById('btn-desconectar-goanywhere');
    btnDesconectar.disabled = true;
    
    try {
        const response = await fetch('/modulos/consolidador-t25/goanywhere/desconectar', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            isConnected = false;
            showNotification('Desconectado de GoAnywhere', 'success');
            actualizarEstadoConexion();
        }
        
    } catch (error) {
        showNotification('Error al desconectar', 'error');
        console.error('Error:', error);
    } finally {
        btnDesconectar.disabled = false;
    }
}

function actualizarEstadoConexion() {
    const statusGoAnywhere = document.getElementById('status-goanywhere');
    const btnConectar = document.getElementById('btn-conectar-goanywhere');
    const btnDesconectar = document.getElementById('btn-desconectar-goanywhere');
    
    if (isConnected) {
        statusGoAnywhere.innerHTML = `
            <div class="flex items-center space-x-2">
                <div class="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                <span class="text-green-700 font-medium">Conectado</span>
            </div>
        `;
        btnConectar.classList.add('hidden');
        btnDesconectar.classList.remove('hidden');
    } else {
        statusGoAnywhere.innerHTML = `
            <div class="flex items-center space-x-2">
                <div class="w-3 h-3 bg-red-500 rounded-full"></div>
                <span class="text-red-700 font-medium">Desconectado</span>
            </div>
        `;
        btnConectar.classList.remove('hidden');
        btnDesconectar.classList.add('hidden');
    }
    
    feather.replace();
}

// ============================================================================
// BÚSQUEDA DE CONTRATOS
// ============================================================================

async function buscarContrato() {
    if (!maestraCargada) {
        showNotification('Debes cargar la maestra primero', 'warning');
        return;
    }
    
    const numeroContrato = document.getElementById('input-numero-contrato').value.trim();
    
    if (!numeroContrato) {
        showNotification('Ingresa un número de contrato', 'warning');
        return;
    }
    
    const btnBuscar = document.getElementById('btn-buscar-contrato');
    btnBuscar.disabled = true;
    btnBuscar.innerHTML = '<i data-feather="loader" class="w-4 h-4 mr-2 animate-spin"></i>Buscando...';
    feather.replace();
    
    try {
        const response = await fetch('/modulos/consolidador-t25/buscar-contrato', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ numero_contrato: numeroContrato })
        });
        
        const data = await response.json();
        
        if (data.success && data.contratos.length > 0) {
            contratoSeleccionado = data.contratos[0];
            mostrarDetalleContrato(contratoSeleccionado);
            showNotification('Contrato encontrado', 'success');
        } else {
            showNotification(data.error || 'Contrato no encontrado', 'error');
            limpiarDetalleContrato();
        }
        
    } catch (error) {
        showNotification('Error al buscar contrato', 'error');
        console.error('Error:', error);
        limpiarDetalleContrato();
    } finally {
        btnBuscar.disabled = false;
        btnBuscar.innerHTML = '<i data-feather="search" class="w-4 h-4 mr-2"></i>Buscar';
        feather.replace();
    }
}

function mostrarDetalleContrato(contrato) {
    const detalleCard = document.getElementById('detalle-contrato-card');
    const detalleContent = document.getElementById('detalle-contrato-content');
    
    let otrosiHTML = '';
    if (contrato.otrosi && contrato.otrosi.length > 0) {
        otrosiHTML = '<div class="mt-3"><p class="text-sm font-medium text-gray-700 mb-2">Otrosí:</p><div class="space-y-1">';
        contrato.otrosi.forEach(o => {
            otrosiHTML += `<p class="text-sm text-gray-600">- Otrosí ${o.numero}: ${o.fecha || 'Sin fecha'}</p>`;
        });
        otrosiHTML += '</div></div>';
    }
    
    let actasHTML = '';
    if (contrato.actas && contrato.actas.length > 0) {
        actasHTML = '<div class="mt-3"><p class="text-sm font-medium text-gray-700 mb-2">Actas:</p><div class="space-y-1">';
        contrato.actas.forEach(a => {
            actasHTML += `<p class="text-sm text-gray-600">- Acta ${a.numero}: ${a.fecha || 'Sin fecha'}</p>`;
        });
        actasHTML += '</div></div>';
    }
    
    detalleContent.innerHTML = `
        <div class="space-y-3">
            <div>
                <p class="text-sm text-gray-600">Número de contrato:</p>
                <p class="text-base font-semibold text-gray-900">${contrato.numero_contrato}</p>
            </div>
            <div>
                <p class="text-sm text-gray-600">Razón social:</p>
                <p class="text-base font-medium text-gray-900">${contrato.razon_social}</p>
            </div>
            <div>
                <p class="text-sm text-gray-600">NIT:</p>
                <p class="text-base text-gray-900">${contrato.nit}</p>
            </div>
            <div>
                <p class="text-sm text-gray-600">Fecha inicial:</p>
                <p class="text-base text-gray-900">${contrato.fecha_inicial || 'N/A'}</p>
            </div>
            ${otrosiHTML}
            ${actasHTML}
        </div>
    `;
    
    detalleCard.classList.remove('hidden');
    document.getElementById('btn-procesar').disabled = false;
}

function limpiarDetalleContrato() {
    const detalleCard = document.getElementById('detalle-contrato-card');
    const detalleContent = document.getElementById('detalle-contrato-content');
    
    detalleCard.classList.add('hidden');
    detalleContent.innerHTML = '';
    contratoSeleccionado = null;
    document.getElementById('btn-procesar').disabled = true;
}

// ============================================================================
// PROCESAMIENTO
// ============================================================================

async function procesarContrato() {
    if (!isConnected) {
        showNotification('Debes conectarte a GoAnywhere primero', 'warning');
        return;
    }
    
    if (!contratoSeleccionado) {
        showNotification('Selecciona un contrato', 'warning');
        return;
    }
    
    const modal = document.getElementById('modal-procesamiento');
    const mensajeProceso = document.getElementById('mensaje-proceso');
    const logContent = document.getElementById('log-content');
    const btnProcesar = document.getElementById('btn-procesar');
    
    modal.classList.remove('hidden');
    btnProcesar.disabled = true;
    logContent.innerHTML = '';
    feather.replace();
    
    agregarLog('Iniciando procesamiento...', 'info');
    agregarLog('Contrato: ' + contratoSeleccionado.numero_contrato, 'info');
    
    try {
        mensajeProceso.textContent = 'Procesando anexos...';
        
        const response = await fetch('/modulos/consolidador-t25/buscar-contrato/procesar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ numero_contrato: contratoSeleccionado.numero_contrato })
        });
        
        const data = await response.json();
        
        // Mostrar logs del servidor
        if (data.logs && data.logs.length > 0) {
            data.logs.forEach(log => {
                agregarLog(log.mensaje, log.tipo);
            });
        }
        
        modal.classList.add('hidden');
        btnProcesar.disabled = false;
        
        if (data.success) {
            archivoConsolidado = data.archivo;
            mostrarResultado(data);
        } else {
            agregarLog('Error: ' + data.error, 'error');
            showNotification('Error al procesar: ' + data.error, 'error');
            
            if (data.alertas && data.alertas.length > 0) {
                data.alertas.forEach(alerta => {
                    agregarLog(alerta.mensaje, 'warning');
                });
            }
            
            // Mostrar logs en consola para debugging
            console.error('Error completo:', data);
            if (data.traceback) {
                console.error('Traceback:', data.traceback);
            }
        }
        
    } catch (error) {
        modal.classList.add('hidden');
        btnProcesar.disabled = false;
        agregarLog('Error de conexión: ' + error.message, 'error');
        showNotification('Error de conexión', 'error');
        console.error('Error completo:', error);
    }
}

async function procesarMasivo() {
    if (!isConnected) {
        showNotification('Debes conectarte a GoAnywhere primero', 'warning');
        return;
    }
    
    if (!maestraCargada) {
        showNotification('Debes cargar la maestra primero', 'warning');
        return;
    }
    
    if (!confirm('Esto procesará TODOS los contratos de prestadores de salud. Puede tardar varios minutos. ¿Continuar?')) {
        return;
    }
    
    const modal = document.getElementById('modal-procesamiento');
    const mensajeProceso = document.getElementById('mensaje-proceso');
    const logContent = document.getElementById('log-content');
    const btnMasivo = document.getElementById('btn-procesar-masivo');
    
    modal.classList.remove('hidden');
    btnMasivo.disabled = true;
    logContent.innerHTML = '';
    
    agregarLog('Iniciando procesamiento masivo...', 'info');
    mensajeProceso.textContent = 'Procesando todos los contratos...';
    
    try {
        const response = await fetch('/modulos/consolidador-t25/procesar-masivo', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        modal.classList.add('hidden');
        btnMasivo.disabled = false;
        
        if (data.success) {
            archivoConsolidado = data.archivo;
            agregarLog(`Procesamiento masivo completado`, 'info');
            agregarLog(`Contratos procesados: ${data.total_contratos_procesados}`, 'info');
            agregarLog(`Total de servicios: ${data.total_servicios}`, 'info');
            agregarLog(`Total de alertas: ${data.total_alertas}`, 'info');
            
            mostrarResultado(data);
            cargarEstadisticas();
        } else {
            showNotification('Error en procesamiento masivo: ' + data.error, 'error');
            
            if (data.alertas) {
                data.alertas.forEach(alerta => {
                    agregarLog(alerta.mensaje, 'warning');
                });
            }
        }
        
    } catch (error) {
        modal.classList.add('hidden');
        btnMasivo.disabled = false;
        showNotification('Error de conexión en procesamiento masivo', 'error');
        console.error('Error:', error);
    }
}

function mostrarResultado(data) {
    const modal = document.getElementById('modal-resultado');
    const resultadoContent = document.getElementById('resultado-content');
    const btnDescargar = document.getElementById('btn-descargar');
    
    let alertasHTML = '';
    if (data.alertas && data.alertas.length > 0) {
        alertasHTML = `
            <div class="mt-4">
                <h4 class="text-sm font-semibold text-gray-700 mb-2">Alertas (${data.alertas.length}):</h4>
                <div class="space-y-2 max-h-48 overflow-y-auto">
        `;
        
        data.alertas.forEach(alerta => {
            const iconColor = alerta.tipo === 'error' ? 'text-red-600' : 
                            alerta.tipo === 'warning' ? 'text-yellow-600' : 'text-blue-600';
            const icon = alerta.tipo === 'error' ? 'x-circle' : 
                        alerta.tipo === 'warning' ? 'alert-triangle' : 'info';
            
            alertasHTML += `
                <div class="flex items-start space-x-2 text-sm">
                    <i data-feather="${icon}" class="w-4 h-4 ${iconColor} mt-0.5 flex-shrink-0"></i>
                    <span class="text-gray-700">${alerta.mensaje}</span>
                </div>
            `;
        });
        
        alertasHTML += `
                </div>
            </div>
        `;
    }
    
    resultadoContent.innerHTML = `
        <div class="space-y-4">
            <div class="grid grid-cols-2 gap-4">
                <div class="bg-green-50 p-4 rounded-lg">
                    <p class="text-sm text-green-700 font-medium">Total de servicios</p>
                    <p class="text-2xl font-bold text-green-900">${data.total_servicios || 0}</p>
                </div>
                <div class="bg-blue-50 p-4 rounded-lg">
                    <p class="text-sm text-blue-700 font-medium">Anexos procesados</p>
                    <p class="text-2xl font-bold text-blue-900">${data.total_anexos || 0}</p>
                </div>
            </div>
            ${alertasHTML}
        </div>
    `;
    
    btnDescargar.disabled = false;
    modal.classList.remove('hidden');
    feather.replace();
}

function agregarLog(mensaje, tipo = 'info') {
    const logContent = document.getElementById('log-content');
    const timestamp = new Date().toLocaleTimeString();
    
    let colorClass = 'text-gray-700';
    let icon = 'info';
    
    if (tipo === 'error') {
        colorClass = 'text-red-700';
        icon = 'x-circle';
    } else if (tipo === 'warning') {
        colorClass = 'text-yellow-700';
        icon = 'alert-triangle';
    } else if (tipo === 'success') {
        colorClass = 'text-green-700';
        icon = 'check-circle';
    }
    
    const logEntry = document.createElement('div');
    logEntry.className = 'flex items-start space-x-2 text-sm';
    logEntry.innerHTML = `
        <i data-feather="${icon}" class="w-4 h-4 ${colorClass} mt-0.5 flex-shrink-0"></i>
        <span class="text-gray-500 flex-shrink-0">${timestamp}</span>
        <span class="${colorClass}">${mensaje}</span>
    `;
    
    logContent.appendChild(logEntry);
    logContent.scrollTop = logContent.scrollHeight;
    
    feather.replace();
}

// ============================================================================
// DESCARGA
// ============================================================================

function descargarArchivo() {
    if (!archivoConsolidado) {
        showNotification('No hay archivo para descargar', 'warning');
        return;
    }
    
    window.location.href = `/modulos/consolidador-t25/descargar/${archivoConsolidado}`;
    showNotification('Descargando archivo...', 'success');
}

// ============================================================================
// ESTADÍSTICAS
// ============================================================================

async function cargarEstadisticas() {
    try {
        const response = await fetch('/modulos/consolidador-t25/estadisticas');
        const data = await response.json();
        
        document.getElementById('total-procesos').textContent = data.total_procesos || 0;
        document.getElementById('total-registros').textContent = data.total_registros || 0;
        document.getElementById('tasa-exito').textContent = (data.tasa_exito || 0) + '%';
        
    } catch (error) {
        console.error('Error cargando estadísticas:', error);
    }
}

// ============================================================================
// NOTIFICACIONES
// ============================================================================

function showNotification(mensaje, tipo = 'info') {
    // Crear notificación toast
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 transform transition-all duration-300 translate-x-full`;
    
    let bgColor = 'bg-blue-600';
    let icon = 'info';
    
    if (tipo === 'success') {
        bgColor = 'bg-green-600';
        icon = 'check-circle';
    } else if (tipo === 'error') {
        bgColor = 'bg-red-600';
        icon = 'x-circle';
    } else if (tipo === 'warning') {
        bgColor = 'bg-yellow-600';
        icon = 'alert-triangle';
    }
    
    notification.className += ` ${bgColor} text-white`;
    notification.innerHTML = `
        <div class="flex items-center space-x-3">
            <i data-feather="${icon}" class="w-5 h-5"></i>
            <span>${mensaje}</span>
        </div>
    `;
    
    document.body.appendChild(notification);
    feather.replace();
    
    // Animación de entrada
    setTimeout(() => {
        notification.classList.remove('translate-x-full');
    }, 10);
    
    // Remover después de 5 segundos
    setTimeout(() => {
        notification.classList.add('translate-x-full');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 5000);
}