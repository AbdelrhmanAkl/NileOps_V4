import React, { useState, useEffect } from "react";
import { useLanguage } from "../../contexts/LanguageContext";
import { fetchHealth } from "../../api/client";
import { HealthCheckResponse } from "../../types";

export const EmployeePortal: React.FC = () => {
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
      <div className="bg-gradient-to-r from-gray-800 to-gray-900 rounded-xl p-6 text-white shadow-md">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold mb-2">
              {isArabic ? "بوابة العمليات والموظفين — بنك النيل التجريبي" : "Employee & Operations Portal — NileOps Demo Bank"}
            </h1>
            <p className="text-gray-300 text-sm max-w-3xl leading-relaxed">
              {isArabic
                ? "مساحة عمل العمليات المصرفية، المساعد الداخلي للسياسات، وحوكمة مراجعة الهوية ومكافحة غسل الأموال (محاكاة اصطناعية)."
                : "Internal operations workspace, staff policy copilot, KYC audit workflows, and 4-eyes governance review."}
            </p>
          </div>
          <span className="hidden sm:inline-block bg-amber-500/20 text-amber-300 border border-amber-500/30 text-xs px-3 py-1.5 rounded-md font-mono">
            STAFF ACCESS ONLY
          </span>
        </div>
      </div>

      {/* Backend Status Card */}
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

      {/* Operations Workspaces (Phase Placeholders) */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
          <div className="text-xs font-bold text-nile-700 uppercase mb-1">
            {isArabic ? "مساعد السياسات الداخلي" : "Staff Copilot"}
          </div>
          <p className="text-xs text-gray-600">
            {isArabic
              ? "استرجاع سياسات البنك الـ 12 مع شارات الاعتماد والفقرات التوثيقية."
              : "Search 12 policy domains with approved citations and confidence scores."}
          </p>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
          <div className="text-xs font-bold text-amber-700 uppercase mb-1">
            {isArabic ? "تدقيق الهوية الوطنية" : "KYC & National ID"}
          </div>
          <p className="text-xs text-gray-600">
            {isArabic
              ? "فحص وتدقيق بطاقات الرقم القومي الاصطناعية وقواعد المحافظة والتواريخ."
              : "Inspect synthetic national ID fixtures, layout profiles, and multi-field validation."}
          </p>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
          <div className="text-xs font-bold text-purple-700 uppercase mb-1">
            {isArabic ? "حوكمة السياسات" : "Policy Governance"}
          </div>
          <p className="text-xs text-gray-600">
            {isArabic
              ? "دورة اعتماد السياسات: مسودة ← مراجعة ← اعتماد ← فهرسة في Qdrant."
              : "Four-eyes policy workflow: Draft → Pending Review → Approved → Qdrant Index."}
          </p>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
          <div className="text-xs font-bold text-emerald-700 uppercase mb-1">
            {isArabic ? "إدارة الصلاحيات" : "Role Governance"}
          </div>
          <p className="text-xs text-gray-600">
            {isArabic
              ? "إدارة الأدوار الخمسة المعتمدة وسجلات التدقيق الثابتة."
              : "Canonical 5 roles enforcement and immutable audit log inspection."}
          </p>
        </div>
      </div>
    </div>
  );
};
