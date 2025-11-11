/**
 * Main JavaScript para Plataforma FC Penafiel
 */

// Función para mostrar loader
function showLoader() {
    const loader = document.getElementById('loader');
    if (loader) {
        loader.classList.remove('hidden');
    }
}

// Función para ocultar loader
function hideLoader() {
    const loader = document.getElementById('loader');
    if (loader) {
        loader.classList.add('hidden');
    }
}

// Función para mostrar alertas
function showAlert(message, type = 'info') {
    const alertContainer = document.getElementById('alertContainer');
    if (!alertContainer) return;

    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; color: white; font-size: 1.2rem; cursor: pointer;">&times;</button>
        </div>
    `;

    alertContainer.appendChild(alert);

    // Auto-cerrar después de 5 segundos
    setTimeout(() => {
        alert.remove();
    }, 5000);
}

// Actualizar fecha de última actualización
function updateLastUpdate() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('es-ES', {
        hour: '2-digit',
        minute: '2-digit'
    });
    const element = document.getElementById('ultimaActualizacion');
    if (element) {
        element.textContent = timeString;
    }
}

// Botón de actualizar datos
document.addEventListener('DOMContentLoaded', function() {
    const btnActualizar = document.getElementById('actualizarDatos');
    if (btnActualizar) {
        btnActualizar.addEventListener('click', async function() {
            const icon = this.querySelector('i');
            icon.classList.add('fa-spin');
            this.disabled = true;

            try {
                const response = await fetch('/api/actualizar-datos');
                const data = await response.json();

                if (data.status === 'success') {
                    showAlert('Datos actualizados correctamente', 'success');
                    updateLastUpdate();
                    // Recargar la página después de 1 segundo
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                } else {
                    showAlert('Error al actualizar datos: ' + data.message, 'error');
                }
            } catch (error) {
                console.error('Error:', error);
                showAlert('Error al actualizar datos', 'error');
            } finally {
                icon.classList.remove('fa-spin');
                this.disabled = false;
            }
        });
    }
});

// Manejo de tabs
function setupTabs() {
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            // Remover active de todos los tabs
            tabs.forEach(t => t.classList.remove('active'));
            // Agregar active al tab clickeado
            this.classList.add('active');

            // Manejar contenido de tabs
            const targetId = this.getAttribute('data-target');
            if (targetId) {
                document.querySelectorAll('.tab-content').forEach(content => {
                    content.classList.remove('active');
                });
                const targetContent = document.getElementById(targetId);
                if (targetContent) {
                    targetContent.classList.add('active');
                }
            }
        });
    });
}

// Llamar a setupTabs cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', setupTabs);

// Función para formatear números
function formatNumber(num, decimals = 2) {
    if (num === null || num === undefined || isNaN(num)) {
        return '--';
    }
    return num.toFixed(decimals);
}

// Función para formatear porcentajes
function formatPercentage(num, decimals = 1) {
    if (num === null || num === undefined || isNaN(num)) {
        return '--%';
    }
    return num.toFixed(decimals) + '%';
}

// Manejo de errores global
window.addEventListener('error', function(e) {
    console.error('Error global:', e.error);
});

// Manejo de errores de promesas no capturadas
window.addEventListener('unhandledrejection', function(e) {
    console.error('Promise rejection no manejada:', e.reason);
});

// Verificar estado de salud de la API periódicamente
setInterval(async function() {
    try {
        const response = await fetch('/api/health');
        const data = await response.json();
        if (data.status !== 'healthy') {
            console.warn('API no está en estado saludable');
        }
    } catch (error) {
        console.error('Error verificando salud de la API:', error);
    }
}, 60000); // Cada minuto

// Exportar funciones útiles
window.PenafielPlatform = {
    showLoader,
    hideLoader,
    showAlert,
    updateLastUpdate,
    formatNumber,
    formatPercentage
};
