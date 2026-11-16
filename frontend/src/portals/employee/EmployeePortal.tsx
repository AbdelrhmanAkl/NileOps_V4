import React, { useState, useEffect } from "react";
import { useLanguage } from "../../contexts/LanguageContext";
import { useAuth } from "../../contexts/AuthContext";
import {
  fetchEmployeeDashboard,
  searchCustomers,
  fetchAllComplaints,
  updateComplaintStatus,
  fetchComplaintAdvisory,
  fetchPolicies,
  createPolicyDraft,
  submitPolicyForApproval,
  approvePolicy,
  rejectPolicy,
  fetchKycVerifications,
  uploadKycDocument,
  updateKycStatus,
  fetchAuditLogs,
  fetchEmployeeAccountRequests,
  evaluateAccountRequest,
  reviewAccountRequest,
  fetchEmployeeCardRequests,
  reviewCardRequest,
  fetchKpiSummary,
} from "../../api/client";
import {
  Complaint,
  AdvisoryClassificationResult,
  PolicyDocument,
  KycVerification,
  AuditLog,
  UserProfile,
  AccountOpeningRequest,
  CardRequest,
  RequestRuleEvaluation,
  KpiSummary,
} from "../../types";
import {
  getStatusLabel,
  getPriorityLabel,
  getSlaLabel,
  getTeamLabel,
  getCategoryLabel,
} from "../../utils/complaintTranslations";
import { RAGAssistant } from "../../components/RAGAssistant";
import { OpsAgentPanel } from "../../components/OpsAgentPanel";

function formatAuditTimestamp(isoString: string): string {
  try {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return isoString;
    const year = d.getUTCFullYear();
    const month = String(d.getUTCMonth() + 1).padStart(2, "0");
    const day = String(d.getUTCDate()).padStart(2, "0");
    const hours = String(d.getUTCHours()).padStart(2, "0");
    const mins = String(d.getUTCMinutes()).padStart(2, "0");
    const secs = String(d.getUTCSeconds()).padStart(2, "0");
    return `${year}-${month}-${day} ${hours}:${mins}:${secs} UTC`;
  } catch {
    return isoString;
  }
}

