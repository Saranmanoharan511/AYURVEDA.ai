/**
 * API Client Service
 * 
 * This service provides a centralized axios instance for making API requests
 * to the FastAPI backend. It handles JWT token injection, request/response
 * interceptors, and error handling.
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Create axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - Add JWT token to requests
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - Handle token refresh and errors
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    // If 401 error and not already retrying
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        // Attempt to refresh token
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
            refresh_token: refreshToken,
          });

          const { access_token, id_token } = response.data;

          // Store new tokens
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('id_token', id_token);

          // Retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return apiClient(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed - clear tokens and redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('id_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// Authentication API
export const authAPI = {
  register: (userData) => apiClient.post('/api/v1/auth/register', userData),
  login: (credentials) => apiClient.post('/api/v1/auth/login', credentials),
  logout: () => apiClient.post('/api/v1/auth/logout'),
  getProfile: () => apiClient.get('/api/v1/auth/me'),
  refreshToken: (refreshToken) => apiClient.post('/api/v1/auth/refresh', { refresh_token: refreshToken }),
};

// Health API
export const healthAPI = {
  check: () => apiClient.get('/api/v1/health'),
};

// Export both named exports and default
export { apiClient };
export default apiClient;
