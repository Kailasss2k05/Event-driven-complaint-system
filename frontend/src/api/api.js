import axios from 'axios';

// Main API Instance
export const api = axios.create({
    baseURL: 'http://localhost:8000',
});

// Notifications API Instance
export const notificationApi = axios.create({
    baseURL: 'http://localhost:8002',
});

// Interceptor to add Authorization header
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

notificationApi.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);
