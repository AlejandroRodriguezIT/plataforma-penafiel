/**
 * Módulo de Charts para Plataforma FC Penafiel
 * Maneja la creación y actualización de gráficas
 */

// Configuración global de Chart.js
if (typeof Chart !== 'undefined') {
    Chart.defaults.font.family = 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif';
    Chart.defaults.color = '#2c3e50';
}

// Colores de la plataforma
const COLORS = {
    primary: '#9b59b6',
    success: '#27ae60',
    info: '#3498db',
    warning: '#f39c12',
    danger: '#e74c3c',
    gray: '#95a5a6',
    dark: '#2c3e50',
    light: '#ecf0f1'
};

/**
 * Crea una gráfica de barras
 * @param {string} canvasId - ID del canvas donde crear la gráfica
 * @param {object} data - Datos para la gráfica
 * @param {object} options - Opciones adicionales
 */
function createBarChart(canvasId, data, options = {}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) {
        console.error(`Canvas ${canvasId} not found`);
        return null;
    }

    const ctx = canvas.getContext('2d');

    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: true,
                position: 'top'
            },
            tooltip: {
                mode: 'index',
                intersect: false
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                grid: {
                    color: 'rgba(0, 0, 0, 0.05)'
                }
            },
            x: {
                grid: {
                    display: false
                }
            }
        }
    };

    return new Chart(ctx, {
        type: 'bar',
        data: data,
        options: { ...defaultOptions, ...options }
    });
}

/**
 * Crea una gráfica de líneas
 * @param {string} canvasId - ID del canvas donde crear la gráfica
 * @param {object} data - Datos para la gráfica
 * @param {object} options - Opciones adicionales
 */
function createLineChart(canvasId, data, options = {}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) {
        console.error(`Canvas ${canvasId} not found`);
        return null;
    }

    const ctx = canvas.getContext('2d');

    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: true,
                position: 'top'
            }
        },
        scales: {
            y: {
                beginAtZero: false,
                grid: {
                    color: 'rgba(0, 0, 0, 0.05)'
                }
            },
            x: {
                grid: {
                    display: false
                }
            }
        },
        interaction: {
            mode: 'index',
            intersect: false
        }
    };

    return new Chart(ctx, {
        type: 'line',
        data: data,
        options: { ...defaultOptions, ...options }
    });
}

/**
 * Crea una gráfica de radar
 * @param {string} canvasId - ID del canvas donde crear la gráfica
 * @param {object} data - Datos para la gráfica
 * @param {object} options - Opciones adicionales
 */
function createRadarChart(canvasId, data, options = {}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) {
        console.error(`Canvas ${canvasId} not found`);
        return null;
    }

    const ctx = canvas.getContext('2d');

    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: true,
                position: 'top'
            }
        },
        scales: {
            r: {
                beginAtZero: true,
                ticks: {
                    backdropColor: 'transparent'
                },
                grid: {
                    color: 'rgba(0, 0, 0, 0.1)'
                }
            }
        }
    };

    return new Chart(ctx, {
        type: 'radar',
        data: data,
        options: { ...defaultOptions, ...options }
    });
}

/**
 * Destruye una gráfica de Chart.js
 * @param {Chart} chart - Instancia de Chart.js a destruir
 */
function destroyChart(chart) {
    if (chart) {
        chart.destroy();
    }
}

/**
 * Actualiza los datos de una gráfica existente
 * @param {Chart} chart - Instancia de Chart.js
 * @param {object} newData - Nuevos datos
 */
function updateChartData(chart, newData) {
    if (!chart) return;

    chart.data = newData;
    chart.update();
}

/**
 * Genera un array de colores basado en si el equipo es destacado
 * @param {Array} labels - Array de etiquetas (nombres de equipos)
 * @param {string} highlightTeam - Nombre del equipo a destacar
 * @returns {Array} - Array de colores
 */
function generateColors(labels, highlightTeam = 'Penafiel') {
    return labels.map(label =>
        label === highlightTeam ? COLORS.primary : COLORS.gray
    );
}

/**
 * Formatea datos para una gráfica de barras comparativa
 * @param {object} equipoData - Datos del equipo
 * @param {object} promedioData - Datos del promedio
 * @param {Array} metrics - Métricas a incluir
 * @returns {object} - Datos formateados para Chart.js
 */
function formatComparativaData(equipoData, promedioData, metrics) {
    const labels = metrics.map(m => m.label);
    const equipoValues = metrics.map(m => equipoData[m.key] || 0);
    const promedioValues = metrics.map(m => promedioData[m.key] || 0);

    return {
        labels: labels,
        datasets: [
            {
                label: 'Penafiel',
                data: equipoValues,
                backgroundColor: COLORS.primary,
                borderColor: COLORS.primary,
                borderWidth: 2
            },
            {
                label: 'Promedio Liga',
                data: promedioValues,
                backgroundColor: COLORS.success,
                borderColor: COLORS.success,
                borderWidth: 2
            }
        ]
    };
}

// Almacén global de gráficas activas
window.activeCharts = window.activeCharts || {};

/**
 * Registra una gráfica en el almacén global
 * @param {string} id - ID de la gráfica
 * @param {Chart} chart - Instancia de Chart.js
 */
function registerChart(id, chart) {
    // Destruir gráfica anterior si existe
    if (window.activeCharts[id]) {
        window.activeCharts[id].destroy();
    }
    window.activeCharts[id] = chart;
}

/**
 * Obtiene una gráfica del almacén global
 * @param {string} id - ID de la gráfica
 * @returns {Chart|null} - Instancia de Chart.js o null
 */
function getChart(id) {
    return window.activeCharts[id] || null;
}

// Exportar funciones
window.Charts = {
    createBarChart,
    createLineChart,
    createRadarChart,
    destroyChart,
    updateChartData,
    generateColors,
    formatComparativaData,
    registerChart,
    getChart,
    COLORS
};
