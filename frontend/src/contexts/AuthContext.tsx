import React, { createContext, useContext, useState } from "react";
import { UserProfile, PortalType } from "../types";

interface AuthContextType {
  user: UserProfile | null;
  activePortal: PortalType;
  setActivePortal: (portal: PortalType) => void;
  isAuthenticated: boolean;
  loginAsDemoUser: (portal: PortalType) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [activePortal, setActivePortal] = useState<PortalType>("customer");
  const [user, setUser] = useState<UserProfile | null>(null);

  const loginAsDemoUser = (portal: PortalType) => {
    setActivePortal(portal);
    if (portal === "customer") {
      setUser({
        id: "demo-cust-001",
        email: "retail.customer@nileops.demo",
        fullName: "Tariq Mansour",
        role: "customer_service", // Default public view
        portal: "customer",
      });
    } else {
      setUser({
        id: "demo-staff-001",
        email: "staff.ops@nileops.demo",
        fullName: "Sarah El-Sayed",
        role: "operations_officer",
        portal: "employee",
      });
    }
  };

  const logout = () => {
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        activePortal,
        setActivePortal,
        isAuthenticated: !!user,
        loginAsDemoUser,
        logout,
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
