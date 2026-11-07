import React, { createContext, useContext, useState, useEffect } from "react";
import { UserProfile, PortalType } from "../types";
import { apiLogin, apiSeedDemo } from "../api/client";

interface AuthContextType {
  user: UserProfile | null;
  token: string | null;
  activePortal: PortalType;
  setActivePortal: (portal: PortalType) => void;
  isAuthenticated: boolean;
  loginWithCredentials: (email: string, password: string) => Promise<void>;
  quickLogin: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
  error: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem("nileops_token"));
  const [user, setUser] = useState<UserProfile | null>(() => {
    const saved = localStorage.getItem("nileops_user");
    return saved ? JSON.parse(saved) : null;
  });
  const [activePortal, setActivePortal] = useState<PortalType>("customer");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Auto seed demo data on first load if necessary
  useEffect(() => {
    apiSeedDemo().catch(() => { });
  }, []);

  const loginWithCredentials = async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await apiLogin(email, password);
      setToken(data.access_token);
      setUser(data.user);
      localStorage.setItem("nileops_token", data.access_token);
      localStorage.setItem("nileops_user", JSON.stringify(data.user));

      // Switch portal automatically based on user type
      if (data.user.user_type === "employee") {
        setActivePortal("employee");
      } else {
        setActivePortal("customer");
      }
    } catch (err: any) {
      setError(err.message || "Login failed");
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const quickLogin = async (email: string, password: string) => {
    return loginWithCredentials(email, password);
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem("nileops_token");
    localStorage.removeItem("nileops_user");
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        activePortal,
        setActivePortal,
        isAuthenticated: !!token && !!user,
        loginWithCredentials,
        quickLogin,
        logout,
        isLoading,
        error,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
