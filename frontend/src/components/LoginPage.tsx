import React, { useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import { useLanguage } from "../contexts/LanguageContext";

export const LoginPage: React.FC = () => {
  const { loginWithCredentials, quickLogin, isLoading, error } = useAuth();
  const { isArabic } = useLanguage();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    try {
      await loginWithCredentials(email, password);
    } catch (err: any) {
      setLocalError(err.message || "Login failed");
    }
  };

  const demoAccounts = [
    {
      name: isArabic ? "أحمد منصور (عميل تجزئة)" : "Ahmed Mansour (Retail Customer)",
      roleBadge: isArabic ? "عميل" : "Customer",
      roleColor: "bg-blue-100 text-blue-800 border-blue-200",
      email: "customer1@nileops.demo",
      pass: "Customer2026!",
      portal: "Customer Portal",
    },
    {
      name: isArabic ? "سارة السيد (مسؤول عمليات)" : "Sarah El-Sayed (Operations Officer)",
      roleBadge: isArabic ? "عمليات" : "Operations",
      roleColor: "bg-amber-100 text-amber-800 border-amber-200",
      email: "ops@nileops.demo",
      pass: "NileOps2026!",
      portal: "Employee Portal",
    },
    {
      name: isArabic ? "طارق الغندور (خدمة عملاء)" : "Tarek El-Ghandour (Customer Service)",
      roleBadge: isArabic ? "خدمة عملاء" : "Customer Service",
      roleColor: "bg-emerald-100 text-emerald-800 border-emerald-200",
      email: "cs@nileops.demo",
      pass: "NileOps2026!",
      portal: "Employee Portal",
    },
    {
      name: isArabic ? "نورهان كامل (مراجعة الالتزام ومكافحة غسل الأموال)" : "Nourhan Kamel (Compliance Reviewer)",
      roleBadge: isArabic ? "مراجعة التزام" : "Compliance",
      roleColor: "bg-purple-100 text-purple-800 border-purple-200",
      email: "compliance@nileops.demo",
      pass: "NileOps2026!",
      portal: "Employee Portal",
    },
    {
      name: isArabic ? "شريف عثمان (مدير فرع)" : "Sherif Osman (Branch Manager)",
      roleBadge: isArabic ? "مدير فرع" : "Branch Manager",
      roleColor: "bg-indigo-100 text-indigo-800 border-indigo-200",
      email: "manager@nileops.demo",
      pass: "NileOps2026!",
      portal: "Employee Portal",
    },
    {
      name: isArabic ? "محمود فاروق (مسؤول النظام)" : "Mahmoud Farouk (Administrator)",
      roleBadge: isArabic ? "مسؤول نظام" : "Admin",
      roleColor: "bg-rose-100 text-rose-800 border-rose-200",
      email: "admin@nileops.demo",
      pass: "NileOps2026!",
      portal: "Employee Portal",
    },
  ];

  return (
    <div className="max-w-4xl mx-auto px-4 py-12">
      {/* Simulation Disclaimer Banner */}
      <div className="bg-amber-50 border-l-4 border-amber-500 p-4 rounded-r-lg mb-8 shadow-sm">
        <div className="flex">
          <div className="flex-shrink-0 text-amber-600 font-bold text-lg">⚠️</div>
          <div className="ml-3 rtl:mr-3 rtl:ml-0">
            <h3 className="text-sm font-bold text-amber-800">
              {isArabic ? "تنبيه بيئة محاكاة مصرفية افتراضية" : "Fictional Banking Simulation Notice"}
            </h3>
            <p className="text-xs text-amber-700 mt-1">
              {isArabic
                ? "هذا التطبيق مخصص لمحاكاة العمليات المصرفية الرقمية وتجربة خدمة العملاء باسم 'بنك النيل للعمليات التجريبي'. جميع الحسابات والمعاملات والوثائق اصطناعية تماماً ولا تمثل أي بنك حقيقي."
                : "This platform simulates digital banking operations under 'NileOps Demo Bank'. All customers, accounts, complaints, and transactions are strictly synthetic."}
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-start">
        {/* Login Form */}
        <div className="bg-white p-8 rounded-xl border border-gray-200 shadow-md">
          <div className="mb-6">
            <h2 className="text-xl font-bold text-gray-900">
              {isArabic ? "تسجيل الدخول إلى النظام المصرفي" : "Sign In to NileOps Demo Bank"}
            </h2>
            <p className="text-xs text-gray-500 mt-1">
              {isArabic
                ? "أدخل بيانات حسابك أو اختر أحد الحسابات التجريبية الجاهزة"
                : "Enter credentials or click any demo role below for 1-click access"}
            </p>
          </div>

          {(error || localError) && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-lg">
              {localError || error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">
                {isArabic ? "البريد الإلكتروني" : "Email Address"}
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="ops@nileops.demo"
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-nile-600"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">
                {isArabic ? "كلمة المرور" : "Password"}
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-nile-600"
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-2.5 bg-nile-700 hover:bg-nile-800 text-white font-semibold text-sm rounded-lg shadow transition disabled:opacity-50"
            >
              {isLoading
                ? isArabic
                  ? "جاري التحقق..."
                  : "Signing In..."
                : isArabic
                ? "دخول"
                : "Sign In"}
            </button>
          </form>
        </div>

        {/* 1-Click Quick Demo Switcher */}
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-md space-y-4">
          <div>
            <h3 className="text-base font-bold text-gray-900">
              {isArabic ? "الحسابات التجريبية المعتمدة (دخول سريع)" : "Quick Demo Access (1-Click)"}
            </h3>
            <p className="text-xs text-gray-500 mt-0.5">
              {isArabic
                ? "اختر أي دور لتسجيل الدخول الفوري وتجربة واجهته وصلاحياته"
                : "Select any role to simulate its portal permissions and workflows"}
            </p>
          </div>

          <div className="space-y-2.5">
            {demoAccounts.map((acc, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => quickLogin(acc.email, acc.pass)}
                disabled={isLoading}
                className="w-full text-left rtl:text-right p-3 rounded-lg border border-gray-200 hover:border-nile-600 hover:bg-nile-50/50 transition flex items-center justify-between group"
              >
                <div>
                  <div className="flex items-center space-x-2 rtl:space-x-reverse mb-0.5">
                    <span className="text-xs font-bold text-gray-900 group-hover:text-nile-800">
                      {acc.name}
                    </span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono border ${acc.roleColor}`}>
                      {acc.roleBadge}
                    </span>
                  </div>
                  <span className="text-[11px] text-gray-500 font-mono block">
                    {acc.email}
                  </span>
                </div>
                <span className="text-xs font-semibold text-nile-700 opacity-0 group-hover:opacity-100 transition">
                  {isArabic ? "دخول ←" : "Login →"}
                </span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

