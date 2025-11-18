/**
 * Módulo de Especialidades - JavaScript
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
        dropzone.classList.add('border-positiva-500', 'bg-positiva-50');
    }, false);
});

['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, () => {
        dropzone.classList.remove('border-positiva-500', 'bg-positiva-50');
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
    validateBtn.classList.add('hidden');
    processBtn.classList.add('hidden');
}

// Validar archivo
function validateFile(file) {
    const allowedExtensions = ['xlsx', 'xls'];
    const maxSize = 10 * 1024 * 1024;
    
    const extension = file.name.split('.').pop().toLowerCase();
    
    if (!allowedExtensions.includes(extension)) {
        return {
            valid: false,
            error: 'Formato no permitido. Solo .xlsx y .xls'
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
    
    showLoading('Validando estructura...');
    updateProgress(50, 'Analizando archivo...');
    
    const formData = new FormData();
    formData.append('file', selectedFile);
    
    try {
        const response = await fetch('/modulos/especialidades/validar', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        hideLoading();
        
        if (result.success) {
            const allValid = result.validaciones.every(v => v.valida);
            
            if (allValid) {
                let detalles = result.validaciones.map(val => 
                    `<br>✓ ${val.hoja}: ${val.registros} registros`
                ).join('');
                
                showNotification(`✅ Archivo validado correctamente${detalles}`, 'success');
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
    
    showLoading('Iniciando procesamiento...');
    updateProgress(10, 'Subiendo archivo...');
    
    const formData = new FormData();
    formData.append('file', selectedFile);
    
    try {
        updateProgress(30, 'Validando estructura...');
        
        const response = await fetch('/modulos/especialidades/upload', {
            method: 'POST',
            body: formData
        });
        
        updateProgress(60, 'Asignando especialidades...');
        
        const result = await response.json();
        
        updateProgress(90, 'Generando resultados...');
        
        setTimeout(() => {
            hideLoading();
            
            if (result.success) {
                showNotification('✅ Archivo procesado exitosamente', 'success');
                
                // Redirigir a resultados
                setTimeout(() => {
                    window.location.href = '/modulos/especialidades/resultados?' + new URLSearchParams({
                        archivo: result.archivo_salida,
                        total: result.estadisticas.total_estudios,
                        especificos: result.estadisticas.estudios_especificos,
                        generales: result.estadisticas.estudios_generales,
                        tiempo: result.estadisticas.tiempo_ejecucion
                    });
                }, 1000);
            } else {
                showNotification(result.error || 'Error al procesar', 'error');
            }
        }, 500);
        
    } catch (error) {
        hideLoading();
        showNotification('Error de conexión', 'error');
        console.error(error);
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