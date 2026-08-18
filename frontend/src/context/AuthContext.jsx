import { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check local storage for existing session
    const storedUser = localStorage.getItem('evaluator_user');
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch (e) {}
    }
    setLoading(false);
  }, []);

  const login = async (userId, role, password) => {
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, role, password })
      });
      
      if (!response.ok) throw new Error("Login failed");
      
      const data = await response.json();
      setUser(data);
      localStorage.setItem('evaluator_user', JSON.stringify(data));
      return data;
    } catch (e) {
      console.error(e);
      throw e;
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('evaluator_user');
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {!loading && children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
