import React, { useState, useEffect } from "react";
import { useLanguage } from "../../contexts/LanguageContext";
import { fetchHealth } from "../../api/client";
import { HealthCheckResponse } from "../../types";

export const CustomerPortal: React.FC = () => {
  const { isArabic } = useLanguage();
  const [health, setHealth] = useState<HealthCheckResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchHealth()
      .then(setHealth)
      .catch((err) => setError(err.message));
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-nile-700 to-nile-900 rounded-xl p-6 text-white shadow-md">
        <h1 className="text-2xl font-bold mb-2">
          {isArabic ? "مرحباً بكم في بوابة عملاء بنك النيل التجريبي" : "Welcome to NileOps Demo Bank — Customer Portal"}
        </h1>
        <p className="text-nile-100 text-sm max-w-3xl leading-relaxed">
          {isArabic
            ? "استكشف خدمات الحسابات المصرفية، القروض، والبطاقات، وتواصل مع المساعد الذكي للإجابة عن جميع استفساراتك وفقاً لسياسات البنك المعتمدة."
            : "Explore retail banking services, products, loan inquiries, and conversational customer support backed by our verified policy knowledge base."}
        </p>
      </div>

      {/* Backend Status Card (Phase 1 Verification) */}
      <div className="bg-white border border-gray-200 rounded-lg p-5 shadow-sm">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
          {isArabic ? "حالة الخدمة الخلفية (Phase 1)" : "Backend Integration Status (Phase 1)"}
        </h2>
        {health ? (
          <div className="flex items-center space-x-3 rtl:space-x-reverse text-sm">
            <span className="inline-block w-3 h-3 rounded-full bg-green-500 animate-pulse"></span>
            <span className="font-medium text-gray-800">
              {health.service} v{health.version} —{" "}
              <strong className="text-green-700 uppercase">{health.status}</strong>
            </span>
          </div>
        ) : error ? (
          <div className="text-sm text-red-600 font-medium">
            {isArabic ? "تعذر الاتصال بالخادم:" : "Backend unreachable:"} {error}
          </div>
        ) : (
          <div className="text-sm text-gray-500">{isArabic ? "جاري التحقق من الخادم..." : "Checking backend health..."}</div>
        )}
      </div>

      {/* Feature Cards Grid (Placeholders for upcoming phases) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white border border-gray-200 rounded-lg p-5 shadow-sm hover:shadow transition">
          <div className="w-10 h-10 rounded-lg bg-blue-100 text-blue-800 flex items-center justify-center font-bold mb-3">
            Q&A
          </div>
          <h3 className="text-base font-bold text-gray-900 mb-1">
            {isArabic ? "المساعد المصرفي الذكي" : "Customer Banking AI"}
          </h3>
          <p className="text-xs text-gray-600">
            {isArabic
              ? "محادثة بالعامية المصرية والإنجليزية للإجابة على الأسئلة المصرفية وحساب الفوائد."
              : "Bilingual Egyptian Arabic and English banking guidance for accounts, cards, and loans."}
          </p>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-5 shadow-sm hover:shadow transition">
          <div className="w-10 h-10 rounded-lg bg-emerald-100 text-emerald-800 flex items-center justify-center font-bold mb-3">
            ACC
          </div>
          <h3 className="text-base font-bold text-gray-900 mb-1">
            {isArabic ? "فتح الحسابات والمنتجات" : "Products & Onboarding"}
          </h3>
          <p className="text-xs text-gray-600">
            {isArabic
              ? "إرشادات فتح الحسابات الجارية والتوفير والودائع والشهادات الادخارية."
              : "Account opening prerequisites, certificate of deposit terms, and fee schedules."}
          </p>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-5 shadow-sm hover:shadow transition">
          <div className="w-10 h-10 rounded-lg bg-purple-100 text-purple-800 flex items-center justify-center font-bold mb-3">
            CMP
          </div>
          <h3 className="text-base font-bold text-gray-900 mb-1">
            {isArabic ? "تقديم الشكاوى والمتابعة" : "Complaints & Inquiries"}
          </h3>
          <p className="text-xs text-gray-600">
            {isArabic
              ? "تسجيل الشكاوى وتتبع مسار معالجتها لدى فريق خدمة العملاء (محاكاة داخلية)."
              : "Submit operational complaints and monitor simulated resolution tracking."}
          </p>
        </div>
      </div>
    </div>
  );
};
