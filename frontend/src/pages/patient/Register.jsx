/**
 * Patient Registration Page
 * 
 * This component provides a registration form for new patients.
 * It handles form validation and submission to the backend API.
 */

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

const PatientRegister = () => {
  const navigate = useNavigate();
  const { register } = useAuth();
  
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    given_name: '',
    family_name: '',
  });
  
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    // Clear error for this field
    setErrors(prev => ({ ...prev, [name]: '' }));
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email is invalid';
    }
    
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    }
    
    if (!formData.confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your password';
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }
    
    if (!formData.given_name) {
      newErrors.given_name = 'First name is required';
    }
    
    if (!formData.family_name) {
      newErrors.family_name = 'Last name is required';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setLoading(true);
    setMessage({ type: '', text: '' });
    
    const result = await register({
      email: formData.email,
      password: formData.password,
      given_name: formData.given_name,
      family_name: formData.family_name,
      role: 'patient',
    });
    
    setLoading(false);
    
    if (result.success) {
      setMessage({ type: 'success', text: result.message });
      // Redirect to login after successful registration
      setTimeout(() => {
        navigate('/patient/login');
      }, 2000);
    } else {
      setMessage({ type: 'error', text: result.message });
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-teal-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-lg shadow-xl p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800">Patient Registration</h1>
          <p className="text-gray-600 mt-2">Create your account to get started</p>
        </div>

        {message.text && (
          <div className={`mb-4 p-4 rounded-md ${
            message.type === 'success' 
              ? 'bg-green-50 text-green-800 border border-green-200' 
              : 'bg-red-50 text-red-800 border border-red-200'
          }`}>
            {message.text}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
              Email Address
            </label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className={`w-full px-4 py-3 border rounded-md focus:outline-none focus:ring-2 focus:ring-teal-500 ${
                errors.email ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="you@example.com"
            />
            {errors.email && <p className="mt-1 text-sm text-red-600">{errors.email}</p>}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="given_name" className="block text-sm font-medium text-gray-700 mb-2">
                First Name
              </label>
              <input
                type="text"
                id="given_name"
                name="given_name"
                value={formData.given_name}
                onChange={handleChange}
                className={`w-full px-4 py-3 border rounded-md focus:outline-none focus:ring-2 focus:ring-teal-500 ${
                  errors.given_name ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="John"
              />
              {errors.given_name && <p className="mt-1 text-sm text-red-600">{errors.given_name}</p>}
            </div>

            <div>
              <label htmlFor="family_name" className="block text-sm font-medium text-gray-700 mb-2">
                Last Name
              </label>
              <input
                type="text"
                id="family_name"
                name="family_name"
                value={formData.family_name}
                onChange={handleChange}
                className={`w-full px-4 py-3 border rounded-md focus:outline-none focus:ring-2 focus:ring-teal-500 ${
                  errors.family_name ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="Doe"
              />
              {errors.family_name && <p className="mt-1 text-sm text-red-600">{errors.family_name}</p>}
            </div>
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
              Password
            </label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              className={`w-full px-4 py-3 border rounded-md focus:outline-none focus:ring-2 focus:ring-teal-500 ${
                errors.password ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="••••••••"
            />
            {errors.password && <p className="mt-1 text-sm text-red-600">{errors.password}</p>}
          </div>

          <div>
            <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-2">
              Confirm Password
            </label>
            <input
              type="password"
              id="confirmPassword"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              className={`w-full px-4 py-3 border rounded-md focus:outline-none focus:ring-2 focus:ring-teal-500 ${
                errors.confirmPassword ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="••••••••"
            />
            {errors.confirmPassword && <p className="mt-1 text-sm text-red-600">{errors.confirmPassword}</p>}
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-teal-600 text-white py-3 px-4 rounded-md hover:bg-teal-700 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Creating Account...' : 'Create Account'}
          </button>
        </form>

        <p className="mt-6 text-center text-gray-600">
          Already have an account?{' '}
          <Link to="/patient/login" className="text-teal-600 hover:text-teal-700 font-medium">
            Sign in here
          </Link>
        </p>
      </div>
    </div>
  );
};

export default PatientRegister;
