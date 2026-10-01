import { useState, useEffect, useCallback } from 'react';
import { AuthContext } from './auth-context';

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(() => Boolean(localStorage.getItem('evaluator_token')));

  useEffect(() => {
    const storedToken = localStorage.getItem('evaluator_token');
    if (!storedToken) return;

    fetch('/api/auth/me', { headers: { Authorization: `Bearer ${storedToken}` } })
      .then(async (response) => {
        if (!response.ok) throw new Error('Stored session is no longer valid');
        const userData = await response.json();
        const userObj = {
          id: userData.id,
          username: userData.username || userData.id,
          name: userData.name,
          email: userData.email,
          role: userData.role
        };
        setToken(storedToken);
        setUser(userObj);
        localStorage.setItem('evaluator_user', JSON.stringify(userObj));
      })
      .catch(() => {
        localStorage.removeItem('evaluator_token');
        localStorage.removeItem('evaluator_user');
      })
      .finally(() => setLoading(false));
  }, []);

  // Authenticated fetch helper — attaches Bearer token automatically
  const authFetch = useCallback(async (url, options = {}) => {
    const currentToken = token || localStorage.getItem('evaluator_token');
    if (!currentToken) {
      throw new Error('No auth token available');
    }
    const headers = {
      ...options.headers,
      'Authorization': `Bearer ${currentToken}`,
    };
    // Set Content-Type to JSON for non-FormData bodies
    if (options.body && !(options.body instanceof FormData) && !(options.body instanceof URLSearchParams)) {
      headers['Content-Type'] = headers['Content-Type'] || 'application/json';
    }
    const response = await fetch(url, { ...options, headers });
    if (response.status === 401) {
      setToken(null);
      setUser(null);
      localStorage.removeItem('evaluator_token');
      localStorage.removeItem('evaluator_user');
    }
    return response;
  }, [token]);

  // Register a new user
  const register = async (username, email, password, role = 'student') => {
    try {
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password, role })
      });
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || 'Registration failed');
      }
      return await response.json();
    } catch (e) {
      console.error('Register error:', e);
      throw e;
    }
  };

  // Login via API
  const login = async (username, password, selectedRole = 'student') => {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: username,
        role: selectedRole,
        password
      })
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Login failed');
    }

    const userData = await response.json();
    const userObj = {
      id: userData.id,
      username: userData.username || userData.id,
      name: userData.name || userData.id.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
      email: userData.email,
      role: userData.role || selectedRole || 'student'
    };
    if (!userData.access_token) throw new Error('Authentication response did not include a session token');
    setUser(userObj);
    setToken(userData.access_token);
    localStorage.setItem('evaluator_token', userData.access_token);
    localStorage.setItem('evaluator_user', JSON.stringify(userObj));
    return userObj;
  };

  const switchRole = (newRole) => {
    if (!user) return;
    const updatedUser = { ...user, role: newRole };
    setUser(updatedUser);
    localStorage.setItem('evaluator_user', JSON.stringify(updatedUser));
  };

  const logout = async () => {
    const currentToken = token || localStorage.getItem('evaluator_token');
    try {
      if (currentToken) {
        await fetch('/api/auth/logout', {
          method: 'POST',
          headers: { Authorization: `Bearer ${currentToken}` }
        });
      }
    } finally {
      setUser(null);
      setToken(null);
      localStorage.removeItem('evaluator_user');
      localStorage.removeItem('evaluator_token');
    }
  };

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, switchRole, loading, authFetch }}>
      {!loading && children}
    </AuthContext.Provider>
  );
};

