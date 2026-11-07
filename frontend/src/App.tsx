import React from "react";
import { LanguageProvider } from "./contexts/LanguageContext";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { Header } from "./components/Header";
import { CustomerPortal } from "./portals/customer/CustomerPortal";
import { EmployeePortal } from "./portals/employee/EmployeePortal";

const PortalSwitcher: React.FC = () => {
  const { activePortal } = useAuth();

  return (
    <main className="flex-1">
      {activePortal === "customer" ? <CustomerPortal /> : <EmployeePortal />}
    </main>
  );
};

export const App: React.FC = () => {
  return (
    <LanguageProvider>
      <AuthProvider>
        <div className="min-h-screen flex flex-col bg-gray-50 text-gray-900 font-sans">
          <Header />
          <PortalSwitcher />
          <footer className="bg-white border-t border-gray-200 py-4 mt-auto">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-xs text-gray-500">
              NileOps Demo Bank — Intelligent Digital Banking Operations Platform Simulation (Phase 1 Scaffolding)
            </div>
          </footer>
        </div>
      </AuthProvider>
    </LanguageProvider>
  );
};

export default App;
