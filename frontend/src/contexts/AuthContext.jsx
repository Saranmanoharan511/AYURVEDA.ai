/**
 * Authentication Context
 * 
 * This context provides authentication state and methods to the entire application.
 * It manages user login, logout, registration, and token storage.
 */

import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Check for existing token on mount
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      fetchUserProfile();
    } else {
      setLoading(false);
    }
  }, []);

  // Fetch user profile from backend
  const fetchUserProfile = async () => {
    try {
      const response = await authAPI.getProfile();
      setUser(response.data);
      setIsAuthenticated(true);
    } catch (error) {
      console.error('Failed to fetch user profile:', error);
      // Clear invalid tokens
      localStorage.removeItem('access_token');
      localStorage.removeItem('id_token');
      localStorage.removeItem('refresh_token');
      setUser(null);
      setIsAuthenticated(false);
    } finally {
      setLoading(false);
    }
  };

  // Register new user
  const register = async (userData) => {
    try {
      const response = await authAPI.register(userData);
      return { success: true, message: response.data.message };
    } catch (error) {
      return {
        success: false,
        message: error.response?.data?.detail || 'Registration failed'
      };
    }
  };

  // Login user
  const login = async (credentials) => {
    try {
      const response = await authAPI.login(credentials);
      
      // Store tokens
      localStorage.setItem('access_token', response.data.access_token);
      localStorage.setItem('id_token', response.data.id_token);
      localStorage.setItem('refresh_token', response.data.refresh_token);
      
      // Fetch user profile
      await fetchUserProfile();
      
      return { success: true };
    } catch (error) {
      return {
        success: false,
        message: error.response?.data?.detail || 'Login failed'
      };
    }
  };

  // Logout user
  const logout = async () => {
    try {
      await authAPI.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear tokens and user state
      localStorage.removeItem('access_token');
      localStorage.removeItem('id_token');
      localStorage.removeItem('refresh_token');
      setUser(null);
      setIsAuthenticated(false);
    }
  };

  const value = {
    user,
    loading,
    isAuthenticated,
    register,
    login,
    logout,
    fetchUserProfile,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
