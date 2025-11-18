/**
 * Módulo Consolidador de Servicios Médicos - JavaScript
 */

let selectedFile = null;
let dropzone, fileInput, dropzoneContent, filePreview, fileName, fileSize;
let removeFileBtn, validateBtn, processBtn, fechaSection, fechaAcuerdo;
let loadingModal, loadingMessage, progressBar, progressText;

// Función de inicialización
function initConsolidador() {
    console.log('Iniciando consolidador...');

    // Referencias DOM
    dropzone = document.getElementById('dropzone');
    fileInput = document.getElementById('fileInput');
    dropzoneContent = document.getElementById('dropzone-content');
    filePreview = document.getElementById('file-preview');
    fileName = document.getElementById('file-name');
    fileSize = document.getElementById('file-size');
    removeFileBtn = document.getElementById('remove-file');
    validateBtn = document.getElementById('validate-btn');
    processBtn = document.getElementById('process-btn');
    fechaSection = document.getElementById('fecha-section');
    fechaAcuerdo = document.getElementById('fecha-acuerdo');
    loadingModal = document.getElementById('loading-modal');
    loadingMessage = document.getElementById('loading-message');
    progressBar = document.getElementById('progress-bar');
    progressText = document.getElementById('progress-text');

    // Verificar que todos los elementos existen con mensajes detallados
    const elementos = {
        dropzone, fileInput, dropzoneContent, filePreview, fileName, fileSize,
        removeFileBtn, validateBtn, processBtn, fechaSection, fechaAcuerdo,
        loadingModal, loadingMessage, progressBar, progressText
    };

    let faltantes = [];
    for (let [nombre, elemento] of Object.entries(elementos)) {
        if (!elemento) {
            faltantes.push(nombre);
            console.error(`Elemento faltante: ${nombre}`);
        }
    }

    if (faltantes.length > 0) {
        console.error('No se pudieron encontrar estos elementos:', faltantes);
        alert('Error: Algunos elementos de la página no se cargaron correctamente. Recarga la página.');
        return;
    }

    console.log('Todos los elementos DOM encontrados correctamente');

    // Inicializar event listeners
    try {
        initializeEventListeners();
        console.log('Event listeners inicializados correctamente');
    } catch (error) {
        console.error('Error al inicializar event listeners:', error);
        alert('Error al inicializar el consolidador: ' + error.message);
    }
}

// Esperar a que el DOM esté completamente cargado
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initConsolidador);
} else {
    // DOM ya está cargado
    initConsolidador();
}

function initializeEventListeners() {
    console.log('Configurando event listeners...');

    // Click en dropzone abre selector
    dropzone.addEventListener('click', (e) => {
        console.log('Click en dropzone detectado');
        if (!selectedFile) {
            console.log('Abriendo selector de archivos...');
            fileInput.click();
        } else {
            console.log('Ya hay un archivo seleccionado');
        }
    });

    // Drag & Drop
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, preventDefaults, false);
    });

    // Highlight
    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, () => {
            dropzone.classList.add('border-blue-500', 'bg-blue-50');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, () => {
            dropzone.classList.remove('border-blue-500', 'bg-blue-50');
        }, false);
    });

    // Handle drop
    dropzone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });

    // Handle file selection
    fileInput.addEventListener('change', (e) => {
        console.log('Evento change del input detectado');
        console.log('Archivos seleccionados:', e.target.files.length);
        if (e.target.files.length > 0) {
            console.log('Archivo:', e.target.files[0].name);
            handleFile(e.target.files[0]);
        }
    });

    // Remover archivo
    removeFileBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        resetUpload();
    });

    // Validar estructura
    validateBtn.addEventListener('click', validarArchivo);

    // Procesar archivo
    processBtn.addEventListener('click', procesarArchivo);
}

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

// Helper para mostrar notificaciones de forma segura
function safeShowNotification(message, type) {
    if (typeof showNotification === 'function') {
        showNotification(message, type);
    } else {
        console.error('showNotification no está disponible:', message);
        alert(message);
    }
}

