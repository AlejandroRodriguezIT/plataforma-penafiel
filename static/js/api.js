/**
 * Módulo de API para Plataforma FC Penafiel
 * Maneja todas las llamadas a los endpoints del backend
 */

// Configuración base de la API
const API_CONFIG = {
    baseURL: window.location.origin,
    timeout: 30000, // 30 segundos
    headers: {
        'Content-Type': 'application/json'
    }
};

/**
 * Función genérica para hacer llamadas a la API
 * @param {string} endpoint - Endpoint de la API (ej: '/api/rankings/global')
 * @param {object} options - Opciones adicionales para fetch
 * @returns {Promise} - Promesa con los datos de la respuesta
 */
async function apiCall(endpoint, options = {}) {
    const url = `${API_CONFIG.baseURL}${endpoint}`;

    const defaultOptions = {
        method: 'GET',
        headers: API_CONFIG.headers,
        ...options
    };

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.timeout);

        const response = await fetch(url, {
            ...defaultOptions,
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return data;
    } catch (error) {
        if (error.name === 'AbortError') {
            console.error('Request timeout:', endpoint);
            throw new Error('La petición ha tardado demasiado tiempo');
        }
        console.error('API call error:', endpoint, error);
        throw error;
    }
}

/**
 * API de Datos Físicos
 */
const FisicosAPI = {
    getBarrasColectivas: () => apiCall('/api/fisicos/barras-colectivas'),
    getBarrasIndividuales: () => apiCall('/api/fisicos/barras-individuales'),
    getEvolutivo: () => apiCall('/api/fisicos/evolutivo'),
    getPartidos: () => apiCall('/api/fisicos/partidos'),
    getScatterIndividual: (partido = null) => {
        const url = partido ? `/api/fisicos/scatter-individual?partido=${encodeURIComponent(partido)}` : '/api/fisicos/scatter-individual';
        return apiCall(url);
    }
};

/**
 * API de Microciclos
 */
const MicrociclosAPI = {
    getMicrociclos: () => apiCall('/api/microciclos/lista'),
    getMicrocicloEquipo: (jornada, tipoDistancia = 'Distancia_total') => {
        const url = `/api/microciclos/equipo?jornada=${encodeURIComponent(jornada)}&tipo_distancia=${encodeURIComponent(tipoDistancia)}`;
        return apiCall(url);
    }
};

/**
 * API de Rankings
 */
const RankingsAPI = {
    getRankingGlobal: () => apiCall('/api/rankings/global'),
    getGraficasVerticales: () => apiCall('/api/rankings/verticales')
};

/**
 * API de Estilo de Juego
 */
const EstiloJuegoAPI = {
    getScatterOfensivo: () => apiCall('/api/estilo-juego/scatter-ofensivo'),
    getScatterDefensivo: () => apiCall('/api/estilo-juego/scatter-defensivo')
};

/**
 * API de Estadísticos
 */
const EstadisticosAPI = {
    getResumen: () => apiCall('/api/estadisticos/resumen'),
    getComparativa: () => apiCall('/api/estadisticos/comparativa')
};

/**
 * API de Utilidades
 */
const UtilsAPI = {
    actualizarDatos: () => apiCall('/api/actualizar-datos'),
    healthCheck: () => apiCall('/api/health')
};

// Exportar APIs
window.API = {
    call: apiCall,
    Fisicos: FisicosAPI,
    Microciclos: MicrociclosAPI,
    Rankings: RankingsAPI,
    EstiloJuego: EstiloJuegoAPI,
    Estadisticos: EstadisticosAPI,
    Utils: UtilsAPI
};

// Funciones auxiliares para manejo común de respuestas

/**
 * Maneja la respuesta de una API que devuelve una imagen en base64
 * @param {string} containerId - ID del contenedor donde mostrar la imagen
 * @param {Promise} apiPromise - Promesa de la llamada a la API
 */
async function handleImageResponse(containerId, apiPromise) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Container ${containerId} not found`);
        return;
    }

    try {
        // Mostrar loading
        container.innerHTML = '<div class="chart-placeholder"><p>Cargando...</p></div>';

        const response = await apiPromise;

        if (response.status === 'success' && response.data && response.data.image) {
            container.innerHTML = `
                <img src="data:image/png;base64,${response.data.image}"
                     alt="Gráfica"
                     style="width: 100%; height: auto; display: block;">
            `;
        } else {
            throw new Error(response.message || 'Error al cargar la imagen');
        }
    } catch (error) {
        console.error('Error loading image:', error);
        container.innerHTML = `
            <div class="chart-placeholder">
                <p style="color: var(--color-danger);">
                    <i class="fas fa-exclamation-triangle"></i>
                    Error al cargar la gráfica
                </p>
            </div>
        `;
        if (window.PenafielPlatform) {
            window.PenafielPlatform.showAlert('Error al cargar la gráfica', 'error');
        }
    }
}

/**
 * Maneja la respuesta de una API que devuelve datos JSON
 * @param {Promise} apiPromise - Promesa de la llamada a la API
 * @returns {Object|null} - Datos de la respuesta o null si hay error
 */
async function handleDataResponse(apiPromise) {
    try {
        const response = await apiPromise;

        if (response.status === 'success') {
            return response.data || response;
        } else {
            throw new Error(response.message || 'Error al obtener datos');
        }
    } catch (error) {
        console.error('Error loading data:', error);
        if (window.PenafielPlatform) {
            window.PenafielPlatform.showAlert('Error al cargar datos', 'error');
        }
        return null;
    }
}

// Exportar funciones auxiliares
window.API.handleImageResponse = handleImageResponse;
window.API.handleDataResponse = handleDataResponse;
