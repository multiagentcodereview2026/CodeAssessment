import { createContext, useContext, useState, useEffect } from 'react';
import { apiFetch, apiJson } from '../services/api';
const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);
  const logout = () => {
    localStorage.removeItem('evaluator_token');
    localStorage.removeItem('evaluator_user');
    setUser(null); setToken(null);
  };
  useEffect(() => {
    let active = true;
    window.addEventListener('session-expired', logout);
    const saved = localStorage.getItem('evaluator_token');
    if (saved) {
      apiJson('/api/auth/me').then(profile => {
        if (active) { setToken(saved); setUser(profile); }
      }).catch(() => { if (active) logout(); }).finally(() => { if (active) setLoading(false); });
    } else setLoading(false);
    return () => { active = false; window.removeEventListener('session-expired', logout); };
  }, []);
  const login = async (username, password, selectedRole) => {
    const response = await fetch('/api/auth/login', { method: 'POST', body: new URLSearchParams({ username, password }) });
    const data = await response.json();
    if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Unable to sign in');
    localStorage.setItem('evaluator_token', data.access_token);
    try {
      const profile = await apiJson('/api/auth/me');
      if (profile.role !== selectedRole) throw new Error(`This account is registered as ${profile.role}. Select that role to sign in.`);
      setToken(data.access_token); setUser(profile);
      return profile;
    } catch (error) { logout(); throw error; }
  };
  const register = (username, email, password, role) => apiJson('/api/auth/register', {
    method: 'POST', body: JSON.stringify({ username, email, password, role })
  });
  return <AuthContext.Provider value={{ user, token, loading, login, register, logout, authFetch: apiFetch }}>
    {loading ? <div className="p-8 text-sm text-slate-600">Loading your account...</div> : children}
  </AuthContext.Provider>;
};
export const useAuth = () => useContext(AuthContext);
