/**
 * Protected Route Component
 * 
 * This component wraps routes that require authentication.
 * It checks if the user is authenticated and has the required role
 * before allowing access to the protected route.
 * 
 * Note: Frontend route guards are for UX only. The backend is the
 * final authority for authorization.
 */

import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const ProtectedRoute = ({ children, allowedRoles = [] }) => {
  const { isAuthenticated, user, loading } = useAuth();
  const location = useLocation();

  // Show loading state while checking authentication
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-600"></div>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    // Redirect to appropriate login based on the route being accessed
    let loginPath = '/patient/login';
    if (location.pathname.startsWith('/admin')) {
      loginPath = '/admin/login';
    } else if (location.pathname.startsWith('/doctor')) {
      loginPath = '/doctor/login';
    }
    return <Navigate to={loginPath} state={{ from: location }} replace />;
  }

  // Check role requirements
  if (allowedRoles.length > 0 && user) {
    const userRole = user.role?.toLowerCase();
    const hasRequiredRole = allowedRoles.some(role => 
      role.toLowerCase() === userRole
    );

    if (!hasRequiredRole) {
      // Redirect to appropriate dashboard based on user's role
      if (userRole === 'patient') {
        return <Navigate to="/patient/dashboard" replace />;
      } else if (userRole === 'doctor') {
        return <Navigate to="/doctor/dashboard" replace />;
      } else if (userRole === 'admin') {
        return <Navigate to="/admin/dashboard" replace />;
      }
      return <Navigate to="/" replace />;
    }
  }

  // User is authenticated and has required role
  return children;
};

export default ProtectedRoute;