// Procesar archivo
function handleFile(file) {
    console.log('handleFile llamado con:', file.name, file.size, 'bytes');

    const validation = validateFile(file);
    console.log('Validación:', validation);

    if (!validation.valid) {
        console.error('Archivo no válido:', validation.error);
        safeShowNotification(validation.error, 'error');
        return;
    }

    console.log('Archivo válido, guardando...');
    selectedFile = file;
    
    // Mostrar preview
    dropzoneContent.classList.add('hidden');
    filePreview.classList.remove('hidden');
    fileName.textContent = file.name;
    fileSize.textContent = formatFileSize(file.size);
    
    // Mostrar sección de fecha
    fechaSection.classList.remove('hidden');
    
    // Mostrar botones
    validateBtn.classList.remove('hidden');
    processBtn.classList.remove('hidden');

    if (typeof feather !== 'undefined') {
        feather.replace();
    }

    console.log('Archivo cargado exitosamente. Preview y botones mostrados.');
}

function resetUpload() {
    selectedFile = null;
    fileInput.value = '';
    dropzoneContent.classList.remove('hidden');
    filePreview.classList.add('hidden');
    fechaSection.classList.add('hidden');
    validateBtn.classList.add('hidden');
    processBtn.classList.add('hidden');
}

// Validar archivo
function validateFile(file) {
    const allowedExtensions = ['xlsb'];
    const maxSize = 10 * 1024 * 1024;
    
    const extension = file.name.split('.').pop().toLowerCase();
    
    if (!allowedExtensions.includes(extension)) {
        return {
            valid: false,
            error: 'Formato no permitido. Solo archivos .xlsb'
        };
    }
    
    if (file.size > maxSize) {
        return {
            valid: false,
            error: 'El archivo excede 10 MB'
        };
    }
    
    return { valid: true };
}

// Formatear tamaño
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Validar estructura
async function validarArchivo() {
    if (!selectedFile) return;

    showLoading('Validando archivo XLSB...');
    updateProgress(50, 'Analizando estructura...');

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
        const response = await fetch('/modulos/consolidador/validar', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();
        hideLoading();

        if (response.ok) {
            const allValid = result.validaciones.every(v => v.valida);

            if (allValid) {
                let detalles = result.validaciones.map(val =>
                    `<br>✓ ${val.hoja}: ${val.registros} filas`
                ).join('');

                safeShowNotification(`✅ Archivo XLSB válido${detalles}`, 'success');
            } else {
                let errores = result.validaciones
                    .filter(v => !v.valida)
                    .map(val => `<br>✗ ${val.hoja}: ${val.error}`)
                    .join('');

                safeShowNotification(`❌ Errores encontrados:${errores}`, 'error');
            }
        } else {
            safeShowNotification(result.error || 'Error al validar', 'error');
        }

    } catch (error) {
        hideLoading();
        safeShowNotification('Error de conexión al validar archivo', 'error');
        console.error(error);
    }
}

// Procesar archivo
async function procesarArchivo() {
    if (!selectedFile) return;
    
    showLoading('Iniciando consolidación...');
    updateProgress(10, 'Subiendo archivo...');
    
    const formData = new FormData();
    formData.append('file', selectedFile);
    
    const fecha = fechaAcuerdo.value;
    if (fecha) {
        formData.append('fecha_acuerdo', fecha);
    }
    
    try {
        updateProgress(30, 'Leyendo archivo XLSB...');
        
        const response = await fetch('/modulos/consolidador/upload', {
            method: 'POST',
            body: formData
        });
        
        updateProgress(60, 'Consolidando servicios de sedes...');
        
        const result = await response.json();
        
        updateProgress(90, 'Generando archivo Excel...');
        
        setTimeout(() => {
            hideLoading();
            
            if (response.ok) {
                safeShowNotification('✅ Consolidación completada exitosamente', 'success');
                
                setTimeout(() => {
                    window.location.href = '/modulos/consolidador/resultados?' + new URLSearchParams({
                        archivo: result.archivo_salida,
                        sedes: result.estadisticas.total_sedes,
                        servicios: result.estadisticas.total_servicios,
                        tiempo: result.estadisticas.tiempo_ejecucion,
                        fecha: result.estadisticas.fecha_acuerdo
                    });
                }, 1000);
            } else {
                // Mostrar error específico del servidor
                safeShowNotification(result.error || 'Error desconocido al procesar el archivo', 'error');
            }
        }, 500);
        
    } catch (error) {
        hideLoading();
        safeShowNotification('Error de conexión. Revisa la consola para más detalles.', 'error');
        console.error('Error en la petición fetch:', error);
    }
}

// Loading modal
function showLoading(message) {
    loadingMessage.textContent = message;
    loadingModal.classList.remove('hidden');
    updateProgress(0, '0%');
}

function hideLoading() {
    loadingModal.classList.add('hidden');
}

function updateProgress(percent, text) {
    progressBar.style.width = percent + '%';
    progressText.textContent = text || (percent + '%');
}
