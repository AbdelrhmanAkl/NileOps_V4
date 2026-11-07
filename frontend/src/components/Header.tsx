import React from "react";
import { useLanguage } from "../contexts/LanguageContext";
import { useAuth } from "../contexts/AuthContext";

export const Header: React.FC = () => {
  const { language, setLanguage, isArabic } = useLanguage();
  const { activePortal, setActivePortal, user, loginAsDemoUser, logout } = useAuth();

  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-50 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-4 rtl:space-x-reverse">
          <div className="flex items-center space-x-2 rtl:space-x-reverse">
            <div className="w-9 h-9 rounded-lg bg-nile-700 flex items-center justify-center text-white font-bold text-lg shadow-sm">
              N
            </div>
            <div>
              <span className="text-xl font-bold tracking-tight text-gray-900 block leading-tight">
                {isArabic ? "بنك النيل للعمليات التجريبي" : "NileOps Demo Bank"}
              </span>
              <span className="text-xs text-gray-500 font-medium">
                {isArabic ? "منصة العمليات المصرفية الذكية" : "Digital Banking Operations Platform"}
              </span>
            </div>
          </div>

          {/* Portal Switcher Tabs */}
          <nav className="flex space-x-1 rtl:space-x-reverse bg-gray-100 p-1 rounded-lg ml-6">
            <button
              onClick={() => setActivePortal("customer")}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
                activePortal === "customer"
                  ? "bg-white text-nile-800 shadow-sm"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              {isArabic ? "بوابة العملاء" : "Customer Portal"}
            </button>
            <button
              onClick={() => setActivePortal("employee")}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
                activePortal === "employee"
                  ? "bg-white text-nile-800 shadow-sm"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              {isArabic ? "بوابة الموظفين والعمليات" : "Employee Portal"}
            </button>
          </nav>
        </div>

        {/* Right side controls: Language toggle + User badge */}
        <div className="flex items-center space-x-3 rtl:space-x-reverse">
          <button
            onClick={() => setLanguage(language === "en" ? "ar" : "en")}
            className="px-2.5 py-1 text-xs font-medium border border-gray-300 rounded hover:bg-gray-50 transition"
          >
            {language === "en" ? "عربي (AR)" : "English (EN)"}
          </button>

          {user ? (
            <div className="flex items-center space-x-2 rtl:space-x-reverse text-xs">
              <span className="bg-green-100 text-green-800 px-2 py-0.5 rounded font-medium">
                {user.fullName} ({user.role})
              </span>
              <button
                onClick={logout}
                className="text-gray-500 hover:text-red-600 font-medium"
              >
                {isArabic ? "خروج" : "Logout"}
              </button>
            </div>
          ) : (
            <button
              onClick={() => loginAsDemoUser(activePortal)}
              className="px-3 py-1.5 bg-nile-700 text-white text-xs font-semibold rounded hover:bg-nile-800 shadow-sm transition"
            >
              {isArabic ? "تسجيل تجريبي" : "Demo Login"}
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