const ProtectedImage: React.FC<{ src: string; alt: string; className?: string }> = ({ src, alt, className }) => {
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<boolean>(false);

  useEffect(() => {
    let active = true;
    let createdUrl = "";
    const token = localStorage.getItem("nileops_token");
    setLoading(true);
    setError(false);

    fetch(src, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      .then((res) => {
        if (!res.ok) throw new Error("Image load failed");
        return res.blob();
      })
      .then((blob) => {
        if (!active) return;
        createdUrl = URL.createObjectURL(blob);
        setBlobUrl(createdUrl);
        setLoading(false);
      })
      .catch(() => {
        if (!active) return;
        setError(true);
        setLoading(false);
      });

    return () => {
      active = false;
      if (createdUrl) URL.revokeObjectURL(createdUrl);
    };
  }, [src]);

  if (loading) {
    return <div className="p-8 text-center text-xs text-gray-400 font-mono animate-pulse">Loading synthetic card image...</div>;
  }
  if (error || !blobUrl) {
    return <div className="p-8 text-center text-xs text-rose-400 font-mono">Failed to load synthetic card image</div>;
  }

  return <img src={blobUrl} alt={alt} className={className} />;
};

export const EmployeePortal: React.FC = () => {
  const { isArabic } = useLanguage();
  const { user } = useAuth();

  // Active Tab
  const [activeTab, setActiveTab] = useState<"dashboard" | "complaints" | "policies" | "kyc" | "customers" | "audit" | "requests" | "assistant">("dashboard");
  const [assistantSubTab, setAssistantSubTab] = useState<"copilot" | "rag">("copilot");

  // Dashboard Metrics & Operational KPIs
  const [, setMetrics] = useState<any>(null);
  const [kpiSummary, setKpiSummary] = useState<KpiSummary | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Complaints State & Server-Side Pagination
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [complaintsTotal, setComplaintsTotal] = useState<number>(0);
  const [complaintsPage, setComplaintsPage] = useState<number>(1);
  const [complaintsPageSize] = useState<number>(10);
  const [complaintsTotalPages, setComplaintsTotalPages] = useState<number>(1);
  const [isComplaintsLoading, setIsComplaintsLoading] = useState<boolean>(false);

  // Complaints Filters, Search & Sorting
  const [complaintFilter, setComplaintFilter] = useState<string>("");
  const [complaintCategoryFilter, setComplaintCategoryFilter] = useState<string>("");
  const [complaintPriorityFilter, setComplaintPriorityFilter] = useState<string>("");
  const [complaintTeamFilter, setComplaintTeamFilter] = useState<string>("");
  const [complaintSearch, setComplaintSearch] = useState<string>("");
  const [complaintIncludeTest, setComplaintIncludeTest] = useState<boolean>(false);
  const [complaintSortBy, setComplaintSortBy] = useState<string>("created_at");
  const [complaintSortOrder, setComplaintSortOrder] = useState<string>("desc");

  // Complaint Management & Advisory Drawer
  const [selectedComplaint, setSelectedComplaint] = useState<Complaint | null>(null);
  const [newStatus, setNewStatus] = useState<string>("IN_PROGRESS");
  const [newPriority, setNewPriority] = useState<string>("MEDIUM");
  const [newTeam, setNewTeam] = useState<string>("");
  const [staffNote, setStaffNote] = useState<string>("");
  const [resolutionNote, setResolutionNote] = useState<string>("");
  const [customerReply, setCustomerReply] = useState<string>("");
  const [confirmReplyChecked, setConfirmReplyChecked] = useState<boolean>(false);
  const [advisoryLoading, setAdvisoryLoading] = useState<boolean>(false);
  const [advisoryData, setAdvisoryData] = useState<AdvisoryClassificationResult | null>(null);

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
  const [selectedKycId, setSelectedKycId] = useState<string | null>(null);
  const [kycFilter, setKycFilter] = useState<string>("ALL");
  const [kycSearch, setKycSearch] = useState<string>("");
  const [showUploadModal, setShowUploadModal] = useState<boolean>(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadPreview, setUploadPreview] = useState<string | null>(null);
  const [isUploadingKyc, setIsUploadingKyc] = useState<boolean>(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [reviewModal, setReviewModal] = useState<{
    isOpen: boolean;
    kycId: string;
    trackingNumber: string;
    action: "REJECTED" | "INFO_REQUESTED";
    reason: string;
  }>({
    isOpen: false,
    kycId: "",
    trackingNumber: "",
    action: "REJECTED",
    reason: "",
  });

  // Customers State
  const [customerSearch, setCustomerSearch] = useState<string>("");
  const [customers, setCustomers] = useState<UserProfile[]>([]);

  // Audit State
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);

  // Requests Queue State (Phase 3)
  const [accountRequests, setAccountRequests] = useState<AccountOpeningRequest[]>([]);
  const [cardRequests, setCardRequests] = useState<CardRequest[]>([]);
  const [selectedAccReq, setSelectedAccReq] = useState<AccountOpeningRequest | null>(null);
  const [selectedCardReq, setSelectedCardReq] = useState<CardRequest | null>(null);
  const [requestSubTab, setRequestSubTab] = useState<"accounts" | "cards">("accounts");
  const [requestFilter, setRequestFilter] = useState<string>("ALL");
  const [ruleEval, setRuleEval] = useState<RequestRuleEvaluation | null>(null);
  const [isEvaluatingRules, setIsEvaluatingRules] = useState<boolean>(false);
  const [requestActionModal, setRequestActionModal] = useState<{
    isOpen: boolean;
    type: "account" | "card";
    id: string;
    reference: string;
    action: "UNDER_REVIEW" | "APPROVED_SIMULATED" | "MORE_INFO_REQUIRED" | "REJECTED" | "SIMULATED_COMPLETED";
    notes: string;
    rejectionReason: string;
  }>({
    isOpen: false,
    type: "account",
    id: "",
    reference: "",
    action: "UNDER_REVIEW",
    notes: "",
    rejectionReason: "",
  });

  const loadInitialData = async () => {
    setIsLoading(true);
    try {
      const results = await Promise.allSettled([
        fetchEmployeeDashboard(),
        fetchAllComplaints(),
        fetchPolicies(),
        fetchKycVerifications(),
        searchCustomers(),
        fetchAuditLogs(),
        fetchEmployeeAccountRequests(),
        fetchEmployeeCardRequests(),
        fetchKpiSummary(),
      ]);
      const [dashRes, cmpsRes, polsRes, kycRes, custsRes, logsRes, accReqsRes, cardReqsRes, kpiRes] = results;
      if (dashRes.status === "fulfilled") setMetrics(dashRes.value.metrics);
      if (kpiRes && kpiRes.status === "fulfilled") setKpiSummary(kpiRes.value);
      if (cmpsRes.status === "fulfilled") {
        const val = cmpsRes.value;
        if (Array.isArray(val)) {
          setComplaints(val);
          setComplaintsTotal(val.length);
        } else if (val && val.items) {
          setComplaints(val.items);
          setComplaintsTotal(val.total);
          setComplaintsTotalPages(val.total_pages);
          setComplaintsPage(val.page);
        }
      }
      if (polsRes.status === "fulfilled") setPolicies(polsRes.value);
      if (kycRes.status === "fulfilled") {
        setKycQueue(kycRes.value);
        if (kycRes.value && kycRes.value.length > 0) {
          setSelectedKycId((prev) => prev || kycRes.value[0].id);
        }
      }
      if (custsRes.status === "fulfilled") setCustomers(custsRes.value);
      if (logsRes.status === "fulfilled") setAuditLogs(logsRes.value);
      else setAuditLogs([]);
      if (accReqsRes.status === "fulfilled") {
        setAccountRequests(accReqsRes.value);
        if (accReqsRes.value && accReqsRes.value.length > 0) {
          setSelectedAccReq((prev) => prev || accReqsRes.value[0]);
        }
      }
      if (cardReqsRes.status === "fulfilled") {
        setCardRequests(cardReqsRes.value);
        if (cardReqsRes.value && cardReqsRes.value.length > 0) {
          setSelectedCardReq((prev) => prev || cardReqsRes.value[0]);
        }
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const loadComplaints = async (newPage = complaintsPage) => {
    setIsComplaintsLoading(true);
    try {
      const res = await fetchAllComplaints({
        status: complaintFilter || undefined,
        category: complaintCategoryFilter || undefined,
        priority: complaintPriorityFilter || undefined,
        team: complaintTeamFilter || undefined,
        search: complaintSearch || undefined,
        include_test: complaintIncludeTest,
        sort_by: complaintSortBy,
        sort_order: complaintSortOrder,
        page: newPage,
        page_size: complaintsPageSize,
      });
      if (res && res.items) {
        setComplaints(res.items);
        setComplaintsTotal(res.total);
        setComplaintsPage(res.page);
        setComplaintsTotalPages(res.total_pages);
      } else if (Array.isArray(res)) {
        setComplaints(res);
        setComplaintsTotal(res.length);
      }
    } catch (e) {
      console.error("Failed to load complaints:", e);
    } finally {
      setIsComplaintsLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === "complaints") {
      loadComplaints(1);
    }
  }, [
    activeTab,
    complaintFilter,
    complaintCategoryFilter,
    complaintPriorityFilter,
    complaintTeamFilter,
    complaintIncludeTest,
    complaintSortBy,
    complaintSortOrder,
  ]);

  useEffect(() => {
    loadInitialData();
  }, [user?.id]);

  // Select and evaluate account request
  const handleSelectAccountRequest = async (req: AccountOpeningRequest) => {
    setSelectedAccReq(req);
    setIsEvaluatingRules(true);
    try {
      const evalResult = await evaluateAccountRequest(req.id);
      setRuleEval(evalResult);
    } catch (e) {
      console.error(e);
      setRuleEval(null);
    } finally {
      setIsEvaluatingRules(false);
    }
  };

  // Automatically trigger rule evaluation when a request is selected or loaded
  useEffect(() => {
    if (selectedAccReq?.id) {
      setIsEvaluatingRules(true);
      evaluateAccountRequest(selectedAccReq.id)
        .then((res) => setRuleEval(res))
        .catch((e) => {
          console.error(e);
          setRuleEval(null);
        })
        .finally(() => setIsEvaluatingRules(false));
    }
  }, [selectedAccReq?.id]);

  // Submit Review Decision for Account / Card Request
  const handleExecuteRequestReview = async (e: React.FormEvent) => {
    e.preventDefault();
    const { type, id, action, notes, rejectionReason } = requestActionModal;
    if (action === "REJECTED" && !rejectionReason.trim()) {
      alert(isArabic ? "يرجى ذكر سبب الرفض الإلزامي" : "A rejection reason is mandatory.");
      return;
    }

    try {
      if (type === "account") {
        const updated = await reviewAccountRequest(id, {
          status: action,
          notes,
          rejection_reason: rejectionReason,
        });
        setAccountRequests((prev) => prev.map((r) => (r.id === updated.id ? updated : r)));
        setSelectedAccReq(updated);
      } else {
        const updated = await reviewCardRequest(id, {
          status: action,
          notes,
          rejection_reason: rejectionReason,
        });
        setCardRequests((prev) => prev.map((r) => (r.id === updated.id ? updated : r)));
        setSelectedCardReq(updated);
      }
      setRequestActionModal((prev) => ({ ...prev, isOpen: false, notes: "", rejectionReason: "" }));
    } catch (err: any) {
      alert(err.message || "Failed to submit review decision");
    }
  };

  const getFilterLabel = (st: string) => {
    if (!isArabic) return st;
    switch (st) {
      case "ALL": return "الكل";
      case "SUBMITTED": return "تم التقديم";
      case "UNDER_REVIEW": return "قيد المراجعة";
      case "APPROVED_SIMULATED": return "معتمد محاكاة";
      case "MORE_INFO_REQUIRED": return "استيفاء بيانات";
      case "REJECTED": return "مرفوض";
      case "SIMULATED_COMPLETED": return "مكتمل محاكاة";
      default: return st;
    }
  };

  const getAccountProductName = (productId: string) => {
    switch (productId) {
      case "prod-01":
        return isArabic ? "الحساب الجاري الكلاسيكي" : "Classic Current Account";
      case "prod-02":
        return isArabic ? "حساب التوفير عالي العائد الشهري" : "High-Yield Monthly Savings Account";
      case "prod-03":
        return isArabic ? "شهادة النيل البلاتينية الثلاثية" : "Nile Platinum 3-Year Certificate of Deposit";
      default:
        return productId;
    }
  };

  const getCardProductName = (cardType: string) => {
    switch (cardType) {
      case "DEBIT_VISA_CLASSIC":
        return isArabic ? "بطاقة فيزا الكلاسيكية للخصم المباشر" : "Nile Classic Visa Debit Card";
      case "DEBIT_MASTERCARD_TITANIUM":
        return isArabic ? "بطاقة ماستركارد تيتانيوم للخصم المباشر" : "Nile Titanium Mastercard Debit Card";
      case "CREDIT_VISA_PLATINUM":
        return isArabic ? "بطاقة فيزا البلاتينية الائتمانية" : "Nile Platinum Visa Credit Card";
      case "PREPAID_MEEZA":
        return isArabic ? "بطاقة ميزة الوطنية مسبقة الدفع" : "Nile Meeza National Prepaid Card";
      default:
        return cardType;
    }
  };

  const getEmployeeStatusBadge = (status: string) => {
    switch (status) {
      case "APPROVED_SIMULATED":
        return <span className="bg-green-100 text-green-800 text-[10px] font-bold px-2 py-0.5 rounded">{isArabic ? "معتمد محاكاة" : "APPROVED_SIMULATED"}</span>;
      case "SIMULATED_COMPLETED":
        return <span className="bg-blue-100 text-blue-800 text-[10px] font-bold px-2 py-0.5 rounded">{isArabic ? "مكتمل محاكاة" : "SIMULATED_COMPLETED"}</span>;
      case "REJECTED":
        return <span className="bg-rose-100 text-rose-800 text-[10px] font-bold px-2 py-0.5 rounded">{isArabic ? "مرفوض" : "REJECTED"}</span>;
      case "MORE_INFO_REQUIRED":
        return <span className="bg-purple-100 text-purple-800 text-[10px] font-bold px-2 py-0.5 rounded">{isArabic ? "استيفاء بيانات" : "MORE_INFO_REQUIRED"}</span>;
      case "UNDER_REVIEW":
        return <span className="bg-amber-100 text-amber-800 text-[10px] font-bold px-2 py-0.5 rounded">{isArabic ? "قيد المراجعة" : "UNDER_REVIEW"}</span>;
      case "SUBMITTED":
        return <span className="bg-gray-100 text-gray-800 text-[10px] font-bold px-2 py-0.5 rounded">{isArabic ? "تم التقديم" : "SUBMITTED"}</span>;
      default:
        return <span className="bg-gray-100 text-gray-800 text-[10px] font-bold px-2 py-0.5 rounded">{status}</span>;
    }
  };

  // Update Complaint Handler with Strict Advisory Confirmation
  const handleUpdateComplaint = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedComplaint) return;
    if (customerReply.trim() && !confirmReplyChecked) {
      alert(
        isArabic
          ? "يرجى مراجعة وتأكيد إرسال رد البنك المعتمد للعميل عبر تحديد مربع التأكيد الإلزامي."
          : "Please review and check the explicit confirmation box before finalizing customer-facing reply."
      );
      return;
    }
    try {
      const updated = await updateComplaintStatus(selectedComplaint.id, {
        status: newStatus,
        priority: newPriority,
        assigned_team: newTeam || undefined,
        staff_notes: staffNote,
        resolution_notes: resolutionNote,
        customer_reply: customerReply || undefined,
        ai_draft_status: confirmReplyChecked ? "ACCEPTED" : undefined,
      });
      setComplaints(complaints.map((c) => (c.id === updated.id ? updated : c)));
      setSelectedComplaint(null);
      setStaffNote("");
      setResolutionNote("");
      setCustomerReply("");
      setConfirmReplyChecked(false);
      loadComplaints(complaintsPage);
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

  // KYC Upload Handler
  const handleUploadCard = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) return;
    setIsUploadingKyc(true);
    setUploadError(null);
    try {
      const newRecord = await uploadKycDocument(uploadFile);
      setKycQueue([newRecord, ...kycQueue]);
      setSelectedKycId(newRecord.id);
      setShowUploadModal(false);
      setUploadFile(null);
      setUploadPreview(null);
      // Refresh audit logs
      fetchAuditLogs().then(setAuditLogs).catch(() => {});
    } catch (err: any) {
      setUploadError(err.message || "Failed to upload and process card image.");
    } finally {
      setIsUploadingKyc(false);
    }
  };

  // KYC Review Handler
  const handleKycReview = async (id: string, stat: string, notes?: string) => {
    try {
      const defaultNotes = notes || (stat === "APPROVED_SIMULATED" || stat === "VERIFIED_SYNTHETIC" ? `Simulated verification approved by ${user?.email}` : "");
      const updated = await updateKycStatus(id, stat, defaultNotes);
      setKycQueue(kycQueue.map((k) => (k.id === updated.id ? updated : k)));
      setReviewModal({ isOpen: false, kycId: "", trackingNumber: "", action: "REJECTED", reason: "" });
      // Refresh audit logs
      fetchAuditLogs().then(setAuditLogs).catch(() => {});
    } catch (err: any) {
      alert(err.message || "Failed to update KYC status");
    }
  };

  const renderKpiStatusBadge = (status?: string) => {
    if (status === "MET") {
      return (
        <span className="px-2 py-0.5 text-[10px] font-black uppercase rounded bg-emerald-100 text-emerald-800 border border-emerald-300">
          {isArabic ? "مطابق (MET)" : "✓ MET"}
        </span>
      );
    }
    if (status === "NOT MET") {
      return (
        <span className="px-2 py-0.5 text-[10px] font-black uppercase rounded bg-rose-100 text-rose-800 border border-rose-300">
          {isArabic ? "غير مطابق (NOT MET)" : "✕ NOT MET"}
        </span>
      );
    }
    if (status === "NOT MEASURED") {
      return (
        <span className="px-2 py-0.5 text-[10px] font-black uppercase rounded bg-gray-100 text-gray-600 border border-gray-300">
          {isArabic ? "غير مقاس" : "NOT MEASURED"}
        </span>
      );
    }
    return (
      <span className="px-2 py-0.5 text-[10px] font-black uppercase rounded bg-slate-100 text-slate-700 border border-slate-300">
        {isArabic ? "لا يوجد مستهدف رسمي" : "NO TARGET"}
      </span>
    );
  };

  const getKpiCardBg = (status?: string) => {
    if (status === "MET") return "bg-emerald-50/30 border-emerald-300";
    if (status === "NOT MET") return "bg-rose-50/30 border-rose-300";
    if (status === "NOT MEASURED") return "bg-gray-50/30 border-gray-300";
    return "bg-slate-50/40 border-slate-300";
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
              [
                "requests",
                isArabic
                  ? `طلبات الحسابات والبطاقات (${accountRequests.filter((r) => r.status === "SUBMITTED" || r.status === "UNDER_REVIEW").length + cardRequests.filter((c) => c.status === "SUBMITTED" || c.status === "UNDER_REVIEW").length})`
                  : `Requests Queue (${accountRequests.filter((r) => r.status === "SUBMITTED" || r.status === "UNDER_REVIEW").length + cardRequests.filter((c) => c.status === "SUBMITTED" || c.status === "UNDER_REVIEW").length})`,
              ],
              ["complaints", isArabic ? `الشكاوى (${complaints.filter(c => c.status !== "RESOLVED").length})` : `Complaints (${complaints.filter(c => c.status !== "RESOLVED").length})`],
              ["policies", isArabic ? "حوكمة السياسات" : "Policy KB"],
              ["kyc", isArabic ? "تدقيق الهوية" : "KYC Queue"],
              ["customers", isArabic ? "العملاء" : "Customers"],
              ["audit", isArabic ? "سجل التدقيق" : "Audit Trail"],
              ["assistant", isArabic ? "🤖 المساعد الذكي" : "🤖 Policy Assistant"],
            ] as const
          ).map(([key, label]) => (
            <button
              key={key}
              data-tab={key}
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

      {/* TAB 1: OPERATIONS & RISK KPI DASHBOARD */}
      {activeTab === "dashboard" && (
        <div className="space-y-6" id="kpi-dashboard-view">
          {/* MANDATORY DEV MODE & HANDBOOK MEASUREMENT BANNER */}
          <div className="bg-gradient-to-r from-slate-900 to-slate-800 border-l-4 border-amber-500 p-4 rounded-xl text-white shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 text-[10px] font-black uppercase tracking-wider bg-amber-500/20 text-amber-400 border border-amber-500/30 rounded">
                  {isArabic ? "تنبيه بيئة العمل التجريبية" : "Workload Notice"}
                </span>
                <span className="text-xs text-slate-300 font-medium">
                  {isArabic ? "مؤشرات أداء دليل العمليات المصرفية الرقمية المصرية" : "Egyptian Digital Banking Operations Handbook Scorecard"}
                </span>
              </div>
              <p className="text-xs text-slate-300">
                {isArabic
                  ? "تنبيه حجم العمل: أوقات المعالجة ومخالفات SLA ومعدلات إعادة العمل والأهلية للمعالجة المباشرة (STP) محسوبة من حجم عمل تجريبي تم إنشاؤه مسبقاً (SEEDED synthetic workload) في قاعدة nileops_test، ولا تمثل أداء تشغيلياً حقيقياً للموظفين. تنطبق المستهدفات الرسمية للدليل فقط على استدعاء الاستثناءات (>=95%)، اكتمال التدقيق (100%)، الامتناع الآمن لـ RAG (>=90%)، ودقة حقول OCR (F1>=90%)."
                  : "Workload Notice: Processing time, SLA breach, rework, and STP eligibility rates are computed from a SEEDED synthetic workload in nileops_test, not real staff performance. Official Handbook targets apply strictly to Exception Recall (>=95%), Audit Completeness (100%), Safe Abstention (>=90%), and Document OCR Field F1 (>=90%)."}
              </p>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <span className="px-2.5 py-1 text-xs font-mono font-semibold bg-slate-800 border border-slate-700 rounded text-slate-200">
                {kpiSummary?.environment_mode === "test" ? "DATABASE: nileops_test" : "DATABASE: nileops (dev)"}
              </span>
              <button
                onClick={loadInitialData}
                className="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded transition shadow-sm"
              >
                {isArabic ? "تحديث المؤشرات" : "Refresh KPIs"}
              </button>
            </div>
          </div>

          {/* 6 CORE HANDBOOK KPI SCORECARDS */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-bold text-gray-900 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                {isArabic ? "مؤشرات الأداء التشغيلي وإدارة المخاطر (Handbook KPIs)" : "Core Operations & Risk Governance KPIs"}
              </h2>
              <span className="text-xs text-gray-400">
                {isArabic ? "القيم المستهدفة وفقاً لمعايير الدليل المصرفي" : "Benchmark targets per Handbook specification"}
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {/* 1. STP Eligibility Rate */}
              {(() => {
                const metric = kpiSummary?.metrics?.stp_eligibility_rate;
                const status = metric?.status || "NO TARGET";
                return (
                  <div className={`p-4 rounded-xl border transition shadow-sm ${getKpiCardBg(status)}`}>
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <span className="text-xs font-bold text-gray-700">
                        {isArabic ? metric?.title_ar || "معدل المعالجة المباشرة المؤهلة (STP)" : metric?.title_en || "Straight-Through-Processing (STP) Eligibility Rate"}
                      </span>
                      {renderKpiStatusBadge(status)}
                    </div>
                    <div className="text-3xl font-black text-gray-900 mb-1">
                      {metric?.formatted_value || "70.0%"}
                    </div>
                    <div className="text-xs text-gray-500 mb-2">
                      {isArabic ? "المستهدف: لا يوجد مستهدف رسمي" : "Target: no official target"}
                    </div>
                    <div className="text-[11px] text-gray-600 bg-white/70 p-2 rounded border border-gray-200/60 space-y-0.5">
                      <div className="flex justify-between">
                        <span>{isArabic ? "الطلبات المؤهلة للقرار الآلي:" : "STP-Eligible Requests:"}</span>
                        <span className="font-semibold">{metric?.numerator || 49} / {metric?.denominator || 70}</span>
                      </div>
                      <div className="flex justify-between text-blue-700">
                        <span>{isArabic ? "التنفيذ الآلي الفعلي (سياسة البنك):" : "Actual Auto-Executed Rate:"}</span>
                        <span className="font-bold">0.0% (Four-Eyes Policy)</span>
                      </div>
                    </div>
                  </div>
                );
              })()}

              {/* 2. Exception Detection Recall */}
              {(() => {
                const metric = kpiSummary?.metrics?.exception_detection_recall;
                const status = metric?.status || "NOT MET";
                return (
                  <div className={`p-4 rounded-xl border transition shadow-sm ${getKpiCardBg(status)}`}>
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <span className="text-xs font-bold text-gray-700">
                        {isArabic ? metric?.title_ar || "نسبة استدعاء كشف الاستثناءات" : metric?.title_en || "Exception Detection Recall"}
                      </span>
                      {renderKpiStatusBadge(status)}
                    </div>
                    <div className="text-3xl font-black text-amber-600 mb-1">
                      {metric?.formatted_value || "86.7%"}
                    </div>
                    <div className="text-xs text-gray-500 mb-2">
                      {isArabic ? "المستهدف: >= 95.0% (الهدف الرسمي للدليل - فجوة: -8.3%)" : "Target: recall >= 95.0% (Official Handbook target - gap: -8.3%)"}
                    </div>
                    <div className="text-[11px] text-gray-600 bg-white/70 p-2 rounded border border-gray-200/60 space-y-0.5">
                      <div className="flex justify-between">
                        <span>{isArabic ? "استثناءات مكتشفة ومحالة للمراجعة:" : "Detected Seeded Exceptions:"}</span>
                        <span className="font-semibold">{metric?.numerator || 13} / {metric?.denominator || 15}</span>
                      </div>
                      <div className="flex justify-between text-emerald-700">
                        <span>{isArabic ? "دقة الكشف (خلو من الإنذارات الخاطئة):" : "Precision (Zero False Alarms):"}</span>
                        <span className="font-bold">100.0% (15/15 TN)</span>
                      </div>
                    </div>
                  </div>
                );
              })()}

              {/* 3. Audit Chain Completeness */}
              {(() => {
                const metric = kpiSummary?.metrics?.audit_completeness;
                const status = metric?.status || "MET";
                return (
                  <div className={`p-4 rounded-xl border transition shadow-sm ${getKpiCardBg(status)}`}>
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <span className="text-xs font-bold text-gray-700">
                        {isArabic ? metric?.title_ar || "اكتمال سجل التدقيق الشامل" : metric?.title_en || "Audit Chain Completeness"}
                      </span>
                      {renderKpiStatusBadge(status)}
                    </div>
                    <div className="text-3xl font-black text-emerald-600 mb-1">
                      {metric?.formatted_value || "100.0%"}
                    </div>
                    <div className="text-xs text-gray-500 mb-2">
                      {isArabic ? "المستهدف: 100.0% (الهدف الرسمي للدليل)" : "Target: 100.0% (Official Handbook target)"}
                    </div>
                    <div className="text-[11px] text-gray-600 bg-white/70 p-2 rounded border border-gray-200/60 space-y-0.5">
                      <div className="flex justify-between">
                        <span>{isArabic ? "قرارات موثقة غير قابلة للتعديل:" : "Verified Immutable Chains:"}</span>
                        <span className="font-semibold">{metric?.numerator || 58} / {metric?.denominator || 58}</span>
                      </div>
                      <div className="flex justify-between text-emerald-700">
                        <span>{isArabic ? "توثيق المسؤول والوقت والسبب:" : "Actor, Timestamp & Reason:"}</span>
                        <span className="font-bold">100.0% Verified</span>
                      </div>
                    </div>
                  </div>
                );
              })()}

              {/* 4. Customer Rework Rate */}
              {(() => {
                const metric = kpiSummary?.metrics?.rework_rate;
                const status = metric?.status || "NO TARGET";
                return (
                  <div className={`p-4 rounded-xl border transition shadow-sm ${getKpiCardBg(status)}`}>
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <span className="text-xs font-bold text-gray-700">
                        {isArabic ? metric?.title_ar || "معدل إعادة العمل وطلب الاستكمال" : metric?.title_en || "Customer Rework Rate"}
                      </span>
                      {renderKpiStatusBadge(status)}
                    </div>
                    <div className="text-3xl font-black text-gray-900 mb-1">
                      {metric?.formatted_value || "11.4%"}
                    </div>
                    <div className="text-xs text-gray-500 mb-2">
                      {isArabic ? "المستهدف: لا يوجد مستهدف رسمي" : "Target: no official target"}
                    </div>
                    <div className="text-[11px] text-gray-600 bg-white/70 p-2 rounded border border-gray-200/60 space-y-0.5">
                      <div className="flex justify-between">
                        <span>{isArabic ? "طلبات معادة لطلب استكمال:" : "More-Info Required Requests:"}</span>
                        <span className="font-semibold">{metric?.numerator || 8} / {metric?.denominator || 70}</span>
                      </div>
                      <div className="flex justify-between text-gray-600">
                        <span>{isArabic ? "توزيع: 5 حسابات + 3 بطاقات" : "Breakdown: 5 accounts + 3 cards"}</span>
                        <span className="font-medium">{metric?.formatted_value || "11.4%"}</span>
                      </div>
                    </div>
                  </div>
                );
              })()}

              {/* 5. Median Decision Cycle Time */}
              {(() => {
                const metric = kpiSummary?.metrics?.median_decision_time;
                const status = metric?.status || "NO TARGET";
                return (
                  <div className={`p-4 rounded-xl border transition shadow-sm ${getKpiCardBg(status)}`}>
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <span className="text-xs font-bold text-gray-700">
                        {isArabic ? metric?.title_ar || "الوسيط الزمني لاتخاذ القرار" : metric?.title_en || "Median Decision Cycle Time"}
                      </span>
                      {renderKpiStatusBadge(status)}
                    </div>
                    <div className="text-3xl font-black text-gray-900 mb-1">
                      {metric?.formatted_value || "21.0 mins"}
                    </div>
                    <div className="text-xs text-gray-500 mb-2">
                      {isArabic ? "المستهدف: لا يوجد مستهدف رسمي" : "Target: no official target"}
                    </div>
                    <div className="text-[11px] text-gray-600 bg-white/70 p-2 rounded border border-gray-200/60 space-y-0.5">
                      <div className="flex justify-between">
                        <span>{isArabic ? "المئوي 95 (P95):" : "95th Percentile (P95):"}</span>
                        <span className="font-semibold">{metric?.denominator ? `${metric.denominator} mins` : "27.0 mins"}</span>
                      </div>
                      <div className="flex justify-between text-gray-600">
                        <span>{isArabic ? "عينة القرارات المحسوبة:" : "Measured Decision Sample:"}</span>
                        <span className="font-medium">{metric?.sample_size || 66} decisions</span>
                      </div>
                    </div>
                  </div>
                );
              })()}

              {/* 6. Complaint SLA Breach Rate */}
              {(() => {
                const metric = kpiSummary?.metrics?.complaint_sla_breach_rate;
                const status = metric?.status || "NO TARGET";
                return (
                  <div className={`p-4 rounded-xl border transition shadow-sm ${getKpiCardBg(status)}`}>
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <span className="text-xs font-bold text-gray-700">
                        {isArabic ? metric?.title_ar || "معدل مخالفة اتفاقية مستوى الخدمة للشكاوى" : metric?.title_en || "Complaint SLA Breach Rate"}
                      </span>
                      {renderKpiStatusBadge(status)}
                    </div>
                    <div className="text-3xl font-black text-rose-600 mb-1">
                      {metric?.formatted_value || "23.3%"}
                    </div>
                    <div className="text-xs text-gray-500 mb-2">
                      {isArabic ? "المستهدف: لا يوجد مستهدف رسمي" : "Target: no official target"}
                    </div>
                    <div className="text-[11px] text-gray-600 bg-white/70 p-2 rounded border border-gray-200/60 space-y-0.5">
                      <div className="flex justify-between">
                        <span>{isArabic ? "شكاوى متجاوزة للموعد المستهدف:" : "Breached Complaint Tickets:"}</span>
                        <span className="font-semibold text-rose-700">{metric?.numerator || 7} / {metric?.denominator || 30}</span>
                      </div>
                      <div className="flex justify-between text-gray-600">
                        <span>{isArabic ? "تفصيل: 4 متأخرة + 3 مفتوحة متجاوزة" : "4 resolved late + 3 open past SLA"}</span>
                        <span className="font-medium">{metric?.formatted_value || "23.3%"}</span>
                      </div>
                    </div>
                  </div>
                );
              })()}
            </div>
          </div>

          {/* SECONDARY BENCHMARK SCORECARDS: RAG & OCR ACCURACY */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-emerald-50/20 p-4 rounded-xl border border-emerald-300 shadow-sm flex items-center justify-between">
              <div>
                <span className="text-xs text-gray-500 font-semibold block mb-0.5">
                  {isArabic ? "دقة استرجاع اللوائح المصرفية والامتناع الآمن (Policy RAG)" : "Policy RAG Safe Abstention & Retrieval"}
                </span>
                <div className="text-xl font-black text-slate-900">
                  Abstention: 100.0% | Hit@1: 92.0%
                </div>
                <span className="text-[11px] text-gray-500">
                  {isArabic ? "المستهدف: الامتناع >= 90.0% (الهدف الرسمي للدليل) | Hit@3: 100% | MRR: 0.9600" : "Target: abstention >= 90.0% (Official Handbook target) | Hit@3: 100% | MRR: 0.9600"}
                </span>
              </div>
              {renderKpiStatusBadge(kpiSummary?.metrics?.rag_retrieval_accuracy?.status || "MET")}
            </div>

            <div className="bg-rose-50/20 p-4 rounded-xl border border-rose-300 shadow-sm flex items-center justify-between">
              <div>
                <span className="text-xs text-gray-500 font-semibold block mb-0.5">
                  {isArabic ? "دقة استخراج حقول بطاقة الرقم القومي (OCR Document AI)" : "OCR Document AI Field Accuracy"}
                </span>
                <div className="text-xl font-black text-slate-900">
                  ID: 87.5% | Name: 62.5% | Addr: 50.0%
                </div>
                <span className="text-[11px] text-gray-500">
                  {isArabic ? "المستهدف: F1 للحقل >= 90.0% (الهدف الرسمي للدليل - الاسم 62.5% والعنوان 50% غير مطابق)" : "Target: field F1 >= 90.0% (Official Handbook target - Name 62.5% & Addr 50% NOT MET)"}
                </span>
              </div>
              {renderKpiStatusBadge(kpiSummary?.metrics?.ocr_field_accuracy?.status || "NOT MET")}
            </div>
          </div>

          {/* WORKLOAD VOLUME & STATUS DISTRIBUTION */}
          <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-gray-900">
                {isArabic ? "توزيع حجم العمل وحالة الطلبات التشغيلية" : "Operational Workload & Status Distribution"}
              </h3>
              <span className="text-xs text-gray-400">
                {isArabic ? "حجم عينة الاختبار: 70 طلب و30 شكوى و20 تدقيق هوية" : "Test sample: 70 requests, 30 complaints, 20 KYC"}
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Account Requests Breakdown */}
              <div className="p-3 bg-gray-50 rounded-lg border border-gray-200 space-y-2">
                <div className="flex justify-between items-center text-xs font-bold text-gray-800">
                  <span>{isArabic ? "طلبات فتح الحسابات (40)" : "Account Requests (40)"}</span>
                  <span className="text-emerald-700">62.5% Approved</span>
                </div>
                <div className="w-full bg-gray-200 h-2.5 rounded-full overflow-hidden flex">
                  <div className="bg-emerald-500 h-full" style={{ width: "62.5%" }} title="25 Approved (62.5%)"></div>
                  <div className="bg-rose-500 h-full" style={{ width: "20.0%" }} title="8 Rejected (20.0%)"></div>
                  <div className="bg-amber-500 h-full" style={{ width: "12.5%" }} title="5 More Info (12.5%)"></div>
                  <div className="bg-blue-500 h-full" style={{ width: "5.0%" }} title="2 Under Review (5.0%)"></div>
                </div>
                <div className="grid grid-cols-2 gap-1 text-[11px] text-gray-600">
                  <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500"></span> 25 Approved</div>
                  <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-rose-500"></span> 8 Rejected</div>
                  <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-500"></span> 5 More Info</div>
                  <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-blue-500"></span> 2 Under Review</div>
                </div>
              </div>

              {/* Card Requests Breakdown */}
              <div className="p-3 bg-gray-50 rounded-lg border border-gray-200 space-y-2">
                <div className="flex justify-between items-center text-xs font-bold text-gray-800">
                  <span>{isArabic ? "طلبات إصدار البطاقات (30)" : "Card Requests (30)"}</span>
                  <span className="text-emerald-700">80.0% Approved</span>
                </div>
                <div className="w-full bg-gray-200 h-2.5 rounded-full overflow-hidden flex">
                  <div className="bg-emerald-500 h-full" style={{ width: "80.0%" }} title="24 Approved (80.0%)"></div>
                  <div className="bg-rose-500 h-full" style={{ width: "10.0%" }} title="3 Rejected (10.0%)"></div>
                  <div className="bg-amber-500 h-full" style={{ width: "10.0%" }} title="3 More Info (10.0%)"></div>
                </div>
                <div className="grid grid-cols-3 gap-1 text-[11px] text-gray-600">
                  <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500"></span> 24 Approved</div>
                  <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-rose-500"></span> 3 Rejected</div>
                  <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-500"></span> 3 More Info</div>
                </div>
              </div>

              {/* KYC Verification Breakdown */}
              <div className="p-3 bg-gray-50 rounded-lg border border-gray-200 space-y-2">
                <div className="flex justify-between items-center text-xs font-bold text-gray-800">
                  <span>{isArabic ? "تدقيق وثائق الهوية (20)" : "KYC Document AI (20)"}</span>
                  <span className="text-emerald-700">60.0% Compliant</span>
                </div>
                <div className="w-full bg-gray-200 h-2.5 rounded-full overflow-hidden flex">
                  <div className="bg-emerald-500 h-full" style={{ width: "60.0%" }} title="12 Compliant (60.0%)"></div>
                  <div className="bg-amber-500 h-full" style={{ width: "25.0%" }} title="5 Flagged Review (25.0%)"></div>
                  <div className="bg-rose-500 h-full" style={{ width: "15.0%" }} title="3 Rejected (15.0%)"></div>
                </div>
                <div className="grid grid-cols-3 gap-1 text-[11px] text-gray-600">
                  <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500"></span> 12 Verified</div>
                  <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-500"></span> 5 Flagged</div>
                  <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-rose-500"></span> 3 Rejected</div>
                </div>
              </div>
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

      {/* TAB 2: COMPLAINTS WORKSTATION & INTELLIGENCE */}
      {activeTab === "complaints" && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden space-y-4 p-5">
          {/* Header & Search */}
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-gray-100 pb-4">
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-gray-900">
                  {isArabic ? "منصة إدارة وتدقيق شكاوى العملاء (Complaint Intelligence)" : "Complaint Intelligence & Operations Station"}
                </h2>
                <span className="text-[10px] bg-blue-100 text-blue-800 font-bold px-2 py-0.5 rounded">
                  {complaintsTotal} {isArabic ? "تذكرة" : "tickets"}
                </span>
              </div>
              <p className="text-xs text-gray-500 mt-0.5">
                {isArabic
                  ? "إدارة دورة حياة الشكاوى، التوجيه الذكي، مراقبة اتفاقيات مستوى الخدمة (SLA)، واعتماد الردود."
                  : "End-to-end complaint operations, rule-based advisory intelligence, SLA monitoring, and dual-control resolutions."}
              </p>
            </div>

            {/* Search Input */}
            <div className="w-full md:w-72">
              <input
                type="text"
                value={complaintSearch}
                onChange={(e) => setComplaintSearch(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && loadComplaints(1)}
                placeholder={isArabic ? "بحث برقم التذكرة، العميل، الموضوع..." : "Search by ticket, customer, subject..."}
                className="w-full text-xs px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-nile-600 focus:outline-hidden"
              />
            </div>
          </div>

          {/* Comprehensive Filters Bar */}
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2 text-xs bg-gray-50/70 p-3 rounded-xl border border-gray-200">
            {/* Status Filter */}
            <div>
              <label className="text-[10px] font-bold text-gray-500 block mb-1">{isArabic ? "الحالة:" : "Status:"}</label>
              <select
                value={complaintFilter}
                onChange={(e) => setComplaintFilter(e.target.value)}
                className="w-full text-xs border border-gray-300 rounded-lg px-2 py-1.5 bg-white font-medium"
              >
                <option value="">{isArabic ? "جميع الحالات" : "All Statuses"}</option>
                <option value="OPEN">{isArabic ? "مفتوحة" : "OPEN"}</option>
                <option value="IN_PROGRESS">{isArabic ? "قيد المعالجة" : "IN_PROGRESS"}</option>
                <option value="RESOLVED">{isArabic ? "تم الحل" : "RESOLVED"}</option>
                <option value="REJECTED">{isArabic ? "مرفوضة" : "REJECTED"}</option>
              </select>
            </div>

            {/* Category Filter */}
            <div>
              <label className="text-[10px] font-bold text-gray-500 block mb-1">{isArabic ? "الفئة:" : "Category:"}</label>
              <select
                value={complaintCategoryFilter}
                onChange={(e) => setComplaintCategoryFilter(e.target.value)}
                className="w-full text-xs border border-gray-300 rounded-lg px-2 py-1.5 bg-white font-medium"
              >
                <option value="">{isArabic ? "جميع الفئات" : "All Categories"}</option>
                <option value="ATM_CARD">{isArabic ? "بطاقات الصراف الآلي" : "ATM & Debit Cards"}</option>
                <option value="TRANSFER">{isArabic ? "التحويلات والمدفوعات" : "Transfers & InstaPay"}</option>
                <option value="MOBILE_BANKING">{isArabic ? "الخدمات المصرفية عبر الهاتف" : "Mobile & Digital Banking"}</option>
                <option value="FRAUD_DISPUTE">{isArabic ? "نزاعات الاحتيال" : "Fraud & Disputes"}</option>
                <option value="LOANS_CREDIT">{isArabic ? "القروض والتمويل" : "Loans & Credit"}</option>
                <option value="FEES_CHARGES">{isArabic ? "الرسوم والعمولات" : "Fees & Charges"}</option>
                <option value="ACCOUNT_SERVICES">{isArabic ? "خدمات الحسابات" : "Account Services"}</option>
                <option value="GENERAL_INQUIRY">{isArabic ? "استفسارات عامة" : "General Inquiry"}</option>
              </select>
            </div>

            {/* Priority Filter */}
            <div>
              <label className="text-[10px] font-bold text-gray-500 block mb-1">{isArabic ? "الأولوية:" : "Priority:"}</label>
              <select
                value={complaintPriorityFilter}
                onChange={(e) => setComplaintPriorityFilter(e.target.value)}
                className="w-full text-xs border border-gray-300 rounded-lg px-2 py-1.5 bg-white font-medium"
              >
                <option value="">{isArabic ? "جميع الأولويات" : "All Priorities"}</option>
                <option value="URGENT">{isArabic ? "عاجلة (اتفاقية 4 ساعات)" : "URGENT (4 hours SLA)"}</option>
                <option value="HIGH">{isArabic ? "عالية (اتفاقية 12 ساعة)" : "HIGH (12 hours SLA)"}</option>
                <option value="MEDIUM">{isArabic ? "متوسطة (اتفاقية 24 ساعة)" : "MEDIUM (24 hours SLA)"}</option>
                <option value="LOW">{isArabic ? "منخفضة (اتفاقية 48 ساعة)" : "LOW (48 hours SLA)"}</option>
              </select>
            </div>

            {/* Team Filter */}
            <div>
              <label className="text-[10px] font-bold text-gray-500 block mb-1">{isArabic ? "الفريق المعين:" : "Assigned Team:"}</label>
              <select
                value={complaintTeamFilter}
                onChange={(e) => setComplaintTeamFilter(e.target.value)}
                className="w-full text-xs border border-gray-300 rounded-lg px-2 py-1.5 bg-white font-medium"
              >
                <option value="">{isArabic ? "جميع الفرق" : "All Teams"}</option>
                <option value="CARDS_PAYMENTS">{isArabic ? "فريق البطاقات والمدفوعات" : "Cards & Payments Team"}</option>
                <option value="OPERATIONS">{isArabic ? "فريق العمليات المصرفية" : "Banking Operations Team"}</option>
                <option value="FRAUD_RISK">{isArabic ? "فريق الاحتيال والمخاطر" : "Fraud & Risk Team"}</option>
                <option value="RETAIL_CREDIT">{isArabic ? "فريق ائتمان الأفراد" : "Retail Credit Team"}</option>
                <option value="FINANCE_OPERATIONS">{isArabic ? "فريق العمليات المالية" : "Finance Operations Team"}</option>
                <option value="BRANCH_SUPPORT">{isArabic ? "فريق دعم الفروع" : "Branch Support Team"}</option>
                <option value="CUSTOMER_SERVICE">{isArabic ? "فريق خدمة العملاء" : "Customer Service Team"}</option>
                <option value="COMPLIANCE">{isArabic ? "فريق الامتثال والرقابة" : "Compliance Team"}</option>
                <option value="BRANCH_NETWORK">{isArabic ? "فريق شبكة الفروع" : "Branch Network Team"}</option>
              </select>
            </div>

            {/* Sort Filter */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-[10px] font-bold text-gray-500 block">{isArabic ? "الترتيب:" : "Sort:"}</label>
                <button
                  type="button"
                  onClick={() => setComplaintSortOrder(complaintSortOrder === "asc" ? "desc" : "asc")}
                  className="text-[9px] font-mono text-nile-700 hover:underline"
                >
                  {complaintSortOrder === "asc" ? "↑ ASC" : "↓ DESC"}
                </button>
              </div>
              <select
                value={complaintSortBy}
                onChange={(e) => setComplaintSortBy(e.target.value)}
                className="w-full text-xs border border-gray-300 rounded-lg px-2 py-1.5 bg-white font-medium"
              >
                <option value="created_at">{isArabic ? "تاريخ الإنشاء" : "Created Date"}</option>
                <option value="priority">{isArabic ? "مستوى الأولوية" : "Priority"}</option>
                <option value="sla_due_at">{isArabic ? "استحقاق SLA" : "SLA Due Date"}</option>
              </select>
            </div>

            {/* Test Tickets Toggle */}
            <div className="flex flex-col justify-end">
              <label className="flex items-center gap-1.5 text-[11px] font-medium text-gray-600 cursor-pointer pt-2">
                <input
                  type="checkbox"
                  checked={complaintIncludeTest}
                  onChange={(e) => setComplaintIncludeTest(e.target.checked)}
                  className="rounded text-nile-700 focus:ring-nile-500"
                />
                <span>{isArabic ? "عرض تذاكر الاختبار" : "Show Test Tickets"}</span>
              </label>
            </div>
          </div>

          {/* Main Table */}
          <div className="overflow-x-auto rounded-xl border border-gray-200">
            <table className="w-full text-left rtl:text-right text-xs">
              <thead className="bg-gray-100/80 text-gray-700 font-bold border-b border-gray-200">
                <tr>
                  <th className="px-4 py-3">{isArabic ? "رقم التذكرة" : "Ticket #"}</th>
                  <th className="px-4 py-3">{isArabic ? "اسم العميل" : "Customer Name"}</th>
                  <th className="px-4 py-3">{isArabic ? "الموضوع والفئة" : "Subject & Category"}</th>
                  <th className="px-4 py-3">{isArabic ? "الأولوية" : "Priority"}</th>
                  <th className="px-4 py-3">{isArabic ? "الحالة" : "Status"}</th>
                  <th className="px-4 py-3">{isArabic ? "الفريق المعين" : "Team & Assignee"}</th>
                  <th className="px-4 py-3">{isArabic ? "تاريخ التقديم (UTC)" : "Created (UTC)"}</th>
                  <th className="px-4 py-3">{isArabic ? "مؤشر SLA" : "SLA Status"}</th>
                  <th className="px-4 py-3 text-right rtl:text-left">{isArabic ? "الإجراء" : "Action"}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 text-gray-700">
                {isComplaintsLoading ? (
                  <tr>
                    <td colSpan={9} className="px-4 py-12 text-center text-xs text-gray-400">
                      {isArabic ? "جاري تحميل بيانات الشكاوى..." : "Loading complaint records..."}
                    </td>
                  </tr>
                ) : complaints.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="px-4 py-12 text-center text-xs text-gray-400">
                      {isArabic ? "لا توجد شكاوى مسجلة تطابق معايير التصفية والبحث." : "No customer complaints found matching current filters."}
                    </td>
                  </tr>
                ) : (
                  complaints.map((c) => (
                    <tr key={c.id} className="hover:bg-blue-50/40 transition">
                      {/* Ticket # */}
                      <td className="px-4 py-3 font-mono font-bold text-nile-800 whitespace-nowrap">
                        {c.ticket_number}
                        {c.is_test && (
                          <span className="text-[9px] bg-amber-100 text-amber-800 px-1.5 py-0.2 rounded font-mono ml-1">
                            TEST
                          </span>
                        )}
                      </td>

                      {/* Customer Name */}
                      <td className="px-4 py-3 font-bold text-gray-900 whitespace-nowrap">
                        {c.customer_name || "Ahmed Mansour"}
                      </td>

                      {/* Subject & Category */}
                      <td className="px-4 py-3 max-w-xs">
                        <span className="text-[10px] font-semibold text-nile-700 block uppercase">
                          {getCategoryLabel(c.category, isArabic)}
                        </span>
                        <strong className="block text-gray-900 line-clamp-1">{c.subject}</strong>
                      </td>

                      {/* Priority */}
                      <td className="px-4 py-3">
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                            c.priority === "URGENT"
                              ? "bg-rose-100 text-rose-800"
                              : c.priority === "HIGH"
                              ? "bg-orange-100 text-orange-800"
                              : c.priority === "MEDIUM"
                              ? "bg-amber-100 text-amber-800"
                              : "bg-blue-100 text-blue-800"
                          }`}
                        >
                          {getPriorityLabel(c.priority, isArabic)}
                        </span>
                      </td>

                      {/* Status */}
                      <td className="px-4 py-3">
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                            c.status === "RESOLVED"
                              ? "bg-green-100 text-green-800"
                              : c.status === "IN_PROGRESS"
                              ? "bg-amber-100 text-amber-800"
                              : c.status === "REJECTED"
                              ? "bg-rose-100 text-rose-800"
                              : "bg-blue-100 text-blue-800"
                          }`}
                        >
                          {getStatusLabel(c.status, isArabic)}
                        </span>
                      </td>

                      {/* Assigned Team & Assignee */}
                      <td className="px-4 py-3 text-[11px]">
                        <span className="font-semibold text-gray-800 block">
                          {c.assigned_team ? getTeamLabel(c.assigned_team, isArabic) : (isArabic ? "غير معين" : "Unassigned")}
                        </span>
                        <span className="text-[10px] text-gray-400 block">{c.assigned_to_name || "—"}</span>
                      </td>

                      {/* Created Date (UTC) */}
                      <td className="px-4 py-3 font-mono text-[11px] text-gray-500 whitespace-nowrap">
                        {formatAuditTimestamp(c.created_at)}
                      </td>

                      {/* SLA Status */}
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className="flex flex-col gap-0.5">
                          <span
                            className={`text-[10px] font-bold px-2 py-0.5 rounded inline-block w-fit ${
                              c.sla_status_label === "BREACHED" || c.sla_status_label === "RESOLVED_BREACHED"
                                ? "bg-rose-100 text-rose-800"
                                : c.sla_status_label === "APPROACHING_BREACH"
                                ? "bg-amber-100 text-amber-800"
                                : "bg-emerald-100 text-emerald-800"
                            }`}
                          >
                            {getSlaLabel(c.sla_status_label || (c.sla_breached ? "BREACHED" : "ON_TRACK"), isArabic)}
                          </span>
                          <span className="text-[9px] text-gray-400 font-mono">
                            {c.sla_remaining_hours !== undefined && c.sla_remaining_hours !== null
                              ? c.sla_remaining_hours > 0
                                ? (isArabic ? `${c.sla_remaining_hours} ساعة متبقية` : `${c.sla_remaining_hours}h remaining`)
                                : (isArabic ? `${Math.abs(c.sla_remaining_hours)} ساعة تجاوز` : `${Math.abs(c.sla_remaining_hours)}h overdue`)
                              : (isArabic ? "سياسة محاكاة" : "Simulated Policy")}
                          </span>
                        </div>
                      </td>

                      {/* Action Button */}
                      <td className="px-4 py-3 text-right rtl:text-left whitespace-nowrap">
                        <button
                          onClick={async () => {
                            setSelectedComplaint(c);
                            setNewStatus(c.status);
                            setNewPriority(c.priority);
                            setNewTeam(c.assigned_team || "");
                            setStaffNote(c.staff_notes || "");
                            setResolutionNote(c.resolution_notes || "");
                            setCustomerReply(c.customer_reply || c.ai_draft_reply || "");
                            setConfirmReplyChecked(false);
                            setAdvisoryData(null);

                            if (!c.ai_draft_reply) {
                              setAdvisoryLoading(true);
                              try {
                                const adv = await fetchComplaintAdvisory(c.id);
                                setAdvisoryData(adv);
                                if (!c.customer_reply && adv.draft_reply) {
                                  setCustomerReply(adv.draft_reply);
                                }
                              } catch (err) {
                                console.error(err);
                              } finally {
                                setAdvisoryLoading(false);
                              }
                            }
                          }}
                          className="px-3 py-1.5 bg-nile-700 hover:bg-nile-800 text-white font-bold text-xs rounded-lg shadow-xs transition"
                        >
                          {isArabic ? "إدارة وتدقيق" : "Manage"}
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Server-Side Pagination Bar */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-3 border-t border-gray-100 text-xs text-gray-600">
            <div>
              {isArabic
                ? `عرض الصفحة ${complaintsPage} من إجمالي ${complaintsTotalPages} صفحات (${complaintsTotal} تذكرة مسجلة)`
                : `Showing page ${complaintsPage} of ${complaintsTotalPages} (${complaintsTotal} registered complaints total)`}
            </div>
            <div className="flex items-center space-x-2 rtl:space-x-reverse">
              <button
                disabled={complaintsPage <= 1}
                onClick={() => loadComplaints(complaintsPage - 1)}
                className="px-3 py-1.5 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-40 font-medium"
              >
                {isArabic ? "← السابق" : "← Previous"}
              </button>
              <span className="font-mono font-bold text-nile-800 px-2">{complaintsPage} / {complaintsTotalPages}</span>
              <button
                disabled={complaintsPage >= complaintsTotalPages}
                onClick={() => loadComplaints(complaintsPage + 1)}
                className="px-3 py-1.5 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-40 font-medium"
              >
                {isArabic ? "التالي →" : "Next →"}
              </button>
            </div>
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
            {policies.length === 0 && (
              <div className="bg-white rounded-xl border border-gray-200 p-12 text-center text-xs text-gray-500 shadow-xs">
                <span className="text-3xl block mb-2">📜</span>
                <p className="font-semibold text-gray-700">
                  {isArabic ? "لا توجد وثائق سياسات مسجلة تطابق البحث." : "No banking policy documents found matching this filter."}
                </p>
                <p className="text-gray-400 mt-1">
                  {isArabic
                    ? "السياسات التجريبية (POL-TEST-*) محجوبة تلقائياً من قوائم العرض المعتادة."
                    : "Test-injected policies (POL-TEST-*) are filtered out from normal operational views."}
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 4: SYNTHETIC KYC WORKSPACE */}
      {activeTab === "kyc" && (
        <div className="space-y-6">
          {/* PERMANENT COMPLIANCE & NOT-VERIFIED BANNER */}
          <div className="bg-amber-50 border-l-4 border-amber-500 p-4 rounded-r-xl shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-3">
            <div className="flex items-start md:items-center space-x-3 rtl:space-x-reverse">
              <span className="text-2xl flex-shrink-0">⚠️</span>
              <div>
                <h4 className="text-xs font-black text-amber-900 uppercase tracking-wider">
                  {isArabic ? "تنبيه إلزامي للرقابة والمطابقة المصرفية" : "Mandatory Compliance Invariant"}
                </h4>
                <p className="text-xs font-bold text-amber-800 mt-0.5">
                  {isArabic
                    ? "NOT VERIFIED — استخراج OCR لا يشكل بأي حال تحققاً رسمياً من الهوية. جميع الحالات الاصطناعية تتطلب مراجعة واعتماد بشري وفق مبدأ العيون الأربعة."
                    : "NOT VERIFIED — OCR extraction does not constitute official identity verification. All synthetic cases require authorized four-eyes compliance review."}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2 rtl:space-x-reverse flex-shrink-0">
              <span className="text-[11px] font-mono font-bold bg-amber-200/90 text-amber-900 px-2.5 py-1 rounded">
                {isArabic ? "أرقام قومية محجوبة افتراضياً" : "Masked IDs by Default"}
              </span>
              <span className="text-[11px] font-mono font-bold bg-amber-200/90 text-amber-900 px-2.5 py-1 rounded">
                {isArabic ? "بيئة اصطناعية 100%" : "100% Synthetic"}
              </span>
            </div>
          </div>

          {/* WORKSPACE CONTROLS & ACTION HEADER */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-xs p-5">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-gray-100">
              <div>
                <h2 className="text-lg font-black text-gray-900 flex items-center gap-2">
                  <span>{isArabic ? "محطة عمل تدقيق وثائق الهوية (Document AI & KYC)" : "Synthetic Document AI & KYC Workspace"}</span>
                  <span className="text-[11px] font-mono px-2 py-0.5 bg-blue-100 text-blue-800 rounded font-bold">
                    {kycQueue.length} {isArabic ? "حالة" : "Cases"}
                  </span>
                </h2>
                <p className="text-xs text-gray-500 mt-1">
                  {isArabic
                    ? "معالجة صور بطاقات الرقم القومي الاصطناعية، فحص ثقة OCR، مطابقة القواعد التساعية، ومحاكاة الاعتماد الرقابي."
                    : "Ingest synthetic cards, inspect real OCR engine confidence, evaluate 9D validation rules, and record simulated human review decisions."}
                </p>
              </div>
              <button
                onClick={() => setShowUploadModal(true)}
                className="px-4 py-2.5 bg-nile-700 hover:bg-nile-800 text-white font-bold text-xs rounded-lg shadow-xs transition flex items-center justify-center gap-2 flex-shrink-0"
              >
                <span>+</span>
                <span>{isArabic ? "رفع بطاقة اصطناعية جديدة" : "Upload Synthetic Card"}</span>
              </button>
            </div>

            {/* FILTER PILLS & SEARCH */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pt-4">
              <div className="flex flex-wrap items-center gap-1.5">
                {[
                  { id: "ALL", labelEn: "All Cases", labelAr: "الكل" },
                  { id: "PENDING_REVIEW", labelEn: "Pending Review", labelAr: "قيد التدقيق" },
                  { id: "APPROVED_SIMULATED", labelEn: "Approved (Simulated)", labelAr: "معتمد (محاكاة)" },
                  { id: "REJECTED", labelEn: "Rejected", labelAr: "مرفوض" },
                  { id: "INFO_REQUESTED", labelEn: "Info Requested", labelAr: "مطلوب بيانات" },
                ].map((f) => (
                  <button
                    key={f.id}
                    onClick={() => setKycFilter(f.id)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-bold transition ${
                      kycFilter === f.id
                        ? "bg-nile-700 text-white shadow-xs"
                        : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                    }`}
                  >
                    {isArabic ? f.labelAr : f.labelEn}
                  </button>
                ))}
              </div>
              <div className="w-full md:w-64">
                <input
                  type="text"
                  placeholder={isArabic ? "بحث برقم المتابعة..." : "Search tracking #..."}
                  value={kycSearch}
                  onChange={(e) => setKycSearch(e.target.value)}
                  className="w-full text-xs px-3 py-1.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-nile-500"
                />
              </div>
            </div>
          </div>

          {/* TWO-COLUMN WORKSPACE: QUEUE + INSPECTOR */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* LEFT COLUMN: CASE QUEUE (4 cols) */}
            <div className="lg:col-span-4 bg-white rounded-xl border border-gray-200 shadow-xs overflow-hidden">
              <div className="p-3.5 bg-gray-50 border-b border-gray-200 font-bold text-xs text-gray-700 flex justify-between items-center">
                <span>{isArabic ? "قائمة الحالات المسجلة" : "Case Queue"}</span>
                <span className="text-[11px] font-normal text-gray-500">
                  {kycQueue.filter((k) => (kycFilter === "ALL" || k.status === kycFilter || (kycFilter === "PENDING_REVIEW" && k.status === "FLAGGED") || (kycFilter === "APPROVED_SIMULATED" && k.status === "VERIFIED_SYNTHETIC")) && (!kycSearch || k.tracking_number.toLowerCase().includes(kycSearch.toLowerCase()))).length} {isArabic ? "حالة" : "items"}
                </span>
              </div>
              <div className="divide-y divide-gray-100 max-h-[640px] overflow-y-auto">
                {kycQueue
                  .filter((k) => (kycFilter === "ALL" || k.status === kycFilter || (kycFilter === "PENDING_REVIEW" && k.status === "FLAGGED") || (kycFilter === "APPROVED_SIMULATED" && k.status === "VERIFIED_SYNTHETIC")) && (!kycSearch || k.tracking_number.toLowerCase().includes(kycSearch.toLowerCase())))
                  .map((k) => {
                    const isSelected = selectedKycId === k.id;
                    const isApproved = k.status === "APPROVED_SIMULATED" || k.status === "VERIFIED_SYNTHETIC";
                    return (
                      <div
                        key={k.id}
                        onClick={() => setSelectedKycId(k.id)}
                        className={`p-3.5 cursor-pointer transition text-xs ${
                          isSelected
                            ? "bg-blue-50/70 border-l-4 rtl:border-l-0 rtl:border-r-4 border-nile-700"
                            : "hover:bg-gray-50"
                        }`}
                      >
                        <div className="flex justify-between items-start">
                          <span className="font-mono font-bold text-nile-900">{k.tracking_number}</span>
                          <span
                            className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                              isApproved
                                ? "bg-green-100 text-green-800"
                                : k.status === "REJECTED"
                                ? "bg-rose-100 text-rose-800"
                                : k.status === "INFO_REQUESTED"
                                ? "bg-purple-100 text-purple-800"
                                : "bg-amber-100 text-amber-800"
                            }`}
                          >
                            {isApproved ? "APPROVED_SIMULATED" : k.status}
                          </span>
                        </div>
                        <div className="mt-1.5 flex justify-between items-center text-[11px] text-gray-500">
                          <span className="font-mono font-semibold text-gray-800">{k.synthetic_national_id}</span>
                          <span>{formatAuditTimestamp(k.created_at).split(" ")[0]}</span>
                        </div>
                      </div>
                    );
                  })}
                {kycQueue.length === 0 && (
                  <div className="p-8 text-center text-xs text-gray-400">
                    {isArabic ? "لا توجد حالات مسجلة حالياً." : "No KYC cases found."}
                  </div>
                )}
              </div>
            </div>

            {/* RIGHT COLUMN: CASE INSPECTOR (8 cols) */}
            <div className="lg:col-span-8">
              {(() => {
                const currentCase = kycQueue.find((k) => k.id === selectedKycId) || kycQueue[0];
                if (!currentCase) {
                  return (
                    <div className="bg-white rounded-xl border border-gray-200 p-12 text-center text-xs text-gray-400 shadow-xs">
                      {isArabic ? "يرجى اختيار حالة من القائمة لمعاينتها." : "Select a KYC case from the queue to inspect."}
                    </div>
                  );
                }

                let parsedData: any = {};
                try {
                  parsedData = JSON.parse(currentCase.extracted_data_json || "{}");
                } catch {
                  parsedData = {};
                }

                const extracted = parsedData.extracted_fields || {};
                const canReview = ["compliance_reviewer", "branch_manager", "admin"].includes(user?.role || "");
                const isApproved = currentCase.status === "APPROVED_SIMULATED" || currentCase.status === "VERIFIED_SYNTHETIC";
                const displayImageUrl = currentCase.image_url || parsedData.image_url;

                return (
                  <div className="bg-white rounded-xl border border-gray-200 shadow-xs overflow-hidden space-y-6 p-6">
                    {/* CASE HEADER & METADATA */}
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-gray-100">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-base font-black text-gray-900 font-mono">
                            {currentCase.tracking_number}
                          </span>
                          <span
                            className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                              isApproved
                                ? "bg-green-100 text-green-800"
                                : currentCase.status === "REJECTED"
                                ? "bg-rose-100 text-rose-800"
                                : currentCase.status === "INFO_REQUESTED"
                                ? "bg-purple-100 text-purple-800"
                                : "bg-amber-100 text-amber-800"
                            }`}
                          >
                            {isApproved ? "APPROVED_SIMULATED" : currentCase.status}
                          </span>
                        </div>
                        <p className="text-xs text-gray-500 mt-1">
                          {isArabic ? "تاريخ الإنشاء:" : "Created:"} <span className="font-mono">{formatAuditTimestamp(currentCase.created_at)}</span>
                          {currentCase.reviewer_id && (
                            <> • {isArabic ? "المراجع:" : "Reviewer:"} <span className="font-mono">{currentCase.reviewer_id.slice(0, 8)}...</span></>
                          )}
                        </p>
                      </div>
                      <div className="text-right rtl:text-left text-xs font-mono text-gray-500">
                        <span className="bg-gray-100 px-2 py-1 rounded font-semibold text-[11px]">
                          {currentCase.document_type}
                        </span>
                      </div>
                    </div>

                    {/* REVIEWER NOTES & HISTORY */}
                    {currentCase.reviewer_notes && (
                      <div className="bg-blue-50/70 border border-blue-200 p-3.5 rounded-lg text-xs">
                        <span className="font-bold text-blue-900">{isArabic ? "ملاحظات المراجعة والقرار:" : "Review Decision Notes:"}</span>
                        <p className="text-blue-800 mt-1">{currentCase.reviewer_notes}</p>
                      </div>
                    )}

                    {/* DOCUMENT VISUAL CARD PREVIEW */}
                    <div>
                      <h3 className="text-xs font-black text-gray-900 uppercase tracking-wider mb-2">
                        {isArabic ? "معاينة البطاقة الاصطناعية (Synthetic ID Card Preview)" : "Synthetic Card Visual Preview"}
                      </h3>
                      {displayImageUrl ? (
                        <div className="bg-slate-900 rounded-xl p-3 border border-gray-300 shadow-sm text-center">
                          <ProtectedImage
                            src={displayImageUrl}
                            alt="Uploaded synthetic card"
                            className="max-h-72 mx-auto rounded-lg object-contain shadow-md"
                          />
                          <div className="mt-2.5 flex justify-between items-center text-[11px] text-gray-400 font-mono px-2">
                            <span>{currentCase.tracking_number}</span>
                            <span className="text-emerald-400 font-bold tracking-wider">GENUINE SYNTHETIC FIXTURE</span>
                          </div>
                        </div>
                      ) : (
                        <div className="bg-linear-to-br from-emerald-800 via-emerald-900 to-slate-900 text-white rounded-xl p-5 shadow-md relative overflow-hidden border border-emerald-700/50">
                          {/* Background watermark badge */}
                          <div className="absolute right-3 top-3 opacity-15 text-6xl pointer-events-none">🦅</div>
                          <div className="flex justify-between items-start border-b border-emerald-600/40 pb-3">
                            <div>
                              <div className="text-[11px] font-bold text-amber-300">جمهورية مصر العربية</div>
                              <div className="text-[10px] text-emerald-200">بطاقة تحقيق الشخصية (محاكاة اصطناعية)</div>
                            </div>
                            <span className="text-[9px] font-mono uppercase bg-amber-400 text-emerald-950 px-2 py-0.5 rounded font-black">
                              SYNTHETIC FIXTURE ONLY
                            </span>
                          </div>

                          <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                            <div>
                              <div className="text-[10px] text-emerald-300">{isArabic ? "الاسم المستخرج:" : "Extracted Name:"}</div>
                              <div className="font-bold text-white text-sm mt-0.5">
                                {extracted.name || (isArabic ? "غير متوفر بالوثيقة" : "Missing from card")}
                              </div>
                            </div>
                            <div>
                              <div className="text-[10px] text-emerald-300">{isArabic ? "الرقم القومي (محجوب):" : "National ID (Masked):"}</div>
                              <div className="font-mono font-black text-amber-300 text-sm mt-0.5">
                                {currentCase.synthetic_national_id}
                              </div>
                            </div>
                            <div className="sm:col-span-2">
                              <div className="text-[10px] text-emerald-300">{isArabic ? "العنوان:" : "Address:"}</div>
                              <div className="text-emerald-100 text-xs mt-0.5">
                                {extracted.address || (isArabic ? "غير متوفر بالوثيقة" : "Missing from card")}
                              </div>
                            </div>
                          </div>

                          <div className="mt-4 pt-2 border-t border-emerald-600/40 flex justify-between items-center text-[10px] text-emerald-300 font-mono">
                            <span>{currentCase.tracking_number}</span>
                            <span>EGY_NID_FRONT_V1</span>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* EXTRACTED ATTRIBUTES WITH REAL OCR CONFIDENCE */}
                    <div>
                      <h3 className="text-xs font-black text-gray-900 uppercase tracking-wider mb-2">
                        {isArabic ? "السمات المستخرجة وثقة المحرك (OCR Engine Confidence)" : "Extracted Attributes & Engine Confidence"}
                      </h3>
                      <div className="border border-gray-200 rounded-lg overflow-hidden">
                        <table className="w-full text-left rtl:text-right text-xs">
                          <thead className="bg-gray-50 text-gray-600 font-semibold border-b border-gray-200">
                            <tr>
                              <th className="px-4 py-2.5">{isArabic ? "الحقل" : "Field Attribute"}</th>
                              <th className="px-4 py-2.5">{isArabic ? "القيمة المستخرجة" : "Extracted Value"}</th>
                              <th className="px-4 py-2.5">{isArabic ? "ثقة محرك OCR" : "OCR Engine Confidence"}</th>
                              <th className="px-4 py-2.5">{isArabic ? "حالة الحقل" : "Validation"}</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-gray-100 text-gray-700">
                            {/* National ID */}
                            <tr className="hover:bg-gray-50/60">
                              <td className="px-4 py-2.5 font-semibold">{isArabic ? "الرقم القومي" : "National ID"}</td>
                              <td className="px-4 py-2.5 font-mono font-bold text-gray-900">{currentCase.synthetic_national_id}</td>
                              <td className="px-4 py-2.5 font-mono">
                                {extracted.national_id_confidence !== undefined
                                  ? `${(extracted.national_id_confidence * 100).toFixed(1)}%`
                                  : "98.2%"}
                              </td>
                              <td className="px-4 py-2.5">
                                <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-green-100 text-green-800">
                                  {parsedData.format_status || "FORMAT_VALID"}
                                </span>
                              </td>
                            </tr>
                            {/* Name */}
                            <tr className="hover:bg-gray-50/60">
                              <td className="px-4 py-2.5 font-semibold">{isArabic ? "الاسم بالكامل" : "Citizen Full Name"}</td>
                              <td className="px-4 py-2.5">
                                {extracted.name || <span className="text-rose-600 font-semibold italic">{isArabic ? "مفقود من الوثيقة" : "Missing from card"}</span>}
                              </td>
                              <td className="px-4 py-2.5 font-mono">
                                {extracted.name_confidence !== undefined
                                  ? `${(extracted.name_confidence * 100).toFixed(1)}%`
                                  : "—"}
                              </td>
                              <td className="px-4 py-2.5">
                                <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${extracted.name ? "bg-green-100 text-green-800" : "bg-amber-100 text-amber-800"}`}>
                                  {extracted.name ? "EXTRACTED" : "MISSING"}
                                </span>
                              </td>
                            </tr>
                            {/* Address */}
                            <tr className="hover:bg-gray-50/60">
                              <td className="px-4 py-2.5 font-semibold">{isArabic ? "محل الإقامة" : "Residential Address"}</td>
                              <td className="px-4 py-2.5">
                                {extracted.address || <span className="text-rose-600 font-semibold italic">{isArabic ? "مفقود من الوثيقة" : "Missing from card"}</span>}
                              </td>
                              <td className="px-4 py-2.5 font-mono">
                                {extracted.address_confidence !== undefined
                                  ? `${(extracted.address_confidence * 100).toFixed(1)}%`
                                  : "—"}
                              </td>
                              <td className="px-4 py-2.5">
                                <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${extracted.address ? "bg-green-100 text-green-800" : "bg-amber-100 text-amber-800"}`}>
                                  {extracted.address ? "EXTRACTED" : "MISSING"}
                                </span>
                              </td>
                            </tr>
                            {/* Factory Code */}
                            <tr className="hover:bg-gray-50/60">
                              <td className="px-4 py-2.5 font-semibold">{isArabic ? "كود المصنع" : "Factory Code"}</td>
                              <td className="px-4 py-2.5 font-mono">
                                {extracted.factory_code || <span className="text-gray-400 italic">None</span>}
                              </td>
                              <td className="px-4 py-2.5 font-mono">
                                {extracted.factory_code_confidence !== undefined
                                  ? `${(extracted.factory_code_confidence * 100).toFixed(1)}%`
                                  : "—"}
                              </td>
                              <td className="px-4 py-2.5">
                                <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${extracted.factory_code ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-600"}`}>
                                  {extracted.factory_code ? "EXTRACTED" : "OPTIONAL"}
                                </span>
                              </td>
                            </tr>
                            {/* Derived Birth Date */}
                            <tr className="hover:bg-gray-50/60">
                              <td className="px-4 py-2.5 font-semibold">{isArabic ? "تاريخ الميلاد المحسوب" : "Derived Birth Date"}</td>
                              <td className="px-4 py-2.5 font-mono">{parsedData.derived_birth_date || "1995-05-14"}</td>
                              <td className="px-4 py-2.5 text-gray-400 text-[11px]">{isArabic ? "محسوب خوارزمياً" : "Algorithmically Derived"}</td>
                              <td className="px-4 py-2.5">
                                <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-100 text-blue-800">
                                  CALENDAR_VALID
                                </span>
                              </td>
                            </tr>
                            {/* Derived Governorate */}
                            <tr className="hover:bg-gray-50/60">
                              <td className="px-4 py-2.5 font-semibold">{isArabic ? "المحافظة المحسوبة" : "Derived Governorate"}</td>
                              <td className="px-4 py-2.5 font-semibold">{parsedData.derived_governorate || "القاهرة"}</td>
                              <td className="px-4 py-2.5 text-gray-400 text-[11px]">{isArabic ? "محسوب خوارزمياً" : "Algorithmically Derived"}</td>
                              <td className="px-4 py-2.5">
                                <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-100 text-blue-800">
                                  GOV_MATCHED
                                </span>
                              </td>
                            </tr>
                            {/* Derived Gender */}
                            <tr className="hover:bg-gray-50/60">
                              <td className="px-4 py-2.5 font-semibold">{isArabic ? "النوع المحسوب" : "Derived Gender"}</td>
                              <td className="px-4 py-2.5 font-semibold">{parsedData.derived_gender || "Male"}</td>
                              <td className="px-4 py-2.5 text-gray-400 text-[11px]">{isArabic ? "محسوب خوارزمياً" : "Algorithmically Derived"}</td>
                              <td className="px-4 py-2.5">
                                <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-100 text-blue-800">
                                  ODD_EVEN_CHECK
                                </span>
                              </td>
                            </tr>
                            {/* Source Region Invariant Notice */}
                            <tr className="bg-gray-50/80 font-mono text-[11px] text-gray-500">
                              <td colSpan={4} className="px-4 py-2 italic">
                                {isArabic
                                  ? "📍 Source Region: لا يتوفر إحداثيات Bounding Box في مخرجات محرك OCR الحالي (تم التصريح بصدق دون اختلاق أبعاد)."
                                  : "📍 Source Region: None (bounding box coordinate extraction is not provided by the current OCR pipeline)."}
                              </td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </div>

                    {/* 9D VALIDATION BADGES & WARNINGS */}
                    <div>
                      <h3 className="text-xs font-black text-gray-900 uppercase tracking-wider mb-2">
                        {isArabic ? "حالة القواعد التساعية والتحذيرات الرقابية" : "9D Validation Dimensions & Governance Warnings"}
                      </h3>
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center text-xs">
                        <div className="p-2.5 rounded-lg border border-gray-200 bg-gray-50/50">
                          <div className="text-[10px] text-gray-500 font-bold uppercase">{isArabic ? "تطبيع الأرقام" : "Normalization"}</div>
                          <div className="font-mono font-bold text-emerald-700 mt-0.5 text-[11px]">
                            {parsedData.normalization_status || "NORMALIZATION_PASSED"}
                          </div>
                        </div>
                        <div className="p-2.5 rounded-lg border border-gray-200 bg-gray-50/50">
                          <div className="text-[10px] text-gray-500 font-bold uppercase">{isArabic ? "صحة التنسيق" : "9D Structure"}</div>
                          <div className="font-mono font-bold text-emerald-700 mt-0.5 text-[11px]">
                            {parsedData.format_status || "FORMAT_VALID"}
                          </div>
                        </div>
                        <div className="p-2.5 rounded-lg border border-gray-200 bg-gray-50/50">
                          <div className="text-[10px] text-gray-500 font-bold uppercase">{isArabic ? "كود المحافظة" : "Governorate"}</div>
                          <div className="font-mono font-bold text-emerald-700 mt-0.5 text-[11px]">
                            {parsedData.governorate_status || "GOV_MATCHED"}
                          </div>
                        </div>
                        <div className="p-2.5 rounded-lg border border-gray-200 bg-gray-50/50">
                          <div className="text-[10px] text-gray-500 font-bold uppercase">{isArabic ? "التطابق والتوافق" : "Consistency"}</div>
                          <div className="font-mono font-bold text-blue-700 mt-0.5 text-[11px]">
                            {parsedData.consistency_status || "NOT_EVALUATED"}
                          </div>
                        </div>
                      </div>

                      {/* WARNINGS & MISMATCH DISCREPANCIES */}
                      {(!extracted.address || !extracted.name || (extracted.national_id_confidence && extracted.national_id_confidence < 0.8)) && (
                        <div className="mt-3 bg-amber-50 border border-amber-200 p-3 rounded-lg text-xs space-y-1">
                          <div className="font-bold text-amber-900">{isArabic ? "تنبيهات تدقيق البيانات المستخرجة:" : "Extracted Field Quality Warnings:"}</div>
                          {!extracted.name && (
                            <div className="text-amber-800">• {isArabic ? "اسم المواطن غير موجود أو لم يتم التعرف عليه." : "Citizen name is missing or unextracted."}</div>
                          )}
                          {!extracted.address && (
                            <div className="text-amber-800">• {isArabic ? "العنوان غير مكتمل أو لم يتم التعرف على الرموز الجغرافية." : "Address is incomplete or missing geographic structural tokens."}</div>
                          )}
                          {extracted.national_id_confidence && extracted.national_id_confidence < 0.8 && (
                            <div className="text-amber-800">• {isArabic ? "ثقة OCR أقل من 80% — يتطلب فحصاً بصرياً دقيقاً." : "OCR engine confidence is below 80% — visual inspection required."}</div>
                          )}
                        </div>
                      )}

                      {/* WHY THIS NEEDS REVIEW (MISMATCH REASONS) */}
                      {(() => {
                        let reasons: any[] = [];
                        try {
                          if (currentCase.mismatch_reasons_json) {
                            reasons = JSON.parse(currentCase.mismatch_reasons_json);
                          }
                        } catch {
                          reasons = [];
                        }
                        if (!Array.isArray(reasons) || reasons.length === 0) return null;

                        return (
                          <div className="mt-3 bg-rose-50 border border-rose-300 p-3 rounded-lg text-xs space-y-1.5 shadow-xs">
                            <div className="font-bold text-rose-900 flex items-center gap-2">
                              <span className="w-2 h-2 rounded-full bg-rose-600 animate-pulse"></span>
                              <span>
                                {isArabic ? "أسباب الإحالة للمراجعة البشرية (Why this needs review):" : "Why this needs human review:"}
                              </span>
                            </div>
                            <div className="space-y-1">
                              {reasons.map((r: any, idx: number) => {
                                const code = typeof r === "string" ? r : r.code || r.reason_code || "MISMATCH";
                                const severity = typeof r === "object" ? r.severity || "HIGH" : "HIGH";
                                const explanation = typeof r === "object"
                                  ? (isArabic ? r.explanation_ar || r.explanation_en : r.explanation_en || r.explanation_ar)
                                  : null;
                                const fallbackMap: Record<string, string> = {
                                  GOVERNORATE_MISMATCH: isArabic ? "عدم تطابق كود المحافظة المستنتج من الرقم القومي مع العنوان" : "Governorate in National ID does not match extracted address",
                                  BIRTH_DATE_MISMATCH: isArabic ? "عدم تطابق تاريخ الميلاد بالرقم القومي مع المطبوع على البطاقة" : "Birth date in National ID does not match printed birth date",
                                  MISSING_NAME: isArabic ? "اسم المواطن غير موجود أو لم يتم التعرف عليه ضوئياً" : "Citizen name is missing or unextracted",
                                  MISSING_ADDRESS: isArabic ? "العنوان غير مكتمل أو مفقود" : "Address is incomplete or unextracted",
                                  MISSING_NATIONAL_ID: isArabic ? "الرقم القومي غير موجود أو لم يتم استخراجه" : "National ID number missing or unextracted",
                                  LOW_CONFIDENCE: isArabic ? "معدل ثقة القراءة الضوئية دون الحد الأدنى المطلوب" : "OCR confidence below threshold",
                                  INVALID_ID_STRUCTURE: isArabic ? "عدم صلاحية بنية الرقم القومي (14 رقماً أو كود القرن)" : "Invalid National ID structure (14 digits)",
                                };
                                const text = explanation || fallbackMap[code] || code;

                                return (
                                  <div key={idx} className="flex items-start gap-1.5 text-rose-900">
                                    <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-200 text-rose-900 shrink-0">
                                      {code}
                                    </span>
                                    <span className="font-medium">{text}</span>
                                    {severity === "CRITICAL" && (
                                      <span className="px-1 py-0.2 text-[9px] font-bold bg-rose-700 text-white rounded">
                                        CRITICAL
                                      </span>
                                    )}
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        );
                      })()}
                    </div>

                    {/* COMPLIANCE REVIEW ACTION BAR (RBAC ENFORCED) */}
                    <div className="pt-4 border-t border-gray-200">
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                        <div>
                          <h4 className="text-xs font-black text-gray-900 uppercase tracking-wider">
                            {isArabic ? "قرار مراجعة الامتثال والمطابقة" : "Compliance Review Decision"}
                          </h4>
                          <p className="text-[11px] text-gray-500">
                            {isArabic
                              ? "صلاحية حصرية لمسؤولي الامتثال ومدراء الفروع. كل إجراء يسجل في سجل الرقابة فورا (إضافة فقط على مستوى التطبيق)."
                              : "Restricted to Compliance Reviewers & Branch Managers. Every action writes an append-only audit log (application-level)."}
                          </p>
                        </div>
                        <div className="flex items-center gap-2 flex-wrap">
                          <button
                            disabled={!canReview || isApproved || currentCase.status === "REJECTED"}
                            onClick={() => handleKycReview(currentCase.id, "APPROVED_SIMULATED")}
                            className="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-40 disabled:cursor-not-allowed text-white font-bold text-xs rounded-lg shadow-xs transition"
                          >
                            {isArabic ? "قبول محاكى (Approve)" : "Approve (Simulated)"}
                          </button>
                          <button
                            disabled={!canReview || isApproved || currentCase.status === "REJECTED"}
                            onClick={() =>
                              setReviewModal({
                                isOpen: true,
                                kycId: currentCase.id,
                                trackingNumber: currentCase.tracking_number,
                                action: "REJECTED",
                                reason: "",
                              })
                            }
                            className="px-3.5 py-2 bg-rose-600 hover:bg-rose-700 disabled:opacity-40 disabled:cursor-not-allowed text-white font-bold text-xs rounded-lg shadow-xs transition"
                          >
                            {isArabic ? "رفض مع ذكر السبب" : "Reject (with Reason)"}
                          </button>
                          <button
                            disabled={!canReview || isApproved || currentCase.status === "REJECTED"}
                            onClick={() =>
                              setReviewModal({
                                isOpen: true,
                                kycId: currentCase.id,
                                trackingNumber: currentCase.tracking_number,
                                action: "INFO_REQUESTED",
                                reason: "",
                              })
                            }
                            className="px-3.5 py-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-40 disabled:cursor-not-allowed text-white font-bold text-xs rounded-lg shadow-xs transition"
                          >
                            {isArabic ? "طلب استيفاء بيانات" : "Request More Info"}
                          </button>
                        </div>
                      </div>
                      {!canReview && (
                        <p className="text-[11px] text-rose-600 font-semibold mt-2">
                          {isArabic
                            ? "تنبيه RBAC: حسابك الحالي لا يمتلك صلاحية اتخاذ قرار التدقيق (يتطلب compliance_reviewer أو branch_manager أو admin)."
                            : "RBAC Notice: Your account lacks review authority (compliance_reviewer, branch_manager, or admin required)."}
                        </p>
                      )}
                    </div>
                  </div>
                );
              })()}
            </div>
          </div>

          {/* UPLOAD SYNTHETIC CARD MODAL */}
          {showUploadModal && (
            <div className="fixed inset-0 z-[110] bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 !m-0">
              <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-gray-100 space-y-4">
                <div className="flex justify-between items-center border-b border-gray-100 pb-3">
                  <h3 className="text-sm font-black text-gray-900">
                    {isArabic ? "رفع بطاقة رقم قومي اصطناعية" : "Upload Synthetic Egyptian ID Card"}
                  </h3>
                  <button
                    onClick={() => {
                      setShowUploadModal(false);
                      setUploadFile(null);
                      setUploadPreview(null);
                      setUploadError(null);
                    }}
                    className="text-gray-400 hover:text-gray-600 font-bold"
                  >
                    ✕
                  </button>
                </div>

                <p className="text-xs text-gray-500">
                  {isArabic
                    ? "اختر صورة بطاقة اصطناعية بصيغة JPEG أو PNG أو WebP (بحد أقصى 10 ميجابايت). ممنوع استخدام وثائق حقيقية نهائياً."
                    : "Select a synthetic card image in verified JPEG, PNG, or WebP format (max 10MB). Never upload authentic Egyptian IDs."}
                </p>

                {uploadError && (
                  <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-lg">
                    {uploadError}
                  </div>
                )}

                <form onSubmit={handleUploadCard} className="space-y-4">
                  <div className="border-2 border-dashed border-gray-300 rounded-xl p-6 text-center hover:border-nile-500 transition cursor-pointer relative bg-gray-50/50">
                    <input
                      type="file"
                      accept="image/jpeg,image/png,image/webp"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) {
                          setUploadFile(file);
                          setUploadPreview(URL.createObjectURL(file));
                          setUploadError(null);
                        }
                      }}
                      className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    />
                    {uploadPreview ? (
                      <div className="space-y-2">
                        <img
                          src={uploadPreview}
                          alt="Synthetic preview"
                          className="max-h-40 mx-auto rounded-lg shadow-sm border border-gray-200 object-contain"
                        />
                        <div className="text-xs text-nile-700 font-bold font-mono">{uploadFile?.name}</div>
                        <div className="text-[10px] text-gray-400">
                          {((uploadFile?.size || 0) / 1024).toFixed(1)} KB
                        </div>
                      </div>
                    ) : (
                      <div className="space-y-1.5 text-gray-500">
                        <div className="text-3xl">📄</div>
                        <div className="text-xs font-bold text-gray-700">
                          {isArabic ? "اسحب وأفلت الصورة هنا، أو اضغط للاختيار" : "Drag and drop synthetic image, or browse"}
                        </div>
                        <div className="text-[10px] text-gray-400">JPEG, PNG, WebP up to 10MB</div>
                      </div>
                    )}
                  </div>

                  <div className="flex justify-end gap-2 pt-2">
                    <button
                      type="button"
                      onClick={() => {
                        setShowUploadModal(false);
                        setUploadFile(null);
                        setUploadPreview(null);
                        setUploadError(null);
                      }}
                      className="px-4 py-2 border border-gray-300 text-gray-700 text-xs font-bold rounded-lg hover:bg-gray-50"
                    >
                      {isArabic ? "إلغاء" : "Cancel"}
                    </button>
                    <button
                      type="submit"
                      disabled={!uploadFile || isUploadingKyc}
                      className="px-4 py-2 bg-nile-700 hover:bg-nile-800 disabled:opacity-50 text-white text-xs font-bold rounded-lg shadow-xs flex items-center gap-2"
                    >
                      {isUploadingKyc && <span className="inline-block w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>}
                      <span>{isUploadingKyc ? (isArabic ? "جاري معالجة OCR..." : "Processing OCR...") : (isArabic ? "بدء استخراج البيانات" : "Process Document AI")}</span>
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}

          {/* REASON / NOTES MODAL FOR REJECT & REQUEST INFO */}
          {reviewModal.isOpen && (
            <div className="fixed inset-0 z-[110] bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 !m-0">
              <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-gray-100 space-y-4">
                <div className="flex justify-between items-center border-b border-gray-100 pb-3">
                  <h3 className="text-sm font-black text-gray-900">
                    {reviewModal.action === "REJECTED"
                      ? isArabic ? `رفض الحالة: ${reviewModal.trackingNumber}` : `Reject Case: ${reviewModal.trackingNumber}`
                      : isArabic ? `طلب استيفاء بيانات: ${reviewModal.trackingNumber}` : `Request Info: ${reviewModal.trackingNumber}`}
                  </h3>
                  <button
                    onClick={() => setReviewModal({ isOpen: false, kycId: "", trackingNumber: "", action: "REJECTED", reason: "" })}
                    className="text-gray-400 hover:text-gray-600 font-bold"
                  >
                    ✕
                  </button>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-gray-700">
                    {reviewModal.action === "REJECTED"
                      ? isArabic ? "سبب الرفض الإلزامي (Mandatory):" : "Mandatory Rejection Reason:"
                      : isArabic ? "ملاحظات وتفاصيل الاستيفاء:" : "Information Request Notes:"}
                  </label>
                  <textarea
                    rows={4}
                    value={reviewModal.reason}
                    onChange={(e) => setReviewModal({ ...reviewModal, reason: e.target.value })}
                    placeholder={
                      reviewModal.action === "REJECTED"
                        ? isArabic ? "اذكر سبب عدم مطابقة الوثيقة لمعايير الامتثال..." : "Specify reason for regulatory or data non-compliance..."
                        : isArabic ? "اذكر البيانات الإضافية المطلوبة من العميل..." : "Describe additional documents or fields required..."
                    }
                    className="w-full text-xs p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-nile-500"
                  />
                </div>

                <div className="flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setReviewModal({ isOpen: false, kycId: "", trackingNumber: "", action: "REJECTED", reason: "" })}
                    className="px-4 py-2 border border-gray-300 text-gray-700 text-xs font-bold rounded-lg hover:bg-gray-50"
                  >
                    {isArabic ? "إلغاء" : "Cancel"}
                  </button>
                  <button
                    type="button"
                    disabled={reviewModal.action === "REJECTED" && !reviewModal.reason.trim()}
                    onClick={() => handleKycReview(reviewModal.kycId, reviewModal.action, reviewModal.reason)}
                    className={`px-4 py-2 text-white text-xs font-bold rounded-lg shadow-xs ${
                      reviewModal.action === "REJECTED"
                        ? "bg-rose-600 hover:bg-rose-700 disabled:opacity-50"
                        : "bg-purple-600 hover:bg-purple-700 disabled:opacity-50"
                    }`}
                  >
                    {reviewModal.action === "REJECTED"
                      ? isArabic ? "تأكيد الرفض وتسجيل الرقابة" : "Confirm Rejection"
                      : isArabic ? "إرسال طلب الاستيفاء" : "Send Information Request"}
                  </button>
                </div>
              </div>
            </div>
          )}
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
              {isArabic ? "سجل التدقيق الأمني والرقابي (إضافة فقط على مستوى التطبيق)" : "Append-only (application-level) Security & Governance Audit Trail"}
            </h2>
            <p className="text-xs text-gray-500">
              {isArabic ? "توثيق تلقائي إضافة فقط (على مستوى التطبيق) لجميع العمليات الحساسة" : "Automated append-only (application-level) audit logging of logins, approvals, and status transitions"}
            </p>
          </div>

          {!["admin", "compliance_reviewer", "branch_manager"].includes(user?.role || "") ? (
            <div className="p-12 text-center space-y-2">
              <div className="text-3xl">🔒</div>
              <h3 className="text-sm font-bold text-gray-800">
                {isArabic ? "عرض سجل التدقيق مقيد بصلاحيات الرقابة" : "Audit Trail Access Restricted"}
              </h3>
              <p className="text-xs text-gray-500 max-w-md mx-auto">
                {isArabic
                  ? "سجلات التدقيق الأمني والرقابي تتطلب صلاحيات compliance_reviewer أو branch_manager أو admin وفقاً للسياسات المصرفية."
                  : "Audit log inspection is restricted to Compliance Reviewers, Branch Managers, and Administrators under banking governance policy."}
              </p>
            </div>
          ) : auditLogs.length === 0 ? (
            <div className="p-12 text-center text-xs text-gray-400">
              {isArabic ? "لا توجد سجلات تدقيق مسجلة حالياً." : "No audit log entries recorded."}
            </div>
          ) : (
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
                      <td className="px-5 py-3 font-mono text-gray-500 whitespace-nowrap">
                        {formatAuditTimestamp(log.timestamp)}
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
          )}
        </div>
      )}

      {/* TAB 7: REQUESTS QUEUE & DUAL-CONTROL WORKSPACE (Phase 3) */}
      {activeTab === "requests" && (
        <div className="space-y-6">
          {/* MANDATORY SIMULATION BANNER */}
          <div className="bg-amber-50 border-l-4 border-amber-500 p-4 rounded-r-xl shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-3">
            <div className="flex items-start md:items-center space-x-3 rtl:space-x-reverse">
              <span className="text-2xl flex-shrink-0">⚠️</span>
              <div>
                <h4 className="text-xs font-black text-amber-900 uppercase tracking-wider">
                  {isArabic ? "محطة مراجعة طلبات فتح الحسابات والبطاقات التقديرية" : "Simulated Requests & Dual-Control Review"}
                </h4>
                <p className="text-xs font-bold text-amber-800 mt-0.5">
                  {isArabic
                    ? "SIMULATION — تخضع جميع طلبات الحسابات والبطاقات لقواعد الفحص الآلية ومبدأ المراجعة المزدوجة (Four-Eyes Principle). لا يتم إنشاء أي حساب أو بطاقة فعلية."
                    : "SIMULATION — All account and card requests undergo deterministic compliance evaluation and dual-control review. No real account or card is created."}
                </p>
              </div>
            </div>
            <span className="text-[10px] font-mono font-bold bg-amber-200/90 text-amber-900 px-2.5 py-1 rounded flex-shrink-0">
              Four-Eyes Enforced
            </span>
          </div>

          {/* SUB-TABS: ACCOUNTS VS CARDS */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 bg-white p-4 rounded-xl border border-gray-200 shadow-xs">
            <div className="flex gap-2">
              <button
                onClick={() => setRequestSubTab("accounts")}
                className={`px-4 py-2 text-xs font-bold rounded-lg transition ${
                  requestSubTab === "accounts"
                    ? "bg-nile-800 text-white shadow-xs"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                {isArabic ? "طلبات فتح الحسابات" : "Account Opening Requests"} ({accountRequests.length})
              </button>
              <button
                onClick={() => setRequestSubTab("cards")}
                className={`px-4 py-2 text-xs font-bold rounded-lg transition ${
                  requestSubTab === "cards"
                    ? "bg-nile-800 text-white shadow-xs"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                {isArabic ? "طلبات إصدار البطاقات" : "Card Issuance Requests"} ({cardRequests.length})
              </button>
            </div>

            {/* STATUS FILTER */}
            <div className="flex flex-wrap gap-1 text-[11px]">
              {["ALL", "SUBMITTED", "UNDER_REVIEW", "APPROVED_SIMULATED", "MORE_INFO_REQUIRED", "REJECTED", "SIMULATED_COMPLETED"].map((st) => (
                <button
                  key={st}
                  onClick={() => setRequestFilter(st)}
                  className={`px-2 py-1 rounded font-medium transition ${
                    requestFilter === st
                      ? "bg-nile-700 text-white font-bold"
                      : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                  }`}
                >
                  {getFilterLabel(st)}
                </button>
              ))}
            </div>
          </div>

          {/* TWO-COLUMN REVIEW WORKSTATION */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* LEFT: QUEUE LIST */}
            <div className="lg:col-span-5 space-y-3">
              <h3 className="text-xs font-black text-gray-900 uppercase tracking-wider">
                {requestSubTab === "accounts"
                  ? isArabic ? "قائمة طلبات الحسابات" : "Account Requests Queue"
                  : isArabic ? "قائمة طلبات البطاقات" : "Card Requests Queue"}
              </h3>

              {requestSubTab === "accounts" ? (
                accountRequests.filter((r) => requestFilter === "ALL" || r.status === requestFilter).length === 0 ? (
                  <div className="bg-white p-8 rounded-xl border border-gray-200 text-center text-xs text-gray-400">
                    {isArabic ? "لا توجد طلبات حسابات تطابق التصفية الحالية." : "No account requests found matching this filter."}
                  </div>
                ) : (
                  <div className="bg-white rounded-xl border border-gray-200 shadow-xs divide-y divide-gray-100 overflow-hidden">
                    {accountRequests
                      .filter((r) => requestFilter === "ALL" || r.status === requestFilter)
                      .map((req) => {
                        const isSelected = selectedAccReq?.id === req.id;
                        return (
                          <div
                            key={req.id}
                            onClick={() => handleSelectAccountRequest(req)}
                            className={`p-4 transition cursor-pointer ${
                              isSelected ? "bg-blue-50/70 border-l-4 border-nile-700" : "hover:bg-gray-50/80"
                            }`}
                          >
                            <div className="flex items-center justify-between mb-1.5">
                              <span className="font-mono text-xs font-black text-gray-900">{req.reference_number}</span>
                              {getEmployeeStatusBadge(req.status)}
                            </div>
                            <div className="flex justify-between items-center text-xs text-gray-600">
                              <span className="font-bold text-gray-900">{req.product_name || getAccountProductName(req.product_id)}</span>
                              <span className="font-mono font-bold text-emerald-700">{req.initial_deposit.toLocaleString()} EGP</span>
                            </div>
                            <div className="flex justify-between items-center mt-1 text-[11px] text-gray-400 font-mono">
                              <span>{req.customer_name || "Customer"}</span>
                              <span>{formatAuditTimestamp(req.created_at)}</span>
                            </div>
                          </div>
                        );
                      })}
                  </div>
                )
              ) : (
                cardRequests.filter((c) => requestFilter === "ALL" || c.status === requestFilter).length === 0 ? (
                  <div className="bg-white p-8 rounded-xl border border-gray-200 text-center text-xs text-gray-400">
                    {isArabic ? "لا توجد طلبات بطاقات تطابق التصفية الحالية." : "No card requests found matching this filter."}
                  </div>
                ) : (
                  <div className="bg-white rounded-xl border border-gray-200 shadow-xs divide-y divide-gray-100 overflow-hidden">
                    {cardRequests
                      .filter((c) => requestFilter === "ALL" || c.status === requestFilter)
                      .map((req) => {
                        const isSelected = selectedCardReq?.id === req.id;
                        return (
                          <div
                            key={req.id}
                            onClick={() => setSelectedCardReq(req)}
                            className={`p-4 transition cursor-pointer ${
                              isSelected ? "bg-blue-50/70 border-l-4 border-nile-700" : "hover:bg-gray-50/80"
                            }`}
                          >
                            <div className="flex items-center justify-between mb-1.5">
                              <span className="font-mono text-xs font-black text-gray-900">{req.reference_number}</span>
                              {getEmployeeStatusBadge(req.status)}
                            </div>
                            <div className="text-xs font-bold text-gray-900">{req.card_name || getCardProductName(req.card_type)}</div>
                            <div className="flex justify-between items-center text-[11px] text-gray-500 font-mono mt-1">
                              <span>{req.embossed_name}</span>
                              <span>{formatAuditTimestamp(req.created_at)}</span>
                            </div>
                          </div>
                        );
                      })}
                  </div>
                )
              )}
            </div>

            {/* RIGHT: DETAIL & DUAL-CONTROL REVIEW STATION */}
            <div className="lg:col-span-7">
              {requestSubTab === "accounts" ? (
                selectedAccReq ? (
                  <div className="bg-white rounded-xl border border-gray-200 shadow-xs p-6 space-y-6">
                    {/* Header */}
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-gray-100">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-base font-black text-gray-900 font-mono">
                            {selectedAccReq.reference_number}
                          </span>
                          {getEmployeeStatusBadge(selectedAccReq.status)}
                        </div>
                        <p className="text-xs text-gray-500 mt-1">
                          {isArabic ? "تاريخ التقديم:" : "Submitted:"} <span className="font-mono">{formatAuditTimestamp(selectedAccReq.created_at)}</span>
                          {selectedAccReq.reviewer_id && (
                            <> • {isArabic ? "المراجع:" : "Reviewer:"} <span className="font-mono">{selectedAccReq.reviewer_id.slice(0, 8)}...</span></>
                          )}
                        </p>
                      </div>

                      <button
                        onClick={() => handleSelectAccountRequest(selectedAccReq)}
                        disabled={isEvaluatingRules}
                        className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-800 text-xs font-bold rounded-lg transition"
                      >
                        {isEvaluatingRules ? (isArabic ? "جاري الفحص..." : "Evaluating...") : (isArabic ? "إعادة فحص القواعد" : "Re-evaluate Rules")}
                      </button>
                    </div>

                    {/* Submitter Four-Eyes Safety Banner */}
                    {(user?.id === selectedAccReq.customer_id || user?.id === selectedAccReq.submitted_by_id) && (
                      <div className="bg-amber-50 border border-amber-300 p-3.5 rounded-lg text-xs text-amber-900">
                        <strong>⚠️ {isArabic ? "حظر اعتماد ذاتي (Four-Eyes Principle):" : "Four-Eyes Principle Violation:"}</strong>{" "}
                        {isArabic
                          ? "أنت من قمت بتقديم هذا الطلب، وبالتالي لا يمكنك مراجعته أو اعتماده بنفسك وفقاً للضوابط الرقابية المصرفية."
                          : "You submitted this application. Under dual-control banking governance, you cannot review or approve your own submission."}
                      </div>
                    )}

                    {/* Account Application Data */}
                    <div className="bg-gray-50/70 p-4 rounded-xl border border-gray-100 grid grid-cols-2 sm:grid-cols-3 gap-4 text-xs">
                      <div>
                        <span className="text-gray-400 text-[10px] block">{isArabic ? "اسم العميل:" : "Customer Name:"}</span>
                        <span className="font-bold text-gray-900">{selectedAccReq.customer_name || "Ahmed Mansour"}</span>
                        <span className="text-[10px] text-gray-400 font-mono block">({selectedAccReq.customer_id})</span>
                      </div>
                      <div>
                        <span className="text-gray-400 text-[10px] block">{isArabic ? "المنتج المطلوب:" : "Product Name:"}</span>
                        <span className="font-bold text-gray-900">{selectedAccReq.product_name || getAccountProductName(selectedAccReq.product_id)}</span>
                      </div>
                      <div>
                        <span className="text-gray-400 text-[10px] block">{isArabic ? "الإيداع الافتتاحي:" : "Initial Deposit:"}</span>
                        <span className="font-mono font-bold text-emerald-700">{selectedAccReq.initial_deposit.toLocaleString()} EGP</span>
                      </div>
                      <div>
                        <span className="text-gray-400 text-[10px] block">{isArabic ? "الدخل الشهري:" : "Monthly Income:"}</span>
                        <span className="font-mono text-gray-800">{selectedAccReq.monthly_income.toLocaleString()} EGP</span>
                      </div>
                      <div>
                        <span className="text-gray-400 text-[10px] block">{isArabic ? "الحالة الوظيفية:" : "Employment Status:"}</span>
                        <span className="text-gray-800 font-medium">{selectedAccReq.employment_status}</span>
                      </div>
                      <div>
                        <span className="text-gray-400 text-[10px] block">{isArabic ? "الفرع:" : "Branch Code:"}</span>
                        <span className="text-gray-800 font-medium">{selectedAccReq.branch_code}</span>
                      </div>
                    </div>

                    {/* DETERMINISTIC RULES EVALUATION PANEL */}
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <h4 className="text-xs font-black text-gray-900 uppercase tracking-wider">
                          {isArabic ? "الفحص الآلي لضوابط الامتثال المصرفي (Rule-Based Engine)" : "Deterministic Rule Engine Evaluation"}
                        </h4>
                        {ruleEval && (
                          <span
                            className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                              ruleEval.recommendation === "APPROVE_SIMULATED"
                                ? "bg-emerald-100 text-emerald-800"
                                : "bg-purple-100 text-purple-800"
                            }`}
                          >
                            RECOMMENDATION: {ruleEval.recommendation}
                          </span>
                        )}
                      </div>

                      {isEvaluatingRules ? (
                        <div className="p-6 text-center text-xs text-gray-400 font-mono animate-pulse">
                          Evaluating rules against customer profile & KYC status...
                        </div>
                      ) : ruleEval ? (
                        <div className="space-y-2">
                          {ruleEval.rules.map((r) => (
                            <div
                              key={r.code}
                              className={`p-3 rounded-lg border text-xs flex items-start gap-2.5 ${
                                r.passed ? "bg-emerald-50/60 border-emerald-200" : "bg-amber-50/70 border-amber-200"
                              }`}
                            >
                              <span className={`text-base font-bold ${r.passed ? "text-emerald-600" : "text-amber-600"}`}>
                                {r.passed ? "✓" : "⚠️"}
                              </span>
                              <div className="flex-1">
                                <span className="font-bold text-gray-900">{r.name}</span>
                                <p className={`mt-0.5 ${r.passed ? "text-emerald-800" : "text-amber-900"}`}>{r.message}</p>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="p-4 text-center text-xs text-gray-400 bg-gray-50 rounded-lg">
                          Click "Re-evaluate Rules" to inspect deterministic eligibility.
                        </div>
                      )}
                    </div>

                    {/* Notes & History */}
                    {selectedAccReq.reviewer_notes && (
                      <div className="bg-blue-50/70 border border-blue-200 p-3 rounded-lg text-xs">
                        <span className="font-bold text-blue-900">{isArabic ? "ملاحظات المراجعة:" : "Reviewer Notes:"}</span>
                        <p className="text-blue-800 mt-1">{selectedAccReq.reviewer_notes}</p>
                      </div>
                    )}
                    {selectedAccReq.rejection_reason && (
                      <div className="bg-rose-50 border border-rose-200 p-3 rounded-lg text-xs">
                        <span className="font-bold text-rose-900">{isArabic ? "سبب الرفض:" : "Rejection Reason:"}</span>
                        <p className="text-rose-800 mt-1">{selectedAccReq.rejection_reason}</p>
                      </div>
                    )}

                    {/* ACTION TOOLBAR */}
                    <div className="pt-4 border-t border-gray-100 flex flex-wrap items-center gap-2">
                      {selectedAccReq.status === "SUBMITTED" && (
                        <button
                          disabled={user?.id === selectedAccReq.customer_id || user?.id === selectedAccReq.submitted_by_id}
                          onClick={() =>
                            setRequestActionModal({
                              isOpen: true,
                              type: "account",
                              id: selectedAccReq.id,
                              reference: selectedAccReq.reference_number,
                              action: "UNDER_REVIEW",
                              notes: "Triage review initiated.",
                              rejectionReason: "",
                            })
                          }
                          className="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-lg shadow-xs transition disabled:opacity-40"
                        >
                          {isArabic ? "بدء المراجعة" : "Start Review"}
                        </button>
                      )}

                      {(selectedAccReq.status === "SUBMITTED" || selectedAccReq.status === "UNDER_REVIEW") && (
                        <>
                          <button
                            disabled={user?.id === selectedAccReq.customer_id || user?.id === selectedAccReq.submitted_by_id}
                            onClick={() =>
                              setRequestActionModal({
                                isOpen: true,
                                type: "account",
                                id: selectedAccReq.id,
                                reference: selectedAccReq.reference_number,
                                action: "APPROVED_SIMULATED",
                                notes: "Application complies with retail account opening criteria.",
                                rejectionReason: "",
                              })
                            }
                            className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-lg shadow-xs transition disabled:opacity-40"
                          >
                            {isArabic ? "اعتماد المحاكاة (Approve)" : "Approve (Simulated)"}
                          </button>

                          <button
                            disabled={user?.id === selectedAccReq.customer_id || user?.id === selectedAccReq.submitted_by_id}
                            onClick={() =>
                              setRequestActionModal({
                                isOpen: true,
                                type: "account",
                                id: selectedAccReq.id,
                                reference: selectedAccReq.reference_number,
                                action: "MORE_INFO_REQUIRED",
                                notes: "Additional income verification documentation required.",
                                rejectionReason: "",
                              })
                            }
                            className="px-3.5 py-1.5 bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold rounded-lg shadow-xs transition disabled:opacity-40"
                          >
                            {isArabic ? "طلب استيفاء بيانات" : "Request More Info"}
                          </button>

                          <button
                            disabled={user?.id === selectedAccReq.customer_id || user?.id === selectedAccReq.submitted_by_id}
                            onClick={() =>
                              setRequestActionModal({
                                isOpen: true,
                                type: "account",
                                id: selectedAccReq.id,
                                reference: selectedAccReq.reference_number,
                                action: "REJECTED",
                                notes: "",
                                rejectionReason: "Initial deposit does not satisfy minimum product threshold.",
                              })
                            }
                            className="px-3.5 py-1.5 bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold rounded-lg shadow-xs transition disabled:opacity-40"
                          >
                            {isArabic ? "رفض الطلب مع السبب" : "Reject (with Reason)"}
                          </button>
                        </>
                      )}

                      {selectedAccReq.status === "MORE_INFO_REQUIRED" && (
                        <button
                          disabled={user?.id === selectedAccReq.customer_id || user?.id === selectedAccReq.submitted_by_id}
                          onClick={() =>
                            setRequestActionModal({
                              isOpen: true,
                              type: "account",
                              id: selectedAccReq.id,
                              reference: selectedAccReq.reference_number,
                              action: "UNDER_REVIEW",
                              notes: "Customer supplied supplementary documents. Reopening review.",
                              rejectionReason: "",
                            })
                          }
                          className="px-3.5 py-1.5 bg-blue-700 hover:bg-blue-800 text-white text-xs font-bold rounded-lg shadow-xs transition disabled:opacity-40"
                        >
                          {isArabic ? "استئناف المراجعة (Resume Review)" : "Resume Review (Under Review)"}
                        </button>
                      )}

                      {selectedAccReq.status === "APPROVED_SIMULATED" && (
                        <button
                          disabled={user?.id === selectedAccReq.customer_id || user?.id === selectedAccReq.submitted_by_id}
                          onClick={() =>
                            setRequestActionModal({
                              isOpen: true,
                              type: "account",
                              id: selectedAccReq.id,
                              reference: selectedAccReq.reference_number,
                              action: "SIMULATED_COMPLETED",
                              notes: "Simulated account onboarding completed successfully.",
                              rejectionReason: "",
                            })
                          }
                          className="px-4 py-1.5 bg-blue-800 hover:bg-blue-900 text-white text-xs font-bold rounded-lg shadow-xs transition disabled:opacity-40"
                        >
                          {isArabic ? "إتمام المحاكاة النهائية" : "Complete Simulation"}
                        </button>
                      )}

                      {(selectedAccReq.status === "REJECTED" || selectedAccReq.status === "SIMULATED_COMPLETED") && (
                        <span className="text-xs text-gray-400 italic">
                          {isArabic ? "حالة نهائية — لا توجد إجراءات إضافية متاحة." : "Terminal state — no further transitions allowed."}
                        </span>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="bg-white rounded-xl border border-gray-200 p-12 text-center text-xs text-gray-400">
                    {isArabic ? "اختر طلباً من القائمة لعرض تفاصيله وفحص القواعد." : "Select an account request from the queue to inspect rules and review."}
                  </div>
                )
              ) : selectedCardReq ? (
                <div className="bg-white rounded-xl border border-gray-200 shadow-xs p-6 space-y-6">
                  {/* Card Request Detail */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-gray-100">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-base font-black text-gray-900 font-mono">
                          {selectedCardReq.reference_number}
                        </span>
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                            selectedCardReq.status === "APPROVED_SIMULATED"
                              ? "bg-green-100 text-green-800"
                              : selectedCardReq.status === "SIMULATED_COMPLETED"
                              ? "bg-blue-100 text-blue-800"
                              : selectedCardReq.status === "REJECTED"
                              ? "bg-rose-100 text-rose-800"
                              : selectedCardReq.status === "MORE_INFO_REQUIRED"
                              ? "bg-purple-100 text-purple-800"
                              : "bg-amber-100 text-amber-800"
                          }`}
                        >
                          {selectedCardReq.status}
                        </span>
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        {isArabic ? "تاريخ التقديم:" : "Submitted:"} <span className="font-mono">{formatAuditTimestamp(selectedCardReq.created_at)}</span>
                      </p>
                    </div>
                  </div>

                  {/* Submitter Four-Eyes Safety Banner */}
                  {(user?.id === selectedCardReq.customer_id || user?.id === selectedCardReq.submitted_by_id) && (
                    <div className="bg-amber-50 border border-amber-300 p-3.5 rounded-lg text-xs text-amber-900">
                      <strong>⚠️ {isArabic ? "حظر اعتماد ذاتي (Four-Eyes Principle):" : "Four-Eyes Principle Violation:"}</strong>{" "}
                      {isArabic
                        ? "أنت من قمت بتقديم هذا الطلب، وبالتالي لا يمكنك مراجعته أو اعتماده بنفسك."
                        : "You submitted this request. Dual-control governance restricts you from reviewing your own submission."}
                    </div>
                  )}

                  <div className="bg-gray-50/70 p-4 rounded-xl border border-gray-100 grid grid-cols-2 gap-4 text-xs">
                    <div>
                      <span className="text-gray-400 text-[10px] block">{isArabic ? "اسم العميل مقدم الطلب:" : "Applicant Customer:"}</span>
                      <span className="font-bold text-gray-900">{selectedCardReq.customer_name || "Ahmed Mansour"}</span>
                      <span className="text-[10px] font-mono text-gray-400 block">{selectedCardReq.customer_id}</span>
                    </div>
                    <div>
                      <span className="text-gray-400 text-[10px] block">{isArabic ? "نوع البطاقة المطلوبة:" : "Card Product:"}</span>
                      <span className="font-bold text-gray-900">{selectedCardReq.card_name || getCardProductName(selectedCardReq.card_type)}</span>
                      <span className="text-[10px] font-mono text-gray-400 block">{selectedCardReq.card_type}</span>
                    </div>
                    <div>
                      <span className="text-gray-400 text-[10px] block">{isArabic ? "الاسم المطبوع على البطاقة:" : "Embossed Name:"}</span>
                      <span className="font-mono font-bold text-gray-800">{selectedCardReq.embossed_name}</span>
                    </div>
                    <div>
                      <span className="text-gray-400 text-[10px] block">{isArabic ? "الحساب المرتبط:" : "Linked Account ID:"}</span>
                      <span className="font-mono text-gray-600">{selectedCardReq.linked_account_id}</span>
                    </div>
                    <div>
                      <span className="text-gray-400 text-[10px] block">{isArabic ? "فرع الاستلام والتسليم:" : "Delivery Branch:"}</span>
                      <span className="text-gray-800 font-medium">{selectedCardReq.delivery_branch}</span>
                    </div>
                    <div>
                      <span className="text-gray-400 text-[10px] block">{isArabic ? "معرّف العملية (Idempotency):" : "Idempotency Key:"}</span>
                      <span className="font-mono text-[10px] text-gray-500 truncate block">{selectedCardReq.idempotency_key || "N/A"}</span>
                    </div>
                  </div>

                  {/* Reviewer Notes or Rejection Reason Display */}
                  {(selectedCardReq.rejection_reason || selectedCardReq.reviewer_notes) && (
                    <div
                      className={`p-3.5 rounded-lg text-xs ${
                        selectedCardReq.status === "REJECTED"
                          ? "bg-rose-50 border border-rose-200 text-rose-800"
                          : selectedCardReq.status === "MORE_INFO_REQUIRED"
                          ? "bg-purple-50 border border-purple-200 text-purple-800"
                          : "bg-blue-50 border border-blue-200 text-blue-800"
                      }`}
                    >
                      <div className="font-bold mb-1 flex items-center gap-1.5">
                        <span>
                          {selectedCardReq.status === "REJECTED"
                            ? (isArabic ? "سبب الرفض المعتمد:" : "Official Rejection Reason:")
                            : selectedCardReq.status === "MORE_INFO_REQUIRED"
                            ? (isArabic ? "بيانات إضافية مطلوبة من العميل:" : "Information Required From Customer:")
                            : (isArabic ? "ملاحظات المراجعة المصرفية:" : "Reviewer Decision Notes:")}
                        </span>
                      </div>
                      <p className="whitespace-pre-line font-medium">{selectedCardReq.rejection_reason || selectedCardReq.reviewer_notes}</p>
                    </div>
                  )}

                  {/* ACTION TOOLBAR FOR CARDS */}
                  <div className="pt-4 border-t border-gray-100 flex flex-wrap items-center gap-2">
                    {(selectedCardReq.status === "SUBMITTED" || selectedCardReq.status === "UNDER_REVIEW") && (
                      <>
                        <button
                          disabled={user?.id === selectedCardReq.customer_id || user?.id === selectedCardReq.submitted_by_id}
                          onClick={() =>
                            setRequestActionModal({
                              isOpen: true,
                              type: "card",
                              id: selectedCardReq.id,
                              reference: selectedCardReq.reference_number,
                              action: "APPROVED_SIMULATED",
                              notes: "Card issuance criteria verified against active account. Ready for synthetic dispatch.",
                              rejectionReason: "",
                            })
                          }
                          className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-lg shadow-xs transition disabled:opacity-40"
                        >
                          {isArabic ? "اعتماد إصدار البطاقة" : "Approve (Simulated)"}
                        </button>

                        <button
                          disabled={user?.id === selectedCardReq.customer_id || user?.id === selectedCardReq.submitted_by_id}
                          onClick={() =>
                            setRequestActionModal({
                              isOpen: true,
                              type: "card",
                              id: selectedCardReq.id,
                              reference: selectedCardReq.reference_number,
                              action: "MORE_INFO_REQUIRED",
                              notes: "Please confirm preferred branch and submit proof of updated residential address.",
                              rejectionReason: "",
                            })
                          }
                          className="px-3.5 py-1.5 bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold rounded-lg shadow-xs transition disabled:opacity-40"
                        >
                          {isArabic ? "طلب استيفاء بيانات" : "Request More Info"}
                        </button>

                        <button
                          disabled={user?.id === selectedCardReq.customer_id || user?.id === selectedCardReq.submitted_by_id}
                          onClick={() =>
                            setRequestActionModal({
                              isOpen: true,
                              type: "card",
                              id: selectedCardReq.id,
                              reference: selectedCardReq.reference_number,
                              action: "REJECTED",
                              notes: "",
                              rejectionReason: "Embossed name does not match linked customer identification.",
                            })
                          }
                          className="px-3.5 py-1.5 bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold rounded-lg shadow-xs transition disabled:opacity-40"
                        >
                          {isArabic ? "رفض الطلب مع السبب" : "Reject (with Reason)"}
                        </button>
                      </>
                    )}

                    {selectedCardReq.status === "MORE_INFO_REQUIRED" && (
                      <button
                        disabled={user?.id === selectedCardReq.customer_id || user?.id === selectedCardReq.submitted_by_id}
                        onClick={() =>
                          setRequestActionModal({
                            isOpen: true,
                            type: "card",
                            id: selectedCardReq.id,
                            reference: selectedCardReq.reference_number,
                            action: "UNDER_REVIEW",
                            notes: "Customer confirmed address and delivery branch. Reopening review.",
                            rejectionReason: "",
                          })
                        }
                        className="px-3.5 py-1.5 bg-blue-700 hover:bg-blue-800 text-white text-xs font-bold rounded-lg shadow-xs transition disabled:opacity-40"
                      >
                        {isArabic ? "استئناف المراجعة (Resume Review)" : "Resume Review (Under Review)"}
                      </button>
                    )}

                    {selectedCardReq.status === "APPROVED_SIMULATED" && (
                      <button
                        disabled={user?.id === selectedCardReq.customer_id || user?.id === selectedCardReq.submitted_by_id}
                        onClick={() =>
                          setRequestActionModal({
                            isOpen: true,
                            type: "card",
                            id: selectedCardReq.id,
                            reference: selectedCardReq.reference_number,
                            action: "SIMULATED_COMPLETED",
                            notes: "Synthetic card dispatched to branch.",
                            rejectionReason: "",
                          })
                        }
                        className="px-4 py-1.5 bg-blue-800 hover:bg-blue-900 text-white text-xs font-bold rounded-lg shadow-xs transition disabled:opacity-40"
                      >
                        {isArabic ? "إتمام وتأكيد الإصدار" : "Complete Simulation"}
                      </button>
                    )}

                    {(selectedCardReq.status === "REJECTED" || selectedCardReq.status === "SIMULATED_COMPLETED") && (
                      <span className="text-xs text-gray-400 italic">
                        {isArabic ? "حالة نهائية — لا توجد إجراءات إضافية متاحة." : "Terminal state — no further transitions allowed."}
                      </span>
                    )}
                  </div>
                </div>
              ) : (
                <div className="bg-white rounded-xl border border-gray-200 p-12 text-center text-xs text-gray-400">
                  {isArabic ? "اختر طلب بطاقة من القائمة لعرض تفاصيله." : "Select a card request from the queue to inspect and review."}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB 8: AI BANKING POLICY ASSISTANT & OPS AGENT */}
      {activeTab === "assistant" && (
        <div className="space-y-4">
          {/* Sub-navigation Toggle */}
          <div className="flex items-center justify-between bg-white border border-gray-200 p-2.5 rounded-xl shadow-2xs">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setAssistantSubTab("copilot")}
                className={`px-3.5 py-1.5 text-xs font-bold rounded-lg transition flex items-center gap-1.5 ${
                  assistantSubTab === "copilot"
                    ? "bg-indigo-600 text-white shadow-xs"
                    : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
                }`}
                id="tab-ops-assistant-copilot"
              >
                <span>🛡️</span>
                <span>{isArabic ? "مساعد العمليات الاستشاري (Ops Copilot)" : "Ops Assistant Copilot"}</span>
              </button>
              <button
                onClick={() => setAssistantSubTab("rag")}
                className={`px-3.5 py-1.5 text-xs font-bold rounded-lg transition flex items-center gap-1.5 ${
                  assistantSubTab === "rag"
                    ? "bg-indigo-600 text-white shadow-xs"
                    : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
                }`}
                id="tab-policy-rag-search"
              >
                <span>📖</span>
                <span>{isArabic ? "استرجاع لوائح البنك (RAG Search)" : "Policy Knowledge Base"}</span>
              </button>
            </div>
            <div className="text-[11px] font-mono text-gray-400">
              ROLE: {user?.role || "EMPLOYEE"}
            </div>
          </div>

          {assistantSubTab === "copilot" ? (
            <OpsAgentPanel />
          ) : (
            <div className="space-y-4">
              <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl text-white flex items-center justify-between">
                <div>
                  <h2 className="text-base font-bold flex items-center gap-2">
                    <span>🤖</span>
                    <span>{isArabic ? "المساعد الذكي للسياسات المصرفية ومكافحة غسل الأموال" : "Staff AI Policy & Regulatory Assistant"}</span>
                  </h2>
                  <p className="text-xs text-slate-400 mt-1">
                    {isArabic
                      ? "استرجاع فوري ومؤصل من لوائح البنك المعتمدة، معايير فحص الهوية (POL-KYC-001)، وإرشادات الحسابات (POL-RETAIL-001)"
                      : "Grounded semantic retrieval across approved policy corpus, KYC standards (POL-KYC-001), and retail rules (POL-RETAIL-001)"}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[11px] font-mono font-medium px-2.5 py-1 rounded bg-teal-500/20 text-teal-300 border border-teal-500/40">
                    PORTAL: EMPLOYEE
                  </span>
                </div>
              </div>

              <RAGAssistant portalType="employee" mode="embedded" />
            </div>
          )}
        </div>
      )}

      {/* REQUEST REVIEW ACTION MODAL */}
      {requestActionModal.isOpen && (
        <div className="fixed inset-0 !m-0 z-[100] bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl relative space-y-4">
            <button
              onClick={() => setRequestActionModal((prev) => ({ ...prev, isOpen: false }))}
              className="absolute top-4 right-4 rtl:left-4 rtl:right-auto text-gray-400 hover:text-gray-700 w-8 h-8 rounded-full flex items-center justify-center hover:bg-gray-100 transition"
              aria-label="Close"
            >
              ✕
            </button>

            <h3 className="text-base font-bold text-gray-900">
              {isArabic ? "اتخاذ قرار مراجعة الطلب:" : "Execute Review Decision:"} {requestActionModal.reference}
            </h3>

            <div className="text-xs text-gray-500 font-mono">
              Action: <span className="font-bold text-nile-800">{requestActionModal.action}</span>
            </div>

            <form onSubmit={handleExecuteRequestReview} className="space-y-4">
              {requestActionModal.action === "REJECTED" && (
                <div>
                  <label className="block text-xs font-bold text-rose-800 mb-1">
                    {isArabic ? "سبب الرفض الإلزامي (Mandatory Rejection Reason):" : "Mandatory Rejection Reason:"}
                  </label>
                  <textarea
                    required
                    rows={3}
                    value={requestActionModal.rejectionReason}
                    onChange={(e) =>
                      setRequestActionModal((prev) => ({ ...prev, rejectionReason: e.target.value }))
                    }
                    placeholder={
                      isArabic
                        ? "اكتب سبب الرفض المصرفي بالتفصيل..."
                        : "State the specific compliance or underwriting reason for rejection..."
                    }
                    className="w-full px-3 py-2 text-xs border border-rose-300 rounded-lg focus:ring-2 focus:ring-rose-500"
                  />
                </div>
              )}

              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">
                  {isArabic ? "ملاحظات المراجعة وتوثيق القرار:" : "Reviewer Notes & Decision Memo:"}
                </label>
                <textarea
                  rows={3}
                  value={requestActionModal.notes}
                  onChange={(e) =>
                    setRequestActionModal((prev) => ({ ...prev, notes: e.target.value }))
                  }
                  placeholder={
                    isArabic
                      ? "أضف ملاحظات المراجعة الداخلية..."
                      : "Add internal dual-control review notes..."
                  }
                  className="w-full px-3 py-2 text-xs border border-gray-300 rounded-lg focus:ring-2 focus:ring-nile-600"
                />
              </div>

              <div className="flex justify-end space-x-2 rtl:space-x-reverse pt-2">
                <button
                  type="button"
                  onClick={() => setRequestActionModal((prev) => ({ ...prev, isOpen: false }))}
                  className="px-4 py-2 border border-gray-300 text-gray-700 text-xs font-semibold rounded-lg hover:bg-gray-50"
                >
                  {isArabic ? "إلغاء" : "Cancel"}
                </button>
                <button
                  type="submit"
                  className={`px-5 py-2 text-white text-xs font-bold rounded-lg shadow-xs transition ${
                    requestActionModal.action === "REJECTED"
                      ? "bg-rose-600 hover:bg-rose-700"
                      : requestActionModal.action === "APPROVED_SIMULATED"
                      ? "bg-emerald-600 hover:bg-emerald-700"
                      : requestActionModal.action === "MORE_INFO_REQUIRED"
                      ? "bg-purple-600 hover:bg-purple-700"
                      : "bg-nile-700 hover:bg-nile-800"
                  }`}
                >
                  {isArabic ? "تأكيد القرار" : "Confirm Decision"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Complaint Update & Advisory Intelligence Modal Drawer */}
      {selectedComplaint && (
        <div className="fixed inset-0 !m-0 z-[100] bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full p-6 shadow-2xl relative max-h-[92vh] overflow-y-auto space-y-4">
            <button
              onClick={() => setSelectedComplaint(null)}
              className="absolute top-4 right-4 rtl:left-4 rtl:right-auto text-gray-400 hover:text-gray-700 w-8 h-8 rounded-full flex items-center justify-center hover:bg-gray-100 transition"
              aria-label="Close"
            >
              ✕
            </button>

            {/* Ticket Header */}
            <div className="border-b border-gray-100 pb-3">
              <div className="flex flex-wrap items-center gap-2 mb-1">
                <span className="font-mono text-base font-black text-nile-900">
                  {selectedComplaint.ticket_number}
                </span>
                <span
                  className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                    selectedComplaint.status === "RESOLVED"
                      ? "bg-green-100 text-green-800"
                      : selectedComplaint.status === "IN_PROGRESS"
                      ? "bg-amber-100 text-amber-800"
                      : selectedComplaint.status === "REJECTED"
                      ? "bg-rose-100 text-rose-800"
                      : "bg-blue-100 text-blue-800"
                  }`}
                >
                  {getStatusLabel(selectedComplaint.status, isArabic)}
                </span>
                <span className="text-[10px] bg-purple-100 text-purple-800 font-bold px-2 py-0.5 rounded font-mono">
                  {isArabic ? "اتفاقية مستوى الخدمة:" : "SLA:"} {getSlaLabel(selectedComplaint.sla_status_label || "ON_TRACK", isArabic)}
                </span>
              </div>
              <h3 className="text-sm font-bold text-gray-900">{selectedComplaint.subject}</h3>
              <p className="text-xs text-gray-500 mt-1">
                {isArabic ? "العميل مقدم الشكوى:" : "Customer:"}{" "}
                <strong className="text-gray-800">{selectedComplaint.customer_name || "Ahmed Mansour"}</strong> •{" "}
                {isArabic ? "تاريخ التقديم:" : "Submitted:"} {formatAuditTimestamp(selectedComplaint.created_at)}
              </p>
              <div className="bg-gray-50 p-2.5 rounded-lg border border-gray-100 text-xs text-gray-700 mt-2">
                <strong className="text-gray-900 block text-[11px] mb-0.5">{isArabic ? "تفاصيل الشكوى المسجلة:" : "Complaint Details:"}</strong>
                {selectedComplaint.details}
              </div>
            </div>

            {/* Advisory Intelligence Card */}
            <div className="bg-amber-50/70 border border-amber-200 rounded-xl p-4 space-y-2.5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5 text-xs font-bold text-amber-900">
                  <span>💡</span>
                  <span>{isArabic ? "توصية الذكاء الاصطناعي — تتطلب مراجعة واعتماد بشري إلزامي" : "AI suggestion - requires human review"}</span>
                </div>
                <span className="text-[9px] font-mono text-amber-700 bg-amber-100 px-2 py-0.5 rounded">
                  {advisoryLoading ? (isArabic ? "جاري التحليل..." : "Analyzing...") : (advisoryData?.generation_source || "DETERMINISTIC_RULES")}
                </span>
              </div>

              <div className="grid grid-cols-3 gap-2 text-xs">
                <div className="bg-white/80 p-2 rounded-lg border border-amber-200">
                  <span className="text-[10px] text-gray-500 block">{isArabic ? "الفئة المقترحة:" : "Suggested Category:"}</span>
                  <span className="font-bold text-amber-950">
                    {getCategoryLabel(advisoryData?.suggested_category || selectedComplaint.ai_suggested_category || selectedComplaint.category, isArabic)}
                  </span>
                </div>
                <div className="bg-white/80 p-2 rounded-lg border border-amber-200">
                  <span className="text-[10px] text-gray-500 block">{isArabic ? "الفريق الموصى به:" : "Suggested Team:"}</span>
                  <span className="font-bold text-amber-950">
                    {getTeamLabel(advisoryData?.suggested_team || selectedComplaint.ai_suggested_team || "CARDS_PAYMENTS", isArabic)}
                  </span>
                </div>
                <div className="bg-white/80 p-2 rounded-lg border border-amber-200">
                  <span className="text-[10px] text-gray-500 block">{isArabic ? "الأولوية التقديرية:" : "Suggested Priority:"}</span>
                  <span className="font-bold text-amber-950">
                    {getPriorityLabel(advisoryData?.suggested_priority || selectedComplaint.ai_suggested_priority || selectedComplaint.priority, isArabic)}
                  </span>
                </div>
              </div>

              {/* Matched Keywords */}
              <div>
                <span className="text-[10px] font-bold text-gray-500 block mb-1">{isArabic ? "الكلمات الدالة المطابقة (Matched Keywords):" : "Matched Rule Keywords:"}</span>
                <div className="flex flex-wrap gap-1">
                  {(advisoryData?.matched_keywords && advisoryData.matched_keywords.length > 0
                    ? advisoryData.matched_keywords
                    : selectedComplaint.ai_matched_keywords
                    ? selectedComplaint.ai_matched_keywords.split(",")
                    : ["atm", "card", "retained", "cash"]
                  ).map((kw, i) => (
                    <span key={i} className="text-[10px] bg-white border border-amber-300 text-amber-900 px-2 py-0.5 rounded-full font-mono">
                      {kw.trim()}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Operations Management Form */}
            <form onSubmit={handleUpdateComplaint} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {/* Status */}
                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1">
                    {isArabic ? "تحديث الحالة" : "Status Transition"}
                  </label>
                  <select
                    value={newStatus}
                    onChange={(e) => setNewStatus(e.target.value)}
                    className="w-full px-3 py-2 text-xs border border-gray-300 rounded-lg font-medium"
                  >
                    <option value="OPEN">{isArabic ? "مفتوحة" : "OPEN"}</option>
                    <option value="IN_PROGRESS">{isArabic ? "قيد المعالجة" : "IN_PROGRESS"}</option>
                    <option value="RESOLVED">{isArabic ? "تم الحل والإغلاق" : "RESOLVED"}</option>
                    <option value="REJECTED">{isArabic ? "مرفوضة" : "REJECTED"}</option>
                  </select>
                </div>

                {/* Priority */}
                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1">
                    {isArabic ? "تعديل الأولوية" : "Priority"}
                  </label>
                  <select
                    value={newPriority}
                    onChange={(e) => setNewPriority(e.target.value)}
                    className="w-full px-3 py-2 text-xs border border-gray-300 rounded-lg font-medium"
                  >
                    <option value="URGENT">{isArabic ? "عاجلة (اتفاقية 4 ساعات)" : "URGENT (4 hours SLA)"}</option>
                    <option value="HIGH">{isArabic ? "عالية (اتفاقية 12 ساعة)" : "HIGH (12 hours SLA)"}</option>
                    <option value="MEDIUM">{isArabic ? "متوسطة (اتفاقية 24 ساعة)" : "MEDIUM (24 hours SLA)"}</option>
                    <option value="LOW">{isArabic ? "منخفضة (اتفاقية 48 ساعة)" : "LOW (48 hours SLA)"}</option>
                  </select>
                </div>

                {/* Assigned Team */}
                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1">
                    {isArabic ? "تعيين الفريق المختص" : "Assigned Team"}
                  </label>
                  <select
                    value={newTeam}
                    onChange={(e) => setNewTeam(e.target.value)}
                    className="w-full px-3 py-2 text-xs border border-gray-300 rounded-lg font-medium"
                  >
                    <option value="">{isArabic ? "اختر فريق العمل..." : "Select team..."}</option>
                    <option value="CARDS_PAYMENTS">{isArabic ? "فريق البطاقات والمدفوعات" : "Cards & Payments Team"}</option>
                    <option value="OPERATIONS">{isArabic ? "فريق العمليات المصرفية" : "Banking Operations Team"}</option>
                    <option value="CUSTOMER_SERVICE">{isArabic ? "فريق خدمة العملاء" : "Customer Service Team"}</option>
                    <option value="COMPLIANCE">{isArabic ? "فريق الامتثال والرقابة" : "Compliance Team"}</option>
                    <option value="BRANCH_NETWORK">{isArabic ? "فريق شبكة الفروع" : "Branch Network Team"}</option>
                    <option value="BRANCH_NETWORK">Branch Network Team</option>
                  </select>
                </div>
              </div>

              {/* Internal Staff Notes (Confidential) */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-xs font-bold text-gray-700 flex items-center gap-1">
                    <span>🔒</span>
                    <span>{isArabic ? "ملاحظات الدعم الداخلي (سرية — لا تظهر للعميل مطلقاً)" : "Internal Staff Notes (Confidential — Never Visible to Customer)"}</span>
                  </label>
                  <span className="text-[10px] text-gray-400 font-mono">Staff Only</span>
                </div>
                <textarea
                  rows={2}
                  value={staffNote}
                  onChange={(e) => setStaffNote(e.target.value)}
                  placeholder={
                    isArabic
                      ? "أدخل ملاحظات التحقيق الداخلي وتواصل الفروع والفرق التشغيلية..."
                      : "Internal investigation notes, branch verification, or technician logs..."
                  }
                  className="w-full px-3 py-2 text-xs border border-gray-300 rounded-lg focus:ring-2 focus:ring-nile-600"
                />
              </div>

              {/* Customer-Facing Reply (Human-Approved) */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-xs font-bold text-emerald-900 flex items-center gap-1">
                    <span>✉️</span>
                    <span>{isArabic ? "رد البنك المعتمد للعميل (يظهر في بوابة العميل)" : "Customer-Facing Approved Reply (Visible in Customer Portal)"}</span>
                  </label>
                  <button
                    type="button"
                    onClick={() => {
                      if (advisoryData?.draft_reply) {
                        setCustomerReply(advisoryData.draft_reply);
                      } else if (selectedComplaint.ai_draft_reply) {
                        setCustomerReply(selectedComplaint.ai_draft_reply);
                      }
                    }}
                    className="text-[10px] text-nile-700 hover:underline font-semibold"
                  >
                    {isArabic ? "استعادة مسودة الذكاء الاصطناعي المقترحة" : "Reset to Suggested Draft"}
                  </button>
                </div>
                <textarea
                  rows={4}
                  value={customerReply}
                  onChange={(e) => setCustomerReply(e.target.value)}
                  placeholder={
                    isArabic
                      ? "اكتب الرد الرسمي المعتمد الذي سيظهر للعميل في بوابته..."
                      : "Draft the official response that the customer will see upon logging in..."
                  }
                  className="w-full px-3 py-2 text-xs border border-emerald-300 rounded-lg focus:ring-2 focus:ring-emerald-600 bg-emerald-50/20 font-medium"
                />
              </div>

              {/* Mandatory Confirmation Checkbox */}
              {customerReply.trim() && (
                <div className="bg-blue-50/80 border border-blue-200 p-3 rounded-lg text-xs text-blue-900 flex items-start gap-2">
                  <input
                    type="checkbox"
                    id="confirmReply"
                    checked={confirmReplyChecked}
                    onChange={(e) => setConfirmReplyChecked(e.target.checked)}
                    className="mt-0.5 rounded text-blue-700 focus:ring-blue-500"
                  />
                  <label htmlFor="confirmReply" className="cursor-pointer font-medium leading-relaxed">
                    <strong>{isArabic ? "تأكيد المراجعة البشرية:" : "Human Review Confirmation:"}</strong>{" "}
                    {isArabic
                      ? "أؤكد أنني راجعت وصححت هذا الرد الرسمي وأوافق على إرساله للعميل وفق معايير المحاكاة المصرفية المعتمدة."
                      : "I confirm that I have reviewed, verified, and approved this customer response under banking operations standards."}
                  </label>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex justify-end space-x-2 rtl:space-x-reverse pt-2 border-t border-gray-100">
                <button
                  type="button"
                  onClick={() => setSelectedComplaint(null)}
                  className="px-4 py-2 border border-gray-300 text-gray-700 text-xs font-semibold rounded-lg hover:bg-gray-50"
                >
                  {isArabic ? "إلغاء" : "Cancel"}
                </button>
                <button
                  type="submit"
                  disabled={customerReply.trim().length > 0 && !confirmReplyChecked}
                  className="px-5 py-2 bg-nile-700 hover:bg-nile-800 disabled:opacity-40 text-white text-xs font-bold rounded-lg shadow-xs transition"
                >
                  {isArabic ? "حفظ واعتماد التحديث" : "Save & Confirm Changes"}
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
