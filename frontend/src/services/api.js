import axios from 'axios';

// Configure Axios with base URL and credentials
const api = axios.create({
    baseURL: '',
    withCredentials: true,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Authentication
export const login = async (usuario, password) => {
    const response = await api.post('/api/login', { usuario, password });
    return response.data;
};

export const logout = async () => {
    const response = await api.post('/api/logout');
    return response.data;
};

export const getSession = async () => {
    const response = await api.get('/api/session');
    return response.data;
};

// Line Selection and Validation Flow
export const getLineasDisponibles = async () => {
    const response = await api.get('/api/lineas/disponibles');
    return response.data;
};

export const seleccionarLinea = async (linea) => {
    const response = await api.post('/api/seleccionar-linea', { linea });
    return response.data;
};

export const validarMensaje = async (mensaje_id, accion, comentario = '') => {
    const response = await api.post('/api/validar', { mensaje_id, accion, comentario });
    return response.data;
};

export const getMensajesAsignados = async () => {
    const response = await api.get('/api/mensajes/asignados');
    return response.data;
};

// Error Management (Admin/Ariel Only)
export const getErrores = async () => {
    const response = await api.get('/api/errores');
    return response.data;
};

export const desbloquearMensaje = async (mensaje_id) => {
    const response = await api.post('/api/errores/desbloquear', { mensaje_id });
    return response.data;
};

// Scraping VPN (legacy — requests-based, no funciona con GlobalProtect)
export const scrapingSanMartin = async (vpn_user, vpn_password, fecha_inicio, fecha_fin) => {
    const response = await api.post('/api/scraping/san-martin', {
        vpn_user,
        vpn_password,
        fecha_inicio,
        fecha_fin,
    });
    return response.data;
};

// Scraping Híbrido (Playwright: login auto + extracción CDP)
export const scrapingIniciar = async (vpn_user, vpn_password) => {
    const response = await api.post('/api/scraping/iniciar', { vpn_user, vpn_password });
    return response.data;
};

export const scrapingExtraer = async () => {
    const response = await api.post('/api/scraping/extraer');
    return response.data;
};

export default api;
