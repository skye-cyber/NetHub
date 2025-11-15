import axios from 'axios';

// Create instance with baseURL that will work in both dev and production
const api = axios.create({
    baseURL: process.env.NODE_ENV === 'development'
    ? '/api'  // Will use proxy in development
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
export const grantAccess = (mac) => api.post(`/admin/grant_access/${mac}`);
export const revokeAccess = (mac) => api.post(`/admin/revoke_access/${mac}`);

export default api;

