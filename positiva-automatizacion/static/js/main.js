/**
 * JavaScript principal del sistema
 */

// Sistema de notificaciones mejorado
function showNotification(message, type = 'info') {
    const container = document.getElementById('notification-container');
    
    const colors = {
        'success': 'bg-green-50 border-green-500 text-green-800',
        'error': 'bg-red-50 border-red-500 text-red-800',
        'warning': 'bg-yellow-50 border-yellow-500 text-yellow-800',
        'info': 'bg-blue-50 border-blue-500 text-blue-800'
    };
    
    const icons = {
        'success': 'check-circle',
        'error': 'x-circle',
        'warning': 'alert-triangle',
        'info': 'info'
    };
    
    const notification = document.createElement('div');
    notification.className = `${colors[type]} border-l-4 rounded-xl p-4 shadow-lg transform transition-all duration-300 translate-x-0 animate-slide-in`;
    notification.innerHTML = `
        <div class="flex items-start space-x-3">
            <div class="flex-shrink-0">
                <i data-feather="${icons[type]}" class="w-5 h-5 mt-0.5"></i>
            </div>
            <p class="text-sm font-medium flex-1 leading-relaxed">${message}</p>
            <button onclick="this.parentElement.parentElement.remove()" class="ml-2 hover:opacity-70 flex-shrink-0">
                <i data-feather="x" class="w-4 h-4"></i>
            </button>
        </div>
    `;
    
    container.appendChild(notification);
    feather.replace();
    
    // Auto-remover con animación
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

// Formatear números
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// Inicializar tooltips y feather icons
document.addEventListener('DOMContentLoaded', function() {
    // Reinicializar iconos de Feather
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
});