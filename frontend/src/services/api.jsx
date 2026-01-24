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
export const pingServer = () => api.get('/status/heartbeat');
export const deviceInfor = () => api.get('/clientinfo');
export const grantAccess = (mac) => api.post(`/admin/grant_access/${mac}`);
export const revokeAccess = (mac) => api.post(`/admin/revoke_access/${mac}`);

// --

export const getNetworks = async () => api.get('/networks')
export const createNetwork = async (networkData) => api.post('/networks', networkData);
export const deleteNetwork = async (networkId) => api.delete(`/networks/delete/${networkId}`);

export const getUsers = async () => api.get('/users');
export const createUser = async (userData) => api.post('/users', userData);

export const getAccessCodes = async () => api.get('/access-codes');
export const generateAccessCode = async (codeData) => api.post('/access-codes', codeData);
export const deleteAccessCode = async (codeId) => api.delete(`/access-codes/delete/${codeId}`);
export const revokeAccessCode = async (codeId) => api.put(`/access-codes/revoke/${codeId}`);
export const get_qr_code = async (codeId) => api.get(`/access-codes/qr-code/${codeId}`);

export const getDevices = async () => api.get('/devices');
export const getDeviceHistory = async () => api.get('/devices/v2');

export const getReports = async () => api.get('/reports')

export const getSettings = async () => api.get('/settings')
export const updateSettings = async (settings) => api.put('/settings', settings)
export const getSettingsHistory = async () => api.get('/settings/history')


export default api;

