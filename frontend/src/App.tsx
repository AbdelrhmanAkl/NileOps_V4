import React, { useEffect, useState } from "react";
import { LanguageProvider } from "./contexts/LanguageContext";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { Header } from "./components/Header";
import { LoginPage } from "./components/LoginPage";
import { CustomerPortal } from "./portals/customer/CustomerPortal";
import { EmployeePortal } from "./portals/employee/EmployeePortal";
import { fetchHealth } from "./api/client";

const MainContent: React.FC = () => {
  const { isAuthenticated, activePortal } = useAuth();

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  return (
    <main className="flex-1">
      {activePortal === "customer" ? <CustomerPortal /> : <EmployeePortal />}
    </main>
  );
};

export const App: React.FC = () => {
  const [dbName, setDbName] = useState<string>("PostgreSQL 16");

  useEffect(() => {
    let mounted = true;
    fetchHealth()
      .then((data) => {
        if (mounted && data?.database) {
          setDbName(data.database);
        }
      })
      .catch(() => {
        // Fallback gracefully if probe fails
      });
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <LanguageProvider>
      <AuthProvider>
        <div className="min-h-screen flex flex-col bg-gray-50 text-gray-900 font-sans antialiased">
          <Header />
          <MainContent />
          <footer className="bg-white border-t border-gray-200 py-4 mt-auto">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-xs text-gray-500 flex flex-col sm:flex-row items-center justify-between gap-2">
              <span>
                <strong>NileOps Demo Bank</strong> — Fictional Digital Banking Operations Platform MVP
              </span>
              <span className="text-[11px] text-gray-400">
                Native Windows Runtime ({dbName} + FastAPI + React 18 / Vite / Tailwind)
              </span>
            </div>
          </footer>
        </div>
      </AuthProvider>
    </LanguageProvider>
  );
};

export default App;
