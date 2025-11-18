/**
 * Módulo Consolidador de Servicios Médicos - JavaScript
 */

let selectedFile = null;

// Referencias DOM
const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('fileInput');
const dropzoneContent = document.getElementById('dropzone-content');
const filePreview = document.getElementById('file-preview');
const fileName = document.getElementById('file-name');
const fileSize = document.getElementById('file-size');
const removeFileBtn = document.getElementById('remove-file');
const validateBtn = document.getElementById('validate-btn');
const processBtn = document.getElementById('process-btn');
const fechaSection = document.getElementById('fecha-section');
const fechaAcuerdo = document.getElementById('fecha-acuerdo');
const loadingModal = document.getElementById('loading-modal');
const loadingMessage = document.getElementById('loading-message');
const progressBar = document.getElementById('progress-bar');
const progressText = document.getElementById('progress-text');

// Click en dropzone abre selector
dropzone.addEventListener('click', () => {
    if (!selectedFile) {
        fileInput.click();
    }
});

// Drag & Drop
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

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
    if (e.target.files.length > 0) {
        handleFile(e.target.files[0]);
    }
});

// Procesar archivo
function handleFile(file) {
    const validation = validateFile(file);
    
    if (!validation.valid) {
        showNotification(validation.error, 'error');
        return;
    }
    
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
    
    feather.replace();
}

// Remover archivo
removeFileBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    resetUpload();
});

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
validateBtn.addEventListener('click', async () => {
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
                
                showNotification(`✅ Archivo XLSB válido${detalles}`, 'success');
            } else {
                let errores = result.validaciones
                    .filter(v => !v.valida)
                    .map(val => `<br>✗ ${val.hoja}: ${val.error}`)
                    .join('');
                
                showNotification(`❌ Errores encontrados:${errores}`, 'error');
            }
        } else {
            showNotification(result.error || 'Error al validar', 'error');
        }
        
    } catch (error) {
        hideLoading();
        showNotification('Error de conexión al validar archivo', 'error');
        console.error(error);
    }
});

// Procesar archivo
processBtn.addEventListener('click', async () => {
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
                showNotification('✅ Consolidación completada exitosamente', 'success');
                
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
                showNotification(result.error || 'Error desconocido al procesar el archivo', 'error');
            }
        }, 500);
        
    } catch (error) {
        hideLoading();
        showNotification('Error de conexión. Revisa la consola para más detalles.', 'error');
        console.error('Error en la petición fetch:', error);
    }
});


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
