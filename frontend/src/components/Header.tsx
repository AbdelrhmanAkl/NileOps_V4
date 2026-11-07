import React from "react";
import { useLanguage } from "../contexts/LanguageContext";
import { useAuth } from "../contexts/AuthContext";

export const Header: React.FC = () => {
  const { language, setLanguage, isArabic } = useLanguage();
  const { activePortal, setActivePortal, user, isAuthenticated, logout } = useAuth();

  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-40 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-4 rtl:space-x-reverse">
          <div className="flex items-center space-x-2.5 rtl:space-x-reverse">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-nile-800 to-nile-600 flex items-center justify-center text-white font-black text-lg shadow-sm">
              N
            </div>
            <div>
              <span className="text-lg font-black tracking-tight text-gray-900 block leading-tight">
                {isArabic ? "بنك النيل التجريبي" : "NileOps Demo Bank"}
              </span>
              <span className="text-[10px] text-gray-400 font-semibold uppercase tracking-wider block">
                {isArabic ? "محاكاة العمليات المصرفية الرقمية" : "Digital Banking Simulation"}
              </span>
            </div>
          </div>

          {/* Portal Switcher (Visible when user has permission or for demo overview) */}
          {isAuthenticated && (
            <nav className="hidden sm:flex space-x-1 rtl:space-x-reverse bg-gray-100 p-1 rounded-lg ml-6 rtl:ml-0 rtl:mr-6">
              <button
                onClick={() => setActivePortal("customer")}
                className={`px-3 py-1.5 text-xs font-semibold rounded-md transition ${
                  activePortal === "customer"
                    ? "bg-white text-nile-900 shadow-sm"
                    : "text-gray-600 hover:text-gray-900"
                }`}
              >
                {isArabic ? "بوابة العملاء" : "Customer Portal"}
              </button>
              {user?.user_type === "employee" && (
                <button
                  onClick={() => setActivePortal("employee")}
                  className={`px-3 py-1.5 text-xs font-semibold rounded-md transition ${
                    activePortal === "employee"
                      ? "bg-white text-nile-900 shadow-sm"
                      : "text-gray-600 hover:text-gray-900"
                  }`}
                >
                  {isArabic ? "بوابة العمليات" : "Employee Portal"}
                </button>
              )}
            </nav>
          )}
        </div>

        {/* Right Controls */}
        <div className="flex items-center space-x-3 rtl:space-x-reverse">
          {/* Language Switcher */}
          <button
            onClick={() => setLanguage(language === "en" ? "ar" : "en")}
            className="px-2.5 py-1 text-xs font-semibold border border-gray-300 rounded-md hover:bg-gray-50 text-gray-700 transition"
          >
            {language === "en" ? "العربية (RTL)" : "English (LTR)"}
          </button>

          {/* User Profile & Logout */}
          {isAuthenticated && user ? (
            <div className="flex items-center space-x-2.5 rtl:space-x-reverse pl-2 rtl:pl-0 rtl:pr-2 border-l rtl:border-l-0 rtl:border-r border-gray-200">
              <div className="text-right rtl:text-left hidden sm:block">
                <span className="text-xs font-bold text-gray-900 block leading-tight">
                  {user.full_name}
                </span>
                <span className="text-[10px] text-gray-500 font-mono">
                  {user.role}
                </span>
              </div>
              <button
                onClick={logout}
                className="px-2.5 py-1 text-xs font-bold text-rose-700 bg-rose-50 hover:bg-rose-100 border border-rose-200 rounded-md transition"
              >
                {isArabic ? "خروج" : "Logout"}
              </button>
            </div>
          ) : null}
        </div>
      </div>
    </header>
  );
};
