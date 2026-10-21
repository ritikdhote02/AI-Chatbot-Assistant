import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api, setStoredToken } from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchCurrentUser = useCallback(async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setUser(null);
      setLoading(false);
      return null;
    }

    try {
      const userData = await api.auth.getMe();
      setUser(userData);
      return userData;
    } catch (err) {
      // If token is expired or invalid, remove it
      if (err.status === 401) {
        setStoredToken(null);
        setUser(null);
      }
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCurrentUser();
  }, [fetchCurrentUser]);

  const login = async (email, password) => {
    const response = await api.auth.login({ email, password });
    setStoredToken(response.access_token);
    const userData = await api.auth.getMe();
    setUser(userData);
    return userData;
  };

  const register = async (name, email, password) => {
    return await api.auth.register({ name, email, password });
  };

  const logout = () => {
    setStoredToken(null);
    setUser(null);
  };

  const value = {
    user,
    loading,
    isAuthenticated: !!user,
    login,
    register,
    logout,
    refreshUser: fetchCurrentUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
