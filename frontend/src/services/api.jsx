import axios from 'axios';

// Create instance with baseURL that will work in both dev and production
const api = axios.create({
    baseURL: process.env.NODE_ENV === 'development'
        ? 'http://127.0.0.1:8001/api'  // Will use proxy in development
        : window.location.origin,  // Uses same origin in production
    timeout: 10000,
});

// Response interceptor for error handling
api.interceptors.response.use(
    response => response,
    error => {
        if (!error.response) {
            // Network error - backend unreachable
            return Promise.reject({
                message: 'Network error: Unable to connect to server',
                status: 'network_error',
                originalError: error
            });
        }
        return Promise.reject(error);
    }
);

export const connectToNetwork = () => api.post('/connect');
export const getStatus = () => api.get('/status');
export const deviceInfor = () => api.get('/clientinfo');
export const grantAccess = (mac) => api.post(`/admin/grant_access/${mac}`);
export const revokeAccess = (mac) => api.post(`//admin/revoke_access/${mac}`);

// --

export const getNetworks = async () => api.get('/networks')

export const createNetwork = async (networkData) => api.post('/networks', networkData);

export const getUsers = async () => api.get('/users');

export const createUser = async (userData) => api.post('/users', userData);

export const generateAccessCode = async (codeData) => api.get('access-codes', codeData);

export const getDeviceHistory = async () => api.get('/devices/v2');

export const getReports = async () => api.get('/reports')

export const getSettings = async () => api.get('/settings')

export const updateSettings = async (settings) => api.put('/settings', settings)

export const getSettingsHistory = async () => api.get('/settings/history')


export default api;

