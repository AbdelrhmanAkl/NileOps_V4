import React, { useState, useEffect } from "react";
import { useLanguage } from "../../contexts/LanguageContext";
import { useAuth } from "../../contexts/AuthContext";
import {
  fetchEmployeeDashboard,
  searchCustomers,
  fetchAllComplaints,
  updateComplaintStatus,
  fetchPolicies,
  createPolicyDraft,
  submitPolicyForApproval,
  approvePolicy,
  rejectPolicy,
  fetchKycVerifications,
  updateKycStatus,
  fetchAuditLogs,
} from "../../api/client";
import { Complaint, PolicyDocument, KycVerification, AuditLog, UserProfile } from "../../types";

export const EmployeePortal: React.FC = () => {
  const { isArabic } = useLanguage();
  const { user } = useAuth();

  // Active Tab
  const [activeTab, setActiveTab] = useState<"dashboard" | "complaints" | "policies" | "kyc" | "customers" | "audit">("dashboard");

  // Dashboard Metrics
  const [metrics, setMetrics] = useState<any>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Complaints State
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [complaintFilter, setComplaintFilter] = useState<string>("");
  const [selectedComplaint, setSelectedComplaint] = useState<Complaint | null>(null);
  const [newStatus, setNewStatus] = useState<string>("IN_PROGRESS");
  const [staffNote, setStaffNote] = useState<string>("");
  const [resolutionNote, setResolutionNote] = useState<string>("");

  // Policies State
  const [policies, setPolicies] = useState<PolicyDocument[]>([]);
  const [policySearch, setPolicySearch] = useState<string>("");
  const [policyDomain, setPolicyDomain] = useState<string>("");
  const [showCreatePolicy, setShowCreatePolicy] = useState<boolean>(false);
  const [newPolicy, setNewPolicy] = useState({
    code: "",
    title_en: "",
    title_ar: "",
    domain: "retail_banking",
    content_en: "",
    content_ar: "",
    version: "1.0.0",
  });
  const [policyFeedback, setPolicyFeedback] = useState<{ text: string; type: "success" | "error" } | null>(null);

  // KYC State
  const [kycQueue, setKycQueue] = useState<KycVerification[]>([]);

  // Customers State
  const [customerSearch, setCustomerSearch] = useState<string>("");
  const [customers, setCustomers] = useState<UserProfile[]>([]);

  // Audit State
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);

  const loadInitialData = async () => {
    setIsLoading(true);
    try {
      const [dash, cmps, pols, kyc, custs, logs] = await Promise.all([
        fetchEmployeeDashboard(),
        fetchAllComplaints(),
        fetchPolicies(),
        fetchKycVerifications(),
        searchCustomers(),
        fetchAuditLogs(),
      ]);
      setMetrics(dash.metrics);
      setComplaints(cmps);
      setPolicies(pols);
      setKycQueue(kyc);
      setCustomers(custs);
      setAuditLogs(logs);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadInitialData();
  }, []);

  // Update Complaint Handler
  const handleUpdateComplaint = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedComplaint) return;
    try {
      const updated = await updateComplaintStatus(selectedComplaint.id, {
        status: newStatus,
        staff_notes: staffNote,
        resolution_notes: resolutionNote,
      });
      setComplaints(complaints.map((c) => (c.id === updated.id ? updated : c)));
      setSelectedComplaint(null);
      setStaffNote("");
      setResolutionNote("");
    } catch (err: any) {
      alert(err.message || "Failed to update complaint");
    }
  };

  // Policy Search Handler
  const handlePolicySearch = async (q: string, dom: string) => {
    setPolicySearch(q);
    setPolicyDomain(dom);
    try {
      const results = await fetchPolicies(q, dom);
      setPolicies(results);
    } catch (err) {
      console.error(err);
    }
  };

  // Create Policy Draft Handler
  const handleCreatePolicy = async (e: React.FormEvent) => {
    e.preventDefault();
    setPolicyFeedback(null);
    try {
      const created = await createPolicyDraft(newPolicy);
      setPolicies([created, ...policies]);
      setShowCreatePolicy(false);
      setPolicyFeedback({
        text: isArabic ? "تم إنشاء مسودة السياسة بنجاح" : "Policy draft created successfully",
        type: "success",
      });
      setNewPolicy({
        code: "",
        title_en: "",
        title_ar: "",
        domain: "retail_banking",
        content_en: "",
        content_ar: "",
        version: "1.0.0",
      });
    } catch (err: any) {
      setPolicyFeedback({ text: err.message, type: "error" });
    }
  };

  // Submit Policy for Approval
  const handleSubmitPolicy = async (id: string) => {
    setPolicyFeedback(null);
    try {
      const updated = await submitPolicyForApproval(id);
      setPolicies(policies.map((p) => (p.id === updated.id ? updated : p)));
      setPolicyFeedback({
        text: isArabic ? "تم تقديم السياسة للاعتماد بنجاح" : "Policy submitted for review",
        type: "success",
      });
    } catch (err: any) {
      setPolicyFeedback({ text: err.message, type: "error" });
    }
  };

  // Approve Policy (4-Eyes Check)
  const handleApprovePolicy = async (id: string) => {
    setPolicyFeedback(null);
    try {
      const updated = await approvePolicy(id, "Approved under compliance audit review.");
      setPolicies(policies.map((p) => (p.id === updated.id ? updated : p)));
      setPolicyFeedback({
        text: isArabic ? "تم اعتماد السياسة وفهرستها في قاعدة المعرفة" : "Policy approved & indexed into KB",
        type: "success",
      });
    } catch (err: any) {
      setPolicyFeedback({ text: err.message, type: "error" });
    }
  };

  // Reject Policy
  const handleRejectPolicy = async (id: string) => {
    const reason = prompt(isArabic ? "سبب الرفض:" : "Enter rejection reason:");
    if (!reason) return;
    setPolicyFeedback(null);
    try {
      const updated = await rejectPolicy(id, reason);
      setPolicies(policies.map((p) => (p.id === updated.id ? updated : p)));
      setPolicyFeedback({
        text: isArabic ? "تم رفض مسودة السياسة" : "Policy draft rejected",
        type: "success",
      });
    } catch (err: any) {
      setPolicyFeedback({ text: err.message, type: "error" });
    }
  };

  // KYC Review Handler
  const handleKycReview = async (id: string, stat: string) => {
    try {
      const updated = await updateKycStatus(id, stat, `Status updated to ${stat} by ${user?.email}`);
      setKycQueue(kycQueue.map((k) => (k.id === updated.id ? updated : k)));
    } catch (err: any) {
      alert(err.message || "Failed to update KYC status");
    }
  };

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-16 text-center text-gray-500">
        <div className="inline-block w-8 h-8 border-4 border-nile-700 border-t-transparent rounded-full animate-spin mb-3"></div>
        <p className="text-sm font-medium">{isArabic ? "جاري تحميل بوابة العمليات..." : "Loading operations workspace..."}</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Employee Header */}
      <div className="bg-gray-900 rounded-2xl p-6 text-white shadow-md flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 rtl:space-x-reverse mb-1">
            <span className="bg-amber-500/20 text-amber-300 border border-amber-500/30 text-[10px] px-2 py-0.5 rounded font-mono">
              INTERNAL STAFF WORKSPACE
            </span>
            <span className="text-xs text-gray-400 font-mono">
              {user?.role.toUpperCase()}
            </span>
          </div>
          <h1 className="text-2xl font-bold">
            {isArabic ? `مساحة عمل العمليات — ${user?.full_name}` : `Operations Workspace — ${user?.full_name}`}
          </h1>
          <p className="text-xs text-gray-400 mt-0.5">
            {isArabic
              ? "إدارة الشكاوى، حوكمة السياسات المزدوجة، تدقيق وثائق الهوية، وسجلات التدقيق الثابتة."
              : "Complaint lifecycle, four-eyes policy governance, synthetic KYC review, and audit trail."}
          </p>
        </div>

        {/* Navigation Tabs */}
        <div className="flex flex-wrap gap-1 bg-gray-800 p-1.5 rounded-xl border border-gray-700">
          {(
            [
              ["dashboard", isArabic ? "لوحة المؤشرات" : "Dashboard"],
              ["complaints", isArabic ? `الشكاوى (${complaints.filter(c => c.status !== "RESOLVED").length})` : `Complaints (${complaints.filter(c => c.status !== "RESOLVED").length})`],
              ["policies", isArabic ? "حوكمة السياسات" : "Policy KB"],
              ["kyc", isArabic ? "تدقيق الهوية" : "KYC Queue"],
              ["customers", isArabic ? "العملاء" : "Customers"],
              ["audit", isArabic ? "سجل التدقيق" : "Audit Trail"],
            ] as const
          ).map(([key, label]) => (
            <button
              key={key}
              onClick={() => setActiveTab(key as any)}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition ${
                activeTab === key ? "bg-nile-700 text-white shadow" : "text-gray-300 hover:text-white hover:bg-gray-700"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {policyFeedback && (
        <div
          className={`p-3 rounded-lg text-xs font-medium border flex items-center justify-between ${
            policyFeedback.type === "success"
              ? "bg-green-50 border-green-200 text-green-800"
              : "bg-red-50 border-red-200 text-red-800"
          }`}
        >
          <span>{policyFeedback.text}</span>
          <button onClick={() => setPolicyFeedback(null)} className="text-xs font-bold">✕</button>
        </div>
      )}

      {/* TAB 1: DASHBOARD METRICS */}
      {activeTab === "dashboard" && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
              <span className="text-xs text-gray-500 font-semibold block mb-1">
                {isArabic ? "شكاوى قيد المتابعة" : "Open Complaints"}
              </span>
              <div className="text-3xl font-black text-rose-600">{metrics?.open_complaints || 0}</div>
            </div>
            <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
              <span className="text-xs text-gray-500 font-semibold block mb-1">
                {isArabic ? "سياسات بانتظار الاعتماد" : "Pending Policies"}
              </span>
              <div className="text-3xl font-black text-amber-600">{metrics?.pending_policies || 0}</div>
            </div>
            <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
              <span className="text-xs text-gray-500 font-semibold block mb-1">
                {isArabic ? "طلبات هوية قيد التدقيق" : "Pending KYC"}
              </span>
              <div className="text-3xl font-black text-blue-600">{metrics?.pending_kyc_reviews || 0}</div>
            </div>
            <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
              <span className="text-xs text-gray-500 font-semibold block mb-1">
                {isArabic ? "إجمالي العملاء" : "Total Customers"}
              </span>
              <div className="text-3xl font-black text-emerald-600">{metrics?.total_customers || 0}</div>
            </div>
            <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
              <span className="text-xs text-gray-500 font-semibold block mb-1">
                {isArabic ? "حسابات مصرفية نشطة" : "Active Accounts"}
              </span>
              <div className="text-3xl font-black text-gray-900">{metrics?.active_accounts || 0}</div>
            </div>
          </div>

          {/* Quick Actions Panel */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm space-y-3">
              <h3 className="text-sm font-bold text-gray-900">
                {isArabic ? "إدارة الشكاوى الفورية" : "Complaint Operations"}
              </h3>
              <p className="text-xs text-gray-500">
                {isArabic
                  ? "مراجعة شكاوى ماكينات الصراف وتحويلات إنستاباي وتسجيل إفادات الحل."
                  : "Review pending ATM debit failures, instant transfer tickets, and log resolutions."}
              </p>
              <button
                onClick={() => setActiveTab("complaints")}
                className="w-full py-2 bg-gray-100 hover:bg-gray-200 text-gray-800 text-xs font-bold rounded-lg transition"
              >
                {isArabic ? "الانتقال للشكاوى ←" : "Open Complaints Queue →"}
              </button>
            </div>

            <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm space-y-3">
              <h3 className="text-sm font-bold text-gray-900">
                {isArabic ? "حوكمة السياسات المصرفية (4-Eyes)" : "Policy Governance (4-Eyes)"}
              </h3>
              <p className="text-xs text-gray-500">
                {isArabic
                  ? "تحرير واعتماد وثائق السياسات عبر ضوابط الفصل الصارم للمهام."
                  : "Author draft policies or review documents under strict separation of duties."}
              </p>
              <button
                onClick={() => setActiveTab("policies")}
                className="w-full py-2 bg-gray-100 hover:bg-gray-200 text-gray-800 text-xs font-bold rounded-lg transition"
              >
                {isArabic ? "الانتقال للسياسات ←" : "Open Policy Workspace →"}
              </button>
            </div>

            <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm space-y-3">
              <h3 className="text-sm font-bold text-gray-900">
                {isArabic ? "تدقيق وثائق الرقم القومي الاصطناعية" : "Synthetic KYC Queue"}
              </h3>
              <p className="text-xs text-gray-500">
                {isArabic
                  ? "تدقيق بطاقات الرقم القومي الاصطناعية وقواعد التحقق الـ 9."
                  : "Inspect synthetic ID fixtures, century & governorate rules, and document AI."}
              </p>
              <button
                onClick={() => setActiveTab("kyc")}
                className="w-full py-2 bg-gray-100 hover:bg-gray-200 text-gray-800 text-xs font-bold rounded-lg transition"
              >
                {isArabic ? "الانتقال لقائمة التدقيق ←" : "Open KYC Queue →"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: COMPLAINTS MANAGEMENT */}
      {activeTab === "complaints" && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="p-5 border-b border-gray-200 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div>
              <h2 className="text-base font-bold text-gray-900">
                {isArabic ? "إدارة ومتابعة شكاوى العملاء" : "Customer Complaints Management"}
              </h2>
              <p className="text-xs text-gray-500">
                {isArabic ? "قائمة جميع التذاكر المسجلة مع إمكانية تحديث الحالة وإضافة ملاحظات الدعم" : "All registered tickets with status updates and resolution notes"}
              </p>
            </div>

            <div className="flex items-center space-x-2 rtl:space-x-reverse">
              <label className="text-xs text-gray-500 font-semibold">{isArabic ? "تصفية:" : "Filter:"}</label>
              <select
                value={complaintFilter}
                onChange={async (e) => {
                  setComplaintFilter(e.target.value);
                  const cmps = await fetchAllComplaints(e.target.value || undefined);
                  setComplaints(cmps);
                }}
                className="text-xs border border-gray-300 rounded px-2.5 py-1.5"
              >
                <option value="">{isArabic ? "جميع الحالات" : "All Statuses"}</option>
                <option value="OPEN">{isArabic ? "مفتوحة" : "OPEN"}</option>
                <option value="IN_PROGRESS">{isArabic ? "قيد المتابعة" : "IN_PROGRESS"}</option>
                <option value="RESOLVED">{isArabic ? "تم الحل" : "RESOLVED"}</option>
                <option value="REJECTED">{isArabic ? "مرفوضة" : "REJECTED"}</option>
              </select>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left rtl:text-right text-xs">
              <thead className="bg-gray-50 text-gray-600 font-semibold border-b border-gray-200">
                <tr>
                  <th className="px-5 py-3">{isArabic ? "رقم التذكرة" : "Ticket #"}</th>
                  <th className="px-5 py-3">{isArabic ? "الفئة" : "Category"}</th>
                  <th className="px-5 py-3">{isArabic ? "الموضوع والبيان" : "Subject & Details"}</th>
                  <th className="px-5 py-3">{isArabic ? "الحالة" : "Status"}</th>
                  <th className="px-5 py-3">{isArabic ? "ملاحظات الدعم" : "Staff Notes"}</th>
                  <th className="px-5 py-3 text-right rtl:text-left">{isArabic ? "الإجراء" : "Action"}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 text-gray-700">
                {complaints.map((c) => (
                  <tr key={c.id} className="hover:bg-gray-50 transition">
                    <td className="px-5 py-3 font-mono font-bold text-nile-800">{c.ticket_number}</td>
                    <td className="px-5 py-3 font-medium">{isArabic ? c.category_ar : c.category}</td>
                    <td className="px-5 py-3 max-w-xs">
                      <strong className="block text-gray-900">{c.subject}</strong>
                      <span className="text-gray-500 line-clamp-1">{c.details}</span>
                    </td>
                    <td className="px-5 py-3">
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                          c.status === "RESOLVED"
                            ? "bg-green-100 text-green-800"
                            : c.status === "IN_PROGRESS"
                            ? "bg-amber-100 text-amber-800"
                            : "bg-blue-100 text-blue-800"
                        }`}
                      >
                        {c.status}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-gray-600 text-[11px] max-w-xs">
                      {c.staff_notes || c.resolution_notes || "—"}
                    </td>
                    <td className="px-5 py-3 text-right rtl:text-left">
                      <button
                        onClick={() => {
                          setSelectedComplaint(c);
                          setNewStatus(c.status);
                          setStaffNote(c.staff_notes || "");
                          setResolutionNote(c.resolution_notes || "");
                        }}
                        className="px-2.5 py-1 bg-nile-700 hover:bg-nile-800 text-white font-bold text-[11px] rounded transition"
                      >
                        {isArabic ? "تحديث" : "Manage"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 3: POLICY GOVERNANCE & 4-EYES APPROVAL */}
      {activeTab === "policies" && (
        <div className="space-y-6">
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div>
              <h2 className="text-base font-bold text-gray-900">
                {isArabic ? "حوكمة السياسات المصرفية (قاعدة المعرفة المعتمدة)" : "Policy Knowledge Base Governance"}
              </h2>
              <p className="text-xs text-gray-500">
                {isArabic
                  ? "الفصل الإلزامي للمهام: لا يمكن لكاتب السياسة اعتماد وثيقته بنفسه (4-Eyes Principle)"
                  : "Strict separation of duties: Authors cannot approve their own documents"}
              </p>
            </div>

            <div className="flex items-center space-x-2 rtl:space-x-reverse">
              <input
                type="text"
                placeholder={isArabic ? "بحث في السياسات..." : "Search policies..."}
                value={policySearch}
                onChange={(e) => handlePolicySearch(e.target.value, policyDomain)}
                className="text-xs border border-gray-300 rounded px-3 py-1.5 w-48"
              />
              <button
                onClick={() => setShowCreatePolicy(true)}
                className="px-3 py-1.5 bg-nile-700 hover:bg-nile-800 text-white text-xs font-bold rounded shadow transition"
              >
                + {isArabic ? "مسودة جديدة" : "New Draft"}
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4">
            {policies.map((p) => {
              const isAuthor = p.created_by_id === user?.id;
              const canApproveRole = ["compliance_reviewer", "branch_manager", "admin"].includes(user?.role || "");

              return (
                <div key={p.id} className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm space-y-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center space-x-2 rtl:space-x-reverse mb-1">
                        <span className="font-mono text-xs font-bold text-nile-800">{p.code}</span>
                        <span className="text-[10px] font-mono bg-gray-100 text-gray-700 px-2 py-0.5 rounded">
                          v{p.version}
                        </span>
                        <span className="text-[10px] bg-blue-50 text-blue-700 px-2 py-0.5 rounded font-semibold">
                          {p.domain}
                        </span>
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                            p.status === "INDEXED" || p.status === "APPROVED"
                              ? "bg-green-100 text-green-800"
                              : p.status === "PENDING_APPROVAL"
                              ? "bg-amber-100 text-amber-800"
                              : p.status === "REJECTED"
                              ? "bg-rose-100 text-rose-800"
                              : "bg-gray-100 text-gray-800"
                          }`}
                        >
                          {p.status}
                        </span>
                      </div>
                      <h3 className="text-sm font-bold text-gray-900">
                        {isArabic ? p.title_ar : p.title_en}
                      </h3>
                    </div>

                    {/* 4-Eyes Action Buttons */}
                    <div className="flex items-center space-x-2 rtl:space-x-reverse">
                      {p.status === "DRAFT" && (
                        <button
                          onClick={() => handleSubmitPolicy(p.id)}
                          className="px-3 py-1 bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold rounded transition"
                        >
                          {isArabic ? "تقديم للاعتماد" : "Submit for Review"}
                        </button>
                      )}

                      {p.status === "PENDING_APPROVAL" && (
                        <>
                          <button
                            onClick={() => handleApprovePolicy(p.id)}
                            disabled={!canApproveRole}
                            title={
                              isAuthor
                                ? "Four-Eyes Rule: You authored this policy and cannot approve it yourself!"
                                : ""
                            }
                            className={`px-3 py-1 text-xs font-bold rounded transition ${
                              isAuthor
                                ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                                : "bg-emerald-600 hover:bg-emerald-700 text-white"
                            }`}
                          >
                            {isAuthor
                              ? isArabic
                                ? "حظر اعتماد ذاتي (4-Eyes)"
                                : "Blocked: Self-Approval"
                              : isArabic
                              ? "اعتماد وفهرسة"
                              : "Approve & Index"}
                          </button>
                          <button
                            onClick={() => handleRejectPolicy(p.id)}
                            className="px-3 py-1 bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold rounded transition"
                          >
                            {isArabic ? "رفض" : "Reject"}
                          </button>
                        </>
                      )}
                    </div>
                  </div>

                  <p className="text-xs text-gray-600 leading-relaxed bg-gray-50/60 p-3 rounded-lg border border-gray-100">
                    {isArabic ? p.content_ar : p.content_en}
                  </p>

                  {p.approval_notes && (
                    <div className="text-[11px] text-green-800 bg-green-50/80 p-2 rounded border border-green-200">
                      <strong>{isArabic ? "ملاحظة الاعتماد:" : "Approval Note:"}</strong> {p.approval_notes}
                    </div>
                  )}
                  {p.rejection_reason && (
                    <div className="text-[11px] text-rose-800 bg-rose-50/80 p-2 rounded border border-rose-200">
                      <strong>{isArabic ? "سبب الرفض:" : "Rejection Reason:"}</strong> {p.rejection_reason}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* TAB 4: SYNTHETIC KYC QUEUE */}
      {activeTab === "kyc" && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="p-5 border-b border-gray-200">
            <h2 className="text-base font-bold text-gray-900">
              {isArabic ? "تدقيق وثائق الرقم القومي الاصطناعية (KYC Simulation)" : "Synthetic National ID KYC Queue"}
            </h2>
            <p className="text-xs text-gray-500">
              {isArabic
                ? "فحص وتدقيق البيانات المستخرجة اصطناعياً وفقاً لمعايير وثيقة NATIONAL_ID_VALIDATION_SPEC"
                : "Simulated document intelligence validation against 14-digit Egyptian National ID standards"}
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left rtl:text-right text-xs">
              <thead className="bg-gray-50 text-gray-600 font-semibold border-b border-gray-200">
                <tr>
                  <th className="px-5 py-3">{isArabic ? "رقم المتابعة" : "Tracking #"}</th>
                  <th className="px-5 py-3">{isArabic ? "الرقم القومي الاصطناعي" : "Synthetic National ID"}</th>
                  <th className="px-5 py-3">{isArabic ? "البيانات المستخرجة" : "Extracted Fields"}</th>
                  <th className="px-5 py-3">{isArabic ? "الحالة" : "Status"}</th>
                  <th className="px-5 py-3 text-right rtl:text-left">{isArabic ? "قرار التدقيق" : "Decision"}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 text-gray-700">
                {kycQueue.map((k) => (
                  <tr key={k.id} className="hover:bg-gray-50 transition">
                    <td className="px-5 py-3 font-mono font-bold text-nile-800">{k.tracking_number}</td>
                    <td className="px-5 py-3 font-mono font-semibold text-gray-900">{k.synthetic_national_id}</td>
                    <td className="px-5 py-3 text-[11px] font-mono text-gray-600 max-w-xs truncate">
                      {k.extracted_data_json}
                    </td>
                    <td className="px-5 py-3">
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                          k.status === "VERIFIED_SYNTHETIC"
                            ? "bg-green-100 text-green-800"
                            : k.status === "REJECTED"
                            ? "bg-rose-100 text-rose-800"
                            : "bg-amber-100 text-amber-800"
                        }`}
                      >
                        {k.status}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-right rtl:text-left space-x-1.5 rtl:space-x-reverse">
                      <button
                        onClick={() => handleKycReview(k.id, "VERIFIED_SYNTHETIC")}
                        className="px-2 py-1 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-[10px] rounded"
                      >
                        {isArabic ? "قبول" : "Verify"}
                      </button>
                      <button
                        onClick={() => handleKycReview(k.id, "REJECTED")}
                        className="px-2 py-1 bg-rose-600 hover:bg-rose-700 text-white font-bold text-[10px] rounded"
                      >
                        {isArabic ? "رفض" : "Reject"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 5: CUSTOMER LOOKUP */}
      {activeTab === "customers" && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-gray-900">
                {isArabic ? "دليل وبحث عملاء البنك" : "Customer Portfolio Search"}
              </h2>
              <p className="text-xs text-gray-500">
                {isArabic ? "استعلام مصرح به لموظفي العمليات وخدمة العملاء" : "Authorized lookup for branch operations & customer support"}
              </p>
            </div>
            <input
              type="text"
              placeholder={isArabic ? "بحث بالاسم أو البريد..." : "Search name or email..."}
              value={customerSearch}
              onChange={async (e) => {
                setCustomerSearch(e.target.value);
                const results = await searchCustomers(e.target.value);
                setCustomers(results);
              }}
              className="text-xs border border-gray-300 rounded px-3 py-1.5 w-64"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {customers.map((c) => (
              <div key={c.id} className="p-4 rounded-lg border border-gray-200 bg-gray-50/50 flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-bold text-gray-900">{c.full_name}</h4>
                  <p className="text-xs text-gray-500 font-mono">{c.email}</p>
                  <p className="text-xs text-gray-400 mt-1">{c.phone_number || "—"}</p>
                </div>
                <span className="text-[10px] bg-green-100 text-green-800 font-bold px-2 py-0.5 rounded">
                  ACTIVE RETAIL
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 6: AUDIT TRAIL */}
      {activeTab === "audit" && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="p-5 border-b border-gray-200">
            <h2 className="text-base font-bold text-gray-900">
              {isArabic ? "سجل التدقيق الأمني والرقابي الثابت" : "Immutable Security & Governance Audit Trail"}
            </h2>
            <p className="text-xs text-gray-500">
              {isArabic ? "توثيق تلقائي غير قابل للتعديل لجميع العمليات الحساسة" : "Automated immutable audit logging of logins, approvals, and status transitions"}
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left rtl:text-right text-xs">
              <thead className="bg-gray-50 text-gray-600 font-semibold border-b border-gray-200">
                <tr>
                  <th className="px-5 py-3">{isArabic ? "التوقيت" : "Timestamp"}</th>
                  <th className="px-5 py-3">{isArabic ? "المستخدم" : "User"}</th>
                  <th className="px-5 py-3">{isArabic ? "الإجراء" : "Action"}</th>
                  <th className="px-5 py-3">{isArabic ? "نوع المورد" : "Resource"}</th>
                  <th className="px-5 py-3">{isArabic ? "تفاصيل العملية" : "Details JSON"}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 text-gray-700">
                {auditLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50 transition">
                    <td className="px-5 py-3 font-mono text-gray-500">
                      {new Date(log.timestamp).toLocaleTimeString("en-GB")}
                    </td>
                    <td className="px-5 py-3 font-medium text-gray-900">
                      {log.user_email || "System"} ({log.user_role || "—"})
                    </td>
                    <td className="px-5 py-3 font-mono font-bold text-nile-800">{log.action}</td>
                    <td className="px-5 py-3">
                      <span className="px-1.5 py-0.5 bg-gray-100 rounded text-[10px] font-mono">{log.resource_type}</span>
                    </td>
                    <td className="px-5 py-3 font-mono text-[11px] text-gray-600 max-w-sm truncate">
                      {log.details_json}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Complaint Update Modal Drawer */}
      {selectedComplaint && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl relative">
            <button
              onClick={() => setSelectedComplaint(null)}
              className="absolute top-4 right-4 rtl:left-4 rtl:right-auto text-gray-400 hover:text-gray-700"
            >
              ✕
            </button>
            <h3 className="text-base font-bold text-gray-900 mb-1">
              {isArabic ? `تحديث الشكوى: ${selectedComplaint.ticket_number}` : `Update Ticket: ${selectedComplaint.ticket_number}`}
            </h3>
            <p className="text-xs text-gray-500 mb-4">{selectedComplaint.subject}</p>

            <form onSubmit={handleUpdateComplaint} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  {isArabic ? "الحالة الجديدة" : "Status"}
                </label>
                <select
                  value={newStatus}
                  onChange={(e) => setNewStatus(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg"
                >
                  <option value="OPEN">OPEN (مفتوحة)</option>
                  <option value="IN_PROGRESS">IN_PROGRESS (قيد المعالجة)</option>
                  <option value="RESOLVED">RESOLVED (تم الحل والإغلاق)</option>
                  <option value="REJECTED">REJECTED (مرفوضة)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  {isArabic ? "ملاحظات الدعم الداخلي" : "Staff Notes (Internal)"}
                </label>
                <textarea
                  rows={3}
                  value={staffNote}
                  onChange={(e) => setStaffNote(e.target.value)}
                  placeholder={isArabic ? "أدخل إفادة الدعم والمتابعة..." : "Internal notes on action taken..."}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg"
                />
              </div>

              {newStatus === "RESOLVED" && (
                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">
                    {isArabic ? "قرار الحل النهائي (يظهر للعميل)" : "Resolution Notes (Customer Facing)"}
                  </label>
                  <textarea
                    rows={2}
                    value={resolutionNote}
                    onChange={(e) => setResolutionNote(e.target.value)}
                    placeholder={isArabic ? "تم استرجاع المبلغ / تم تسوية المعاملة بنجاح..." : "Details provided to the customer upon resolution..."}
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg"
                  />
                </div>
              )}

              <div className="flex justify-end space-x-2 rtl:space-x-reverse pt-2">
                <button
                  type="button"
                  onClick={() => setSelectedComplaint(null)}
                  className="px-4 py-2 border border-gray-300 text-gray-700 text-xs font-semibold rounded-lg hover:bg-gray-50"
                >
                  {isArabic ? "إلغاء" : "Cancel"}
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 bg-nile-700 text-white text-xs font-bold rounded-lg hover:bg-nile-800"
                >
                  {isArabic ? "حفظ التحديث" : "Save Changes"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create Policy Draft Modal */}
      {showCreatePolicy && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-xl w-full p-6 shadow-2xl relative max-h-[90vh] overflow-y-auto">
            <button
              onClick={() => setShowCreatePolicy(false)}
              className="absolute top-4 right-4 rtl:left-4 rtl:right-auto text-gray-400 hover:text-gray-700"
            >
              ✕
            </button>
            <h3 className="text-base font-bold text-gray-900 mb-1">
              {isArabic ? "تحرير مسودة سياسة مصرفية جديدة (DRAFT)" : "Create Policy Document Draft"}
            </h3>
            <p className="text-xs text-gray-500 mb-4">
              {isArabic ? "تنشأ الوثيقة بحالة مسودة وتتطلب تقديم واعتماد مراجع مستقل" : "Creates a DRAFT policy requiring 4-eyes approval by an independent reviewer"}
            </p>

            <form onSubmit={handleCreatePolicy} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">
                    {isArabic ? "كود السياسة" : "Policy Code"}
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="POL-CARD-002"
                    value={newPolicy.code}
                    onChange={(e) => setNewPolicy({ ...newPolicy, code: e.target.value })}
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg font-mono"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">
                    {isArabic ? "مجال السياسة" : "Domain"}
                  </label>
                  <select
                    value={newPolicy.domain}
                    onChange={(e) => setNewPolicy({ ...newPolicy, domain: e.target.value })}
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg"
                  >
                    <option value="retail_banking">Retail Banking</option>
                    <option value="kyc_aml">KYC & AML</option>
                    <option value="digital_channels">Digital Channels</option>
                    <option value="credit_risk">Credit Risk</option>
                    <option value="treasury">Treasury</option>
                    <option value="governance">Corporate Governance</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  {isArabic ? "العنوان بالإنجليزية" : "Title (English)"}
                </label>
                <input
                  type="text"
                  required
                  placeholder="Contactless Cards Limits and PIN Thresholds"
                  value={newPolicy.title_en}
                  onChange={(e) => setNewPolicy({ ...newPolicy, title_en: e.target.value })}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  {isArabic ? "العنوان بالعربية" : "Title (Arabic)"}
                </label>
                <input
                  type="text"
                  required
                  placeholder="حدود المعاملات اللاتلامسية وقواعد إدخال الرقم السري للبطاقات"
                  value={newPolicy.title_ar}
                  onChange={(e) => setNewPolicy({ ...newPolicy, title_ar: e.target.value })}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  {isArabic ? "نص السياسة بالإنجليزية" : "Content (English)"}
                </label>
                <textarea
                  rows={3}
                  required
                  value={newPolicy.content_en}
                  onChange={(e) => setNewPolicy({ ...newPolicy, content_en: e.target.value })}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg font-mono text-xs"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  {isArabic ? "نص السياسة بالعربية" : "Content (Arabic)"}
                </label>
                <textarea
                  rows={3}
                  required
                  value={newPolicy.content_ar}
                  onChange={(e) => setNewPolicy({ ...newPolicy, content_ar: e.target.value })}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg text-xs"
                />
              </div>

              <div className="flex justify-end space-x-2 rtl:space-x-reverse pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreatePolicy(false)}
                  className="px-4 py-2 border border-gray-300 text-gray-700 text-xs font-semibold rounded-lg hover:bg-gray-50"
                >
                  {isArabic ? "إلغاء" : "Cancel"}
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 bg-nile-700 text-white text-xs font-bold rounded-lg hover:bg-nile-800"
                >
                  {isArabic ? "إنشاء المسودة" : "Save Draft"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
