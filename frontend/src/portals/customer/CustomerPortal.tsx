import React, { useState, useEffect } from "react";
import { useLanguage } from "../../contexts/LanguageContext";
import { useAuth } from "../../contexts/AuthContext";
import {
  fetchCustomerAccounts,
  fetchCustomerTransactions,
  fetchCustomerComplaints,
  submitCustomerComplaint,
  fetchPublicProducts,
  fetchPublicCards,
  fetchCustomerAccountRequests,
  createCustomerAccountRequest,
  fetchCustomerCardRequests,
  createCustomerCardRequest,
  fetchCustomerKycStatus,
  submitCustomerKycUpdate,
} from "../../api/client";
import {
  BankAccount,
  Transaction,
  Complaint,
  ProductInfo,
  AccountOpeningRequest,
  CardRequest,
  CardProduct,
} from "../../types";
import { getStatusLabel, getCategoryLabel } from "../../utils/complaintTranslations";
import { RAGAssistant } from "../../components/RAGAssistant";

export const CustomerPortal: React.FC = () => {
  const { isArabic } = useLanguage();
  const { user } = useAuth();

  // Navigation tab
  const [activeTab, setActiveTab] = useState<"overview" | "open_account" | "request_card" | "requests" | "kyc_update">("overview");

  const [accounts, setAccounts] = useState<BankAccount[]>([]);
  const [selectedAccountId, setSelectedAccountId] = useState<string>("");
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [products, setProducts] = useState<ProductInfo[]>([]);
  const [cards, setCards] = useState<CardProduct[]>([]);

  // Simulated Requests
  const [accountRequests, setAccountRequests] = useState<AccountOpeningRequest[]>([]);
  const [cardRequests, setCardRequests] = useState<CardRequest[]>([]);

  // KYC Self-Service Update State
  const [kycRecord, setKycRecord] = useState<any>(null);
  const [kycFile, setKycFile] = useState<File | null>(null);
  const [kycUploading, setKycUploading] = useState<boolean>(false);

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [showComplaintModal, setShowComplaintModal] = useState<boolean>(false);
  const [showAllComplaints, setShowAllComplaints] = useState<boolean>(false);
  const [complaintForm, setComplaintForm] = useState({
    category: "ATM_CARD",
    subject: "",
    details: "",
  });
  const [formSuccess, setFormSuccess] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  // Account Request Form
  const [accForm, setAccForm] = useState({
    product_id: "prod-01",
    account_type: "current",
    initial_deposit: 5000,
    monthly_income: 12000,
    employment_status: "EMPLOYED",
    branch_code: "CAI-01",
  });

  // Card Request Form
  const [cardForm, setCardForm] = useState({
    linked_account_id: "",
    card_type: "DEBIT_VISA_CLASSIC",
    embossed_name: "",
    delivery_branch: "CAI-01",
  });

  // Interest Calculator State
  const [calcAmount, setCalcAmount] = useState<number>(100000);
  const [calcRate, setCalcRate] = useState<number>(23.5);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const results = await Promise.allSettled([
        fetchCustomerAccounts(),
        fetchCustomerComplaints(),
        fetchPublicProducts(),
        fetchPublicCards(),
        fetchCustomerAccountRequests(),
        fetchCustomerCardRequests(),
      ]);

      const [accsRes, cmpsRes, prodsRes, cardsRes, accReqsRes, cardReqsRes] = results;

      if (accsRes.status === "fulfilled") {
        setAccounts(accsRes.value);
        if (accsRes.value.length > 0) {
          setSelectedAccountId(accsRes.value[0].id);
          setCardForm((prev) => ({ ...prev, linked_account_id: accsRes.value[0].id }));
          try {
            const txs = await fetchCustomerTransactions(accsRes.value[0].id);
            setTransactions(txs);
          } catch (e) {
            console.error(e);
          }
        }
      }
      if (cmpsRes.status === "fulfilled") setComplaints(cmpsRes.value.filter((c: Complaint) => !c.is_test));
      if (prodsRes.status === "fulfilled") setProducts(prodsRes.value);
      if (cardsRes.status === "fulfilled") setCards(cardsRes.value);
      if (accReqsRes.status === "fulfilled") setAccountRequests(accReqsRes.value);
      if (cardReqsRes.status === "fulfilled") setCardRequests(cardReqsRes.value);

      try {
        const kyc = await fetchCustomerKycStatus();
        setKycRecord(kyc);
      } catch (e) {
        // Ignore if no prior kyc record
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    if (user?.full_name) {
      setCardForm((prev) => ({ ...prev, embossed_name: user.full_name.toUpperCase() }));
    }
  }, [user?.id]);

  const handleAccountChange = async (accId: string) => {
    setSelectedAccountId(accId);
    try {
      const txs = await fetchCustomerTransactions(accId);
      setTransactions(txs);
    } catch (err) {
      console.error(err);
    }
  };

  const handleComplaintSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setFormError(null);
    setFormSuccess(null);
    try {
      const newCmp = await submitCustomerComplaint(complaintForm);
      setComplaints([newCmp, ...complaints]);
      setFormSuccess(
        isArabic
          ? `تم تسجيل الشكوى بنجاح برقم مرجعي: ${newCmp.ticket_number}`
          : `Complaint ticket created successfully: ${newCmp.ticket_number}`
      );
      setComplaintForm({ category: "ATM_CARD", subject: "", details: "" });
      setTimeout(() => {
        setShowComplaintModal(false);
        setFormSuccess(null);
      }, 2500);
    } catch (err: any) {
      setFormError(err.message || "Failed to submit complaint");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAccountSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setFormError(null);
    setFormSuccess(null);
    try {
      const idempKey = `IDEMP-ACC-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`;
      const newReq = await createCustomerAccountRequest({
        ...accForm,
        idempotency_key: idempKey,
      });
      setAccountRequests([newReq, ...accountRequests]);
      setFormSuccess(
        isArabic
          ? `تم تقديم طلب فتح الحساب بنجاح برقم مرجعي: ${newReq.reference_number}`
          : `Account opening request submitted successfully: ${newReq.reference_number}`
      );
      setTimeout(() => {
        setActiveTab("requests");
        setFormSuccess(null);
      }, 1800);
    } catch (err: any) {
      setFormError(err.message || "Failed to submit account opening request");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCardSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setFormError(null);
    setFormSuccess(null);
    try {
      if (!cardForm.linked_account_id) {
        throw new Error(isArabic ? "يرجى اختيار الحساب المرتبط بالبطاقة" : "Please select an account for card linkage");
      }
      const idempKey = `IDEMP-CRD-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`;
      const newReq = await createCustomerCardRequest({
        ...cardForm,
        idempotency_key: idempKey,
      });
      setCardRequests([newReq, ...cardRequests]);
      setFormSuccess(
        isArabic
          ? `تم تقديم طلب إصدار البطاقة بنجاح برقم مرجعي: ${newReq.reference_number}`
          : `Card issuance request submitted successfully: ${newReq.reference_number}`
      );
      setTimeout(() => {
        setActiveTab("requests");
        setFormSuccess(null);
      }, 1800);
    } catch (err: any) {
      setFormError(err.message || "Failed to submit card request");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleKycSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!kycFile) {
      setFormError(isArabic ? "يرجى اختيار صورة بطاقة الرقم القومي أولاً." : "Please select an ID card image first.");
      return;
    }
    setKycUploading(true);
    setFormError(null);
    setFormSuccess(null);
    try {
      const res = await submitCustomerKycUpdate(kycFile);
      setKycRecord(res);
      setKycFile(null);
      setFormSuccess(
        isArabic
          ? `تم رفع وثيقة الرقم القومي بنجاح (رقم التتبع: ${res.tracking_number}). تم توجيه الوثيقة لمراجعة الامتثال المصرفي.`
          : `National ID document uploaded successfully (Tracking: ${res.tracking_number}). Routed to compliance review.`
      );
    } catch (err: any) {
      setFormError(err.message || (isArabic ? "فشل رفع الوثيقة" : "Failed to upload document"));
    } finally {
      setKycUploading(false);
    }
  };

  const formatCurrency = (val: number, cur: string = "EGP") => {
    return `${val.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${
      isArabic ? "ج.م" : cur
    }`;
  };

  const formatCustomerTimestamp = (ts: string) => {
    if (!ts) return "—";
    const d = new Date(ts);
    return `${d.toLocaleDateString("en-GB")} ${d.toLocaleTimeString("en-GB")} EET (UTC+2)`;
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

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "APPROVED_SIMULATED":
        return (
          <span className="bg-emerald-100 text-emerald-800 text-[10px] font-bold px-2 py-0.5 rounded">
            {isArabic ? "معتمد محاكاة" : "APPROVED (SIMULATED)"}
          </span>
        );
      case "SIMULATED_COMPLETED":
        return (
          <span className="bg-blue-100 text-blue-800 text-[10px] font-bold px-2 py-0.5 rounded">
            {isArabic ? "مكتمل محاكاة" : "SIMULATED COMPLETED"}
          </span>
        );
      case "REJECTED":
        return (
          <span className="bg-rose-100 text-rose-800 text-[10px] font-bold px-2 py-0.5 rounded">
            {isArabic ? "مرفوض" : "REJECTED"}
          </span>
        );
      case "MORE_INFO_REQUIRED":
        return (
          <span className="bg-purple-100 text-purple-800 text-[10px] font-bold px-2 py-0.5 rounded">
            {isArabic ? "استيفاء بيانات" : "MORE INFO REQUIRED"}
          </span>
        );
      case "UNDER_REVIEW":
        return (
          <span className="bg-amber-100 text-amber-800 text-[10px] font-bold px-2 py-0.5 rounded">
            {isArabic ? "قيد المراجعة" : "UNDER REVIEW"}
          </span>
        );
      case "SUBMITTED":
        return (
          <span className="bg-gray-100 text-gray-800 text-[10px] font-bold px-2 py-0.5 rounded">
            {isArabic ? "تم التقديم" : "SUBMITTED"}
          </span>
        );
      default:
        return <span className="bg-gray-100 text-gray-800 text-[10px] font-bold px-2 py-0.5 rounded">{status}</span>;
    }
  };

  const renderTimeline = (status: string, reviewerNotes?: string, rejectionReason?: string) => {
    const steps = [
      { id: "SUBMITTED", label_en: "Submitted", label_ar: "تم التقديم" },
      { id: "UNDER_REVIEW", label_en: "Under Review", label_ar: "قيد المراجعة" },
      {
        id: "DECISION",
        label_en:
          status === "REJECTED"
            ? "Rejected"
            : status === "MORE_INFO_REQUIRED"
            ? "More Info Required"
            : "Approved (Simulated)",
        label_ar:
          status === "REJECTED"
            ? "مرفوض"
            : status === "MORE_INFO_REQUIRED"
            ? "استيفاء بيانات"
            : "معتمد محاكاة",
      },
      { id: "SIMULATED_COMPLETED", label_en: "Completed", label_ar: "مكتمل" },
    ];

    const getStepState = (idx: number) => {
      if (status === "SIMULATED_COMPLETED") return "done";
      if (status === "APPROVED_SIMULATED") {
        return idx <= 2 ? "done" : "todo";
      }
      if (status === "REJECTED" || status === "MORE_INFO_REQUIRED") {
        return idx <= 2 ? "done" : "todo";
      }
      if (status === "UNDER_REVIEW") {
        return idx === 0 ? "done" : idx === 1 ? "current" : "todo";
      }
      return idx === 0 ? "current" : "todo";
    };

    return (
      <div className="space-y-2 pt-2">
        <div className="flex items-center space-x-2 rtl:space-x-reverse">
          {steps.map((st, i) => {
            const state = getStepState(i);
            const isDecisionStep = i === 2;
            const isFailed = isDecisionStep && status === "REJECTED";
            const isMoreInfo = isDecisionStep && status === "MORE_INFO_REQUIRED";

            return (
              <React.Fragment key={st.id}>
                <div className="flex items-center space-x-1.5 rtl:space-x-reverse">
                  <span
                    className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${
                      state === "done"
                        ? isFailed
                          ? "bg-rose-600 text-white"
                          : isMoreInfo
                          ? "bg-purple-600 text-white"
                          : "bg-emerald-600 text-white"
                        : state === "current"
                        ? "bg-amber-500 text-gray-900 ring-2 ring-amber-300"
                        : "bg-gray-200 text-gray-500"
                    }`}
                  >
                    {state === "done" ? (isFailed ? "✕" : isMoreInfo ? "ℹ" : "✓") : i + 1}
                  </span>
                  <span
                    className={`text-[11px] font-medium ${
                      state === "current"
                        ? "text-gray-900 font-bold"
                        : isFailed
                        ? "text-rose-700 font-bold"
                        : isMoreInfo
                        ? "text-purple-700 font-bold"
                        : "text-gray-500"
                    }`}
                  >
                    {isArabic ? st.label_ar : st.label_en}
                  </span>
                </div>
                {i < steps.length - 1 && (
                  <div
                    className={`flex-1 h-0.5 min-w-[16px] ${
                      state === "done"
                        ? isFailed
                          ? "bg-rose-300"
                          : isMoreInfo
                          ? "bg-purple-300"
                          : "bg-emerald-500"
                        : "bg-gray-200"
                    }`}
                  />
                )}
              </React.Fragment>
            );
          })}
        </div>

        {/* REJECTED DETAIL CALLOUT */}
        {status === "REJECTED" && (
          <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs">
            <div className="flex items-center gap-1.5 font-bold text-rose-900 mb-0.5">
              <span>❌</span>
              <span>{isArabic ? "قرار المراجعة: تم رفض الطلب" : "Review Decision: Application Rejected"}</span>
            </div>
            <p className="text-rose-800">
              <span className="font-semibold">{isArabic ? "سبب الرفض الإلزامي: " : "Mandatory Rejection Reason: "}</span>
              {rejectionReason || (isArabic ? "لم يتم استيفاء شروط فتح الحساب أو إصدار البطاقة." : "Eligibility criteria not satisfied.")}
            </p>
          </div>
        )}

        {/* MORE INFO REQUIRED DETAIL CALLOUT */}
        {status === "MORE_INFO_REQUIRED" && (
          <div className="p-3 rounded-lg bg-purple-50 border border-purple-200 text-xs">
            <div className="flex items-center gap-1.5 font-bold text-purple-900 mb-0.5">
              <span>ℹ️</span>
              <span>{isArabic ? "إجراء مطلوب: استيفاء بيانات ومستندات إضافية" : "Action Required: More Information Requested"}</span>
            </div>
            <p className="text-purple-800">
              <span className="font-semibold">{isArabic ? "إفادة مسؤول العمليات: " : "Reviewer Instructions: "}</span>
              {reviewerNotes || (isArabic ? "يرجى تقديم مستندات إضافية لاستكمال الطلب." : "Please submit additional documentation.")}
            </p>
          </div>
        )}

        {/* APPROVED DETAIL CALLOUT */}
        {status === "APPROVED_SIMULATED" && (
          <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-xs">
            <div className="flex items-center gap-1.5 font-bold text-emerald-900 mb-0.5">
              <span>✅</span>
              <span>{isArabic ? "قرار المراجعة: معتمد (محاكاة)" : "Review Decision: Approved (Simulated)"}</span>
            </div>
            {reviewerNotes && (
              <p className="text-emerald-800 mt-0.5">
                <span className="font-semibold">{isArabic ? "ملاحظات الاعتماد: " : "Approval Note: "}</span>
                {reviewerNotes}
              </p>
            )}
          </div>
        )}
      </div>
    );
  };

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-16 text-center text-gray-500">
        <div className="inline-block w-8 h-8 border-4 border-nile-700 border-t-transparent rounded-full animate-spin mb-3"></div>
        <p className="text-sm font-medium">{isArabic ? "جاري تحميل البيانات المصرفية..." : "Loading banking data..."}</p>
      </div>
    );
  }

  const selectedAccount = accounts.find((a) => a.id === selectedAccountId);

  return (
    <>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Customer Header Banner */}
      <div className="bg-gradient-to-r from-nile-800 to-nile-900 rounded-2xl p-6 text-white shadow-lg flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-semibold text-nile-200 uppercase tracking-wider block mb-1">
            {isArabic ? "بوابة الخدمات المصرفية للأفراد" : "Retail Banking Customer Portal"}
          </span>
          <h1 className="text-2xl font-bold">
            {isArabic ? `أهلاً بك، ${user?.full_name}` : `Welcome back, ${user?.full_name}`}
          </h1>
          <p className="text-xs text-nile-200 mt-1">
            {isArabic
              ? "بيانات حساباتك ومعاملاتك المصرفية آمنة ومحدثة لحظياً (محاكاة بنك النيل التجريبي)."
              : "Your simulated banking portfolio and transactions (NileOps Demo Bank)."}
          </p>
        </div>

        <button
          onClick={() => setShowComplaintModal(true)}
          className="px-4 py-2 bg-amber-500 hover:bg-amber-600 text-gray-900 font-bold text-xs rounded-lg shadow transition flex items-center space-x-2 rtl:space-x-reverse"
        >
          <span>✍️</span>
          <span>{isArabic ? "تقديم شكوى أو استفسار" : "Submit Complaint / Inquiry"}</span>
        </button>
      </div>

      {/* MANDATORY SIMULATION BANNER */}
      <div className="bg-amber-50 border-l-4 border-amber-500 p-4 rounded-r-xl shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div className="flex items-start md:items-center space-x-3 rtl:space-x-reverse">
          <span className="text-2xl flex-shrink-0">⚠️</span>
          <div>
            <h4 className="text-xs font-black text-amber-900 uppercase tracking-wider">
              {isArabic ? "تنبيه محاكاة مصرفية معتمدة" : "Simulated Digital Banking Platform"}
            </h4>
            <p className="text-xs font-bold text-amber-800 mt-0.5">
              {isArabic
                ? "SIMULATION — لا يتم إنشاء حسابات مصرفية حقيقية أو إصدار بطاقات ائتمانية فعلية. جميع الطلبات مخصصة للمحاكاة والتدريب فقط."
                : "SIMULATION — No real bank account or payment card is created. All products and numbers are simulated for operational demo purposes."}
            </p>
          </div>
        </div>
        <span className="text-[10px] font-mono font-bold bg-amber-200/90 text-amber-900 px-2.5 py-1 rounded flex-shrink-0">
          100% Synthetic Demo
        </span>
      </div>

      {/* PORTAL NAVIGATION TABS */}
      <div className="flex flex-wrap gap-2 border-b border-gray-200 pb-3">
        <button
          onClick={() => setActiveTab("overview")}
          className={`px-4 py-2 text-xs font-bold rounded-lg transition flex items-center space-x-2 rtl:space-x-reverse ${
            activeTab === "overview"
              ? "bg-nile-800 text-white shadow-sm"
              : "bg-gray-100 text-gray-700 hover:bg-gray-200"
          }`}
        >
          <span>🏛️</span>
          <span>{isArabic ? "الحسابات والمعاملات" : "Accounts & Overview"}</span>
        </button>

        <button
          onClick={() => setActiveTab("open_account")}
          className={`px-4 py-2 text-xs font-bold rounded-lg transition flex items-center space-x-2 rtl:space-x-reverse ${
            activeTab === "open_account"
              ? "bg-nile-800 text-white shadow-sm"
              : "bg-gray-100 text-gray-700 hover:bg-gray-200"
          }`}
        >
          <span>➕</span>
          <span>{isArabic ? "طلب فتح حساب جديد" : "Apply for Account"}</span>
        </button>

        <button
          onClick={() => setActiveTab("request_card")}
          className={`px-4 py-2 text-xs font-bold rounded-lg transition flex items-center space-x-2 rtl:space-x-reverse ${
            activeTab === "request_card"
              ? "bg-nile-800 text-white shadow-sm"
              : "bg-gray-100 text-gray-700 hover:bg-gray-200"
          }`}
        >
          <span>💳</span>
          <span>{isArabic ? "طلب إصدار بطاقة" : "Apply for Card"}</span>
        </button>

        <button
          onClick={() => setActiveTab("requests")}
          className={`px-4 py-2 text-xs font-bold rounded-lg transition flex items-center space-x-2 rtl:space-x-reverse ${
            activeTab === "requests"
              ? "bg-nile-800 text-white shadow-sm"
              : "bg-gray-100 text-gray-700 hover:bg-gray-200"
          }`}
        >
          <span>📋</span>
          <span>
            {isArabic ? "طلباتي ومتابعة الحالة" : "My Requests"} (
            {accountRequests.length + cardRequests.length})
          </span>
        </button>

        <button
          onClick={() => setActiveTab("kyc_update")}
          className={`px-4 py-2 text-xs font-bold rounded-lg transition flex items-center space-x-2 rtl:space-x-reverse ${
            activeTab === "kyc_update"
              ? "bg-nile-800 text-white shadow-sm"
              : "bg-gray-100 text-gray-700 hover:bg-gray-200"
          }`}
        >
          <span>🆔</span>
          <span>{isArabic ? "تحديث بيانات الهوية (KYC)" : "KYC ID Update"}</span>
          {kycRecord && (
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 font-mono">
              {kycRecord.status}
            </span>
          )}
        </button>
      </div>

      {formSuccess && (
        <div className="p-4 bg-emerald-50 border border-emerald-300 text-emerald-900 text-xs rounded-xl shadow-xs">
          <strong>✓ {isArabic ? "تم بنجاح:" : "Success:"}</strong> {formSuccess}
        </div>
      )}
      {formError && (
        <div className="p-4 bg-rose-50 border border-rose-300 text-rose-900 text-xs rounded-xl shadow-xs">
          <strong>✕ {isArabic ? "تنبيه:" : "Error:"}</strong> {formError}
        </div>
      )}

      {/* TAB 1: ACCOUNTS & OVERVIEW */}
      {activeTab === "overview" && (
        <div className="space-y-8">
          {/* Account Balances Grid */}
          <div>
            <h2 className="text-base font-bold text-gray-900 mb-3">
          {isArabic ? "الحسابات المصرفية والودائع" : "Accounts & Deposits Overview"}
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {accounts.map((acc) => {
            const isSelected = acc.id === selectedAccountId;
            return (
              <div
                key={acc.id}
                onClick={() => handleAccountChange(acc.id)}
                className={`p-5 rounded-xl border transition cursor-pointer ${
                  isSelected
                    ? "border-nile-600 bg-white ring-2 ring-nile-500/20 shadow-md"
                    : "border-gray-200 bg-white hover:border-gray-300 shadow-sm"
                }`}
              >
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-bold text-gray-500 uppercase">
                    {acc.account_type === "current"
                      ? isArabic
                        ? "حساب جاري"
                        : "Current Account"
                      : acc.account_type === "savings"
                      ? isArabic
                        ? "حساب توفير شهري"
                        : "High-Yield Savings"
                      : isArabic
                      ? "شهادة ادخارية 3 سنوات"
                      : "3-Year Certificate"}
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-green-100 text-green-800 font-bold">
                    {acc.status}
                  </span>
                </div>
                <div className="text-2xl font-black text-gray-900 mb-1">
                  {formatCurrency(acc.balance, acc.currency)}
                </div>
                <div className="flex items-center justify-between text-xs text-gray-500 pt-2 border-t border-gray-100 font-mono">
                  <span>{acc.account_number}</span>
                  {acc.interest_rate > 0 && (
                    <span className="text-nile-700 font-semibold font-sans">
                      {acc.interest_rate}% {isArabic ? "عائد سنوي" : "p.a."}
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Transaction History Table */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="p-5 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-gray-900">
              {isArabic ? "كشف المعاملات المصرفية" : "Transaction Statement"}
            </h3>
            <p className="text-xs text-gray-500">
              {selectedAccount
                ? isArabic
                  ? `معاملات الحساب رقم: ${selectedAccount.account_number}`
                  : `Showing records for account: ${selectedAccount.account_number}`
                : ""}
            </p>
          </div>
          <span className="text-xs bg-gray-100 text-gray-700 px-2.5 py-1 rounded font-medium">
            {transactions.length} {isArabic ? "معاملة" : "Transactions"}
          </span>
        </div>

        {transactions.length === 0 ? (
          <div className="p-8 text-center text-gray-400 text-xs">
            {isArabic ? "لا توجد معاملات مسجلة لهذا الحساب حالياً." : "No transactions recorded for this account."}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left rtl:text-right text-xs">
              <thead className="bg-gray-50 text-gray-600 font-semibold border-b border-gray-200">
                <tr>
                  <th className="px-5 py-3">{isArabic ? "الرقم المرجعي" : "Reference"}</th>
                  <th className="px-5 py-3">{isArabic ? "النوع" : "Type"}</th>
                  <th className="px-5 py-3">{isArabic ? "البيان" : "Description"}</th>
                  <th className="px-5 py-3">{isArabic ? "الجهة المقابلة" : "Counterparty"}</th>
                  <th className="px-5 py-3">{isArabic ? "التاريخ" : "Date"}</th>
                  <th className="px-5 py-3 text-right rtl:text-left">{isArabic ? "المبلغ" : "Amount"}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 text-gray-700">
                {transactions.map((tx) => {
                  const isPositive = tx.amount > 0;
                  return (
                    <tr key={tx.id} className="hover:bg-gray-50/80 transition">
                      <td className="px-5 py-3 font-mono font-medium text-gray-900">{tx.reference_number}</td>
                      <td className="px-5 py-3">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-gray-100 text-gray-800">
                          {tx.transaction_type}
                        </span>
                      </td>
                      <td className="px-5 py-3 font-medium text-gray-900">
                        {isArabic ? tx.description_ar : tx.description}
                      </td>
                      <td className="px-5 py-3 text-gray-500">{tx.counterparty || "—"}</td>
                      <td className="px-5 py-3 text-gray-500">
                        {new Date(tx.timestamp).toLocaleDateString("en-GB")}
                      </td>
                      <td
                        className={`px-5 py-3 font-mono font-bold text-right rtl:text-left ${
                          isPositive ? "text-emerald-600" : "text-gray-900"
                        }`}
                      >
                        {isPositive ? `+${formatCurrency(tx.amount)}` : formatCurrency(tx.amount)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Customer Complaints Section */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-gray-100 pb-4">
          <div>
            <h3 className="text-base font-bold text-gray-900">
              {isArabic ? "متابعة الشكاوى والطلبات المسجلة" : "My Complaints & Service Requests"}
            </h3>
            <p className="text-xs text-gray-500 mt-0.5">
              {isArabic
                ? "تتبع حالة شكاواك وملاحظات فريق الدعم الفني لحلها"
                : "Real-time tracking of operational tickets submitted to NileOps Demo Bank"}
            </p>
          </div>
        </div>

        {complaints.length === 0 ? (
          <p className="text-xs text-gray-500 italic py-4">
            {isArabic ? "لم تقم بتسجيل أي شكاوى حتى الآن." : "You have not submitted any complaints."}
          </p>
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {(showAllComplaints ? complaints : complaints.slice(0, 4)).map((c) => (
                <div key={c.id} className="p-4 rounded-xl border border-gray-200 bg-white shadow-xs space-y-3">
                  <div className="flex items-center justify-between border-b border-gray-100 pb-2">
                    <div>
                      <span className="font-mono text-xs font-bold text-nile-800">{c.ticket_number}</span>
                      <span className="text-[10px] text-gray-400 block font-medium">
                        {getCategoryLabel(c.category, isArabic)}
                      </span>
                    </div>
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
                  </div>

                  <div>
                    <div className="text-xs font-bold text-gray-900">{c.subject}</div>
                    <p className="text-xs text-gray-600 leading-relaxed mt-1">{c.details}</p>
                  </div>

                  {/* Customer-Facing Human-Approved Bank Reply ONLY */}
                  {c.customer_reply ? (
                    <div className="text-xs bg-emerald-50/90 p-3 rounded-lg border border-emerald-200 text-emerald-950 mt-2">
                      <strong className="text-emerald-900 block text-[11px] mb-1 flex items-center gap-1">
                        <span>✓</span>
                        <span>{isArabic ? "رد البنك المعتمد وتحديث المعالجة:" : "Official Bank Response & Action Taken:"}</span>
                      </strong>
                      <p className="whitespace-pre-line leading-relaxed font-medium">{c.customer_reply}</p>
                      {c.customer_reply_at && (
                        <span className="text-[10px] text-emerald-700 block mt-1.5 font-mono">
                          {formatCustomerTimestamp(c.customer_reply_at)}
                        </span>
                      )}
                    </div>
                  ) : c.resolution_notes ? (
                    <div className="text-xs bg-green-50 p-2.5 rounded-lg border border-green-200 text-green-900 mt-2">
                      <strong className="block text-[11px] mb-0.5">
                        {isArabic ? "قرار الإغلاق والحل النهائي:" : "Final Resolution:"}
                      </strong>
                      {c.resolution_notes}
                    </div>
                  ) : (
                    <div className="text-[11px] text-gray-400 italic bg-gray-50 p-2 rounded-lg border border-gray-100">
                      {isArabic
                        ? "جاري مراجعة الشكوى وتدقيقها من الفريق المختص..."
                        : "Ticket is actively undergoing operational investigation. Official response will appear here."}
                    </div>
                  )}

                  {/* Complaint Progression Stepper */}
                  <div className="pt-2 border-t border-gray-100">
                    <div className="flex items-center justify-between text-[10px] text-gray-500 font-medium">
                      <span className={`flex items-center gap-1 ${c.status === "OPEN" ? "font-bold text-blue-700" : ""}`}>
                        <span className={`w-2 h-2 rounded-full ${c.status ? "bg-blue-600" : "bg-gray-300"}`} />
                        {isArabic ? "تم الاستلام" : "Submitted"}
                      </span>
                      <span className="text-gray-300">───</span>
                      <span className={`flex items-center gap-1 ${c.status === "IN_PROGRESS" ? "font-bold text-amber-700" : ""}`}>
                        <span className={`w-2 h-2 rounded-full ${c.status === "IN_PROGRESS" || c.status === "RESOLVED" ? "bg-amber-500" : "bg-gray-300"}`} />
                        {isArabic ? "قيد المعالجة" : "In Progress"}
                      </span>
                      <span className="text-gray-300">───</span>
                      <span className={`flex items-center gap-1 ${c.status === "RESOLVED" ? "font-bold text-emerald-700" : c.status === "REJECTED" ? "font-bold text-rose-700" : ""}`}>
                        <span className={`w-2 h-2 rounded-full ${c.status === "RESOLVED" ? "bg-emerald-600" : c.status === "REJECTED" ? "bg-rose-600" : "bg-gray-300"}`} />
                        {c.status === "REJECTED" ? (isArabic ? "مرفوضة" : "Closed") : (isArabic ? "تم الحل" : "Resolved")}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {complaints.length > 4 && (
              <div className="text-center pt-2">
                <button
                  type="button"
                  onClick={() => setShowAllComplaints(!showAllComplaints)}
                  className="px-4 py-1.5 text-xs font-semibold text-nile-800 bg-nile-50 hover:bg-nile-100 rounded-lg transition"
                >
                  {showAllComplaints
                    ? (isArabic ? "عرض أقل (أحدث 4 شكاوى)" : "Show Less (Latest 4)")
                    : (isArabic ? `عرض جميع الشكاوى (${complaints.length})` : `View All Registered Tickets (${complaints.length})`)}
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Interactive Savings & Deposit Calculator */}
      <div className="bg-gradient-to-br from-gray-900 to-nile-950 text-white rounded-2xl p-6 shadow-md">
        <h3 className="text-base font-bold mb-2">
          {isArabic ? "حاسبة عوائد شهادات الادخار والودائع" : "Certificate of Deposit Yield Calculator"}
        </h3>
        <p className="text-xs text-gray-300 mb-6">
          {isArabic
            ? "احسب أرباحك التقديرية بالجنيه المصري بناءً على أسعار الفائدة الحالية المعتمدة."
            : "Estimate your monthly and total returns based on NileOps Demo Bank deposit rates."}
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
          <div>
            <label className="block text-xs font-semibold text-gray-300 mb-1">
              {isArabic ? "مبلغ الشهادة (جنيه مصري)" : "Deposit Amount (EGP)"}
            </label>
            <input
              type="number"
              min="1000"
              step="5000"
              value={calcAmount}
              onChange={(e) => setCalcAmount(Number(e.target.value))}
              className="w-full px-3 py-2 text-sm bg-gray-800 border border-gray-700 rounded-lg text-white font-mono focus:ring-2 focus:ring-nile-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-300 mb-1">
              {isArabic ? "سعر العائد السنوي (%)" : "Annual Interest Rate (%)"}
            </label>
            <select
              value={calcRate}
              onChange={(e) => setCalcRate(Number(e.target.value))}
              className="w-full px-3 py-2 text-sm bg-gray-800 border border-gray-700 rounded-lg text-white font-mono focus:ring-2 focus:ring-nile-500"
            >
              <option value="23.5">23.5% (شهادة النيل البلاتينية 3 سنوات)</option>
              <option value="12.5">12.5% (حساب التوفير الشهري)</option>
              <option value="18.0">18.0% (شهادة سنوية)</option>
            </select>
          </div>

          <div className="bg-gray-800/80 p-4 rounded-xl border border-gray-700">
            <span className="text-xs text-gray-400 block mb-1">
              {isArabic ? "العائد الشهري التقديري:" : "Estimated Monthly Payout:"}
            </span>
            <div className="text-xl font-bold text-emerald-400 font-mono">
              {formatCurrency((calcAmount * (calcRate / 100)) / 12)}
            </div>
            <span className="text-[11px] text-gray-400 block mt-1">
              {isArabic ? `إجمالي العائد السنوي: ${formatCurrency(calcAmount * (calcRate / 100))}` : `Total Annual Yield: ${formatCurrency(calcAmount * (calcRate / 100))}`}
            </span>
          </div>
        </div>
      </div>

      {/* Available Banking Products */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 space-y-4">
        <h3 className="text-base font-bold text-gray-900">
          {isArabic ? "باقات وحسابات بنك النيل المتاحة" : "Available Banking Products"}
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {products.map((p) => (
            <div key={p.id} className="p-4 rounded-lg border border-gray-100 bg-gray-50/50 space-y-2">
              <span className="text-[10px] font-bold text-nile-700 uppercase block">{p.category}</span>
              <h4 className="text-xs font-bold text-gray-900">{isArabic ? p.name_ar : p.name_en}</h4>
              <p className="text-[11px] text-gray-500 leading-relaxed">{isArabic ? p.description_ar : p.description_en}</p>
              {p.interest_rate > 0 && (
                <div className="text-xs font-mono font-bold text-emerald-700">
                  {p.interest_rate}% {isArabic ? "عائد سنوي" : "annual yield"}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
      </div>
      )}

      {/* TAB 2: APPLY FOR NEW ACCOUNT */}
      {activeTab === "open_account" && (
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 sm:p-8 space-y-6">
          <div className="border-b border-gray-100 pb-4">
            <h2 className="text-xl font-black text-gray-900">
              {isArabic ? "طلب فتح حساب بنكي جديد (محاكاة)" : "Apply for New Bank Account (Simulated)"}
            </h2>
            <p className="text-xs text-gray-500 mt-1">
              {isArabic
                ? "اختر باقة الحساب واملأ البيانات المبدئية لتقييمها وفق القواعد المصرفية المعتمدة."
                : "Select product and submit initial deposit information for rule-based verification."}
            </p>
          </div>

          <form onSubmit={handleAccountSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-xs font-bold text-gray-700 mb-2">
                  {isArabic ? "نوع المنتج المصرفي" : "Banking Product"}
                </label>
                <select
                  value={accForm.product_id}
                  onChange={(e) => {
                    const pid = e.target.value;
                    let atype = "current";
                    let minDep = 2500;
                    if (pid === "prod-02") {
                      atype = "savings";
                      minDep = 10000;
                    } else if (pid === "prod-03") {
                      atype = "certificate";
                      minDep = 1000;
                    }
                    setAccForm({ ...accForm, product_id: pid, account_type: atype, initial_deposit: minDep });
                  }}
                  className="w-full px-3.5 py-2.5 text-xs border border-gray-300 rounded-xl font-medium focus:ring-2 focus:ring-nile-600 focus:border-nile-600"
                >
                  <option value="prod-01">Classic Current Account (الحد الأدنى: 2,500 ج.م)</option>
                  <option value="prod-02">High-Yield Monthly Savings (الحد الأدنى: 10,000 ج.م - 12.5% عائد)</option>
                  <option value="prod-03">Nile Platinum 3-Year Certificate (الحد الأدنى: 1,000 ج.م - 23.5% عائد)</option>
                </select>
                <p className="text-[11px] text-gray-500 mt-1.5">
                  {isArabic
                    ? "يخضع الطلب للتحقق الآلي من الحد الأدنى لرصيد الافتتاح ووثيقة الهوية."
                    : "Requests undergo deterministic rule evaluation against minimum balance and KYC."}
                </p>
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 mb-2">
                  {isArabic ? "مبلغ الإيداع الافتتاحي (جنيه مصري)" : "Initial Deposit Amount (EGP)"}
                </label>
                <input
                  type="number"
                  min="0"
                  step="500"
                  required
                  value={accForm.initial_deposit}
                  onChange={(e) => setAccForm({ ...accForm, initial_deposit: Number(e.target.value) })}
                  className="w-full px-3.5 py-2.5 text-xs font-mono border border-gray-300 rounded-xl focus:ring-2 focus:ring-nile-600 focus:border-nile-600"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 mb-2">
                  {isArabic ? "الدخل الشهري التقديري (جنيه مصري)" : "Monthly Income (EGP)"}
                </label>
                <input
                  type="number"
                  min="0"
                  step="500"
                  required
                  value={accForm.monthly_income}
                  onChange={(e) => setAccForm({ ...accForm, monthly_income: Number(e.target.value) })}
                  className="w-full px-3.5 py-2.5 text-xs font-mono border border-gray-300 rounded-xl focus:ring-2 focus:ring-nile-600 focus:border-nile-600"
                />
                <span className="text-[10px] text-gray-400 mt-1 block">
                  {isArabic ? "الحد الأدنى الموصى به: 3,000 ج.م" : "Standard guideline: 3,000+ EGP"}
                </span>
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 mb-2">
                  {isArabic ? "الحالة الوظيفية" : "Employment Status"}
                </label>
                <select
                  value={accForm.employment_status}
                  onChange={(e) => setAccForm({ ...accForm, employment_status: e.target.value })}
                  className="w-full px-3.5 py-2.5 text-xs border border-gray-300 rounded-xl font-medium focus:ring-2 focus:ring-nile-600"
                >
                  <option value="EMPLOYED">{isArabic ? "موظف قطاع عام / خاص" : "Employed (Salaried)"}</option>
                  <option value="SELF_EMPLOYED">{isArabic ? "أعمال حرة / صاحب عمل" : "Self-Employed / Business Owner"}</option>
                  <option value="PROFESSIONAL">{isArabic ? "مهن حرة (طبيب/مهندس/محامي)" : "Licensed Professional"}</option>
                  <option value="RETIRED">{isArabic ? "متقاعد / معاش" : "Retired"}</option>
                  <option value="STUDENT">{isArabic ? "طالب جامعي" : "Student"}</option>
                </select>
              </div>

              <div className="md:col-span-2">
                <label className="block text-xs font-bold text-gray-700 mb-2">
                  {isArabic ? "فرع فتح الحساب المفضل" : "Preferred Branch"}
                </label>
                <select
                  value={accForm.branch_code}
                  onChange={(e) => setAccForm({ ...accForm, branch_code: e.target.value })}
                  className="w-full px-3.5 py-2.5 text-xs border border-gray-300 rounded-xl font-medium focus:ring-2 focus:ring-nile-600"
                >
                  <option value="CAI-01">فرع الزمالك الرئيسي (Zamalek Main Branch) — القاهرة</option>
                  <option value="CAI-02">فرع التجمع الخامس (New Cairo 5th Settlement) — القاهرة الجديدة</option>
                  <option value="ALX-01">فرع سموحة (Alexandria Smouha Branch) — الإسكندرية</option>
                </select>
              </div>
            </div>

            <div className="bg-gray-50 border border-gray-200 p-4 rounded-xl text-xs space-y-1 text-gray-600">
              <span className="font-bold text-gray-900 block">{isArabic ? "شروط وسياسات فتح الحساب التقديري:" : "Account Opening Policy Summary:"}</span>
              <p>• {isArabic ? "يجب توفر بطاقة رقم قومي اصطناعية معتمدة في محطة تدقيق الهوية (KYC Approved)." : "Approved synthetic KYC verification is required."}</p>
              <p>• {isArabic ? "لا يتم تفعيل الحساب أو إصدار رقم IBAN حقيقي، وتخضع العملية للمراجعة المزدوجة." : "Dual-control review applies. No authentic banking credentials issued."}</p>
            </div>

            <div className="flex items-center justify-end space-x-3 rtl:space-x-reverse pt-2">
              <button
                type="button"
                onClick={() => setActiveTab("overview")}
                className="px-5 py-2.5 border border-gray-300 text-gray-700 text-xs font-bold rounded-xl hover:bg-gray-50 transition"
              >
                {isArabic ? "إلغاء" : "Cancel"}
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-6 py-2.5 bg-nile-800 hover:bg-nile-900 text-white text-xs font-bold rounded-xl shadow transition disabled:opacity-50"
              >
                {isSubmitting ? (isArabic ? "جاري الإرسال..." : "Submitting...") : (isArabic ? "تأكيد تقديم طلب فتح الحساب" : "Submit Account Application")}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* TAB 3: APPLY FOR PAYMENT CARD */}
      {activeTab === "request_card" && (
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 sm:p-8 space-y-6">
          <div className="border-b border-gray-100 pb-4">
            <h2 className="text-xl font-black text-gray-900">
              {isArabic ? "طلب إصدار بطاقة مصرفية (محاكاة)" : "Apply for Payment Card (Simulated)"}
            </h2>
            <p className="text-xs text-gray-500 mt-1">
              {isArabic
                ? "اختر الحساب المرتبط ونوع البطاقة لاستكمال إجراءات الإصدار التقديرية."
                : "Select linked account and payment card type for simulated issuance."}
            </p>
          </div>

          {accounts.length === 0 ? (
            <div className="p-8 text-center text-xs text-amber-800 bg-amber-50 rounded-xl border border-amber-200">
              {isArabic
                ? "لا توجد لديك حسابات مصرفية نشطة حالياً لربط البطاقة بها. يرجى تقديم طلب فتح حساب أولاً."
                : "No active deposit accounts found to link a card. Please submit an account opening request first."}
            </div>
          ) : (
            <form onSubmit={handleCardSubmit} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-2">
                    {isArabic ? "الحساب المرتبط بالبطاقة" : "Linked Bank Account"}
                  </label>
                  <select
                    value={cardForm.linked_account_id}
                    onChange={(e) => setCardForm({ ...cardForm, linked_account_id: e.target.value })}
                    className="w-full px-3.5 py-2.5 text-xs font-mono border border-gray-300 rounded-xl focus:ring-2 focus:ring-nile-600"
                  >
                    {accounts.map((a) => (
                      <option key={a.id} value={a.id}>
                        {a.account_number} ({a.account_type.toUpperCase()} - {formatCurrency(a.balance, a.currency)})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-2">
                    {isArabic ? "نوع البطاقة المصرفية" : "Card Product Type"}
                  </label>
                  <select
                    value={cardForm.card_type}
                    onChange={(e) => setCardForm({ ...cardForm, card_type: e.target.value })}
                    className="w-full px-3.5 py-2.5 text-xs border border-gray-300 rounded-xl font-medium focus:ring-2 focus:ring-nile-600"
                  >
                    {cards.length > 0 ? (
                      cards.map((c) => (
                        <option key={c.id} value={c.id}>
                          {isArabic ? c.name_ar : c.name_en}
                        </option>
                      ))
                    ) : (
                      <>
                        <option value="DEBIT_VISA_CLASSIC">Nile Classic Visa Debit Card (خصم مباشر فيزا)</option>
                        <option value="DEBIT_MASTERCARD_TITANIUM">Nile Titanium Mastercard Debit Card (ماستركارد تيتانيوم)</option>
                        <option value="CREDIT_VISA_PLATINUM">Nile Platinum Visa Credit Card (فيزا بلاتينية ائتمانية)</option>
                        <option value="PREPAID_MEEZA">Nile Meeza National Prepaid Card (بطاقة ميزة الوطنية)</option>
                      </>
                    )}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-2">
                    {isArabic ? "الاسم المطبوع على البطاقة" : "Embossed Name on Card"}
                  </label>
                  <input
                    type="text"
                    required
                    value={cardForm.embossed_name}
                    onChange={(e) => setCardForm({ ...cardForm, embossed_name: e.target.value.toUpperCase() })}
                    placeholder="TAREK NOUR"
                    className="w-full px-3.5 py-2.5 text-xs font-mono uppercase tracking-wider border border-gray-300 rounded-xl focus:ring-2 focus:ring-nile-600"
                  />
                  <span className="text-[10px] text-gray-400 mt-1 block">
                    {isArabic ? "حروف إنجليزية لاتينية كبيرة فقط" : "Uppercase Latin characters only"}
                  </span>
                </div>

                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-2">
                    {isArabic ? "فرع استلام البطاقة" : "Delivery / Pick-up Branch"}
                  </label>
                  <select
                    value={cardForm.delivery_branch}
                    onChange={(e) => setCardForm({ ...cardForm, delivery_branch: e.target.value })}
                    className="w-full px-3.5 py-2.5 text-xs border border-gray-300 rounded-xl font-medium focus:ring-2 focus:ring-nile-600"
                  >
                    <option value="CAI-01">فرع الزمالك الرئيسي (Zamalek Main Branch) — القاهرة</option>
                    <option value="CAI-02">فرع التجمع الخامس (New Cairo 5th Settlement) — القاهرة الجديدة</option>
                    <option value="ALX-01">فرع سموحة (Alexandria Smouha Branch) — الإسكندرية</option>
                  </select>
                </div>
              </div>

              {/* CARD PREVIEW MOCKUP */}
              <div className="bg-slate-900 rounded-2xl p-6 text-white max-w-sm mx-auto shadow-xl relative overflow-hidden border border-gray-700">
                <div className="flex justify-between items-start mb-6">
                  <div>
                    <span className="text-[10px] tracking-widest text-amber-300 font-bold block">NILEOPS DEMO BANK</span>
                    <span className="text-[9px] text-gray-400">DIGITAL BANKING SIMULATION</span>
                  </div>
                  <span className="text-xs font-bold bg-amber-400 text-gray-950 px-2 py-0.5 rounded text-[9px] uppercase font-mono">
                    SIMULATED
                  </span>
                </div>
                <div className="text-xl mb-4 font-mono">📟 🪪</div>
                <div className="font-mono text-base tracking-widest text-gray-200 mb-4">
                  4211 •••• •••• 8890
                </div>
                <div className="flex justify-between items-end text-xs font-mono">
                  <div>
                    <span className="text-[9px] text-gray-400 block">CARDHOLDER</span>
                    <span className="font-bold tracking-wider">{cardForm.embossed_name || "CUSTOMER NAME"}</span>
                  </div>
                  <div className="text-right">
                    <span className="text-[9px] text-gray-400 block">EXPIRES</span>
                    <span className="font-bold">12/29</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-end space-x-3 rtl:space-x-reverse pt-2">
                <button
                  type="button"
                  onClick={() => setActiveTab("overview")}
                  className="px-5 py-2.5 border border-gray-300 text-gray-700 text-xs font-bold rounded-xl hover:bg-gray-50 transition"
                >
                  {isArabic ? "إلغاء" : "Cancel"}
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-6 py-2.5 bg-nile-800 hover:bg-nile-900 text-white text-xs font-bold rounded-xl shadow transition disabled:opacity-50"
                >
                  {isSubmitting ? (isArabic ? "جاري الإرسال..." : "Submitting...") : (isArabic ? "تأكيد تقديم طلب البطاقة" : "Submit Card Request")}
                </button>
              </div>
            </form>
          )}
        </div>
      )}

      {/* TAB 4: MY REQUESTS & STATUS TIMELINE */}
      {activeTab === "requests" && (
        <div className="space-y-6">
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <h2 className="text-xl font-black text-gray-900">
                {isArabic ? "سجل الطلبات المصرفية ومتابعة الحالة" : "My Requests & Lifecycle Timeline"}
              </h2>
              <p className="text-xs text-gray-500 mt-1">
                {isArabic
                  ? "تتبع مراحل معالجة طلبات فتح الحسابات وإصدار البطاقات خطوة بخطوة."
                  : "Track real-time progression of account and card requests through the governance state machine."}
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setActiveTab("open_account")}
                className="px-3.5 py-1.5 bg-nile-800 text-white text-xs font-bold rounded-lg hover:bg-nile-900 shadow-xs transition"
              >
                + {isArabic ? "طلب حساب" : "New Account"}
              </button>
              <button
                onClick={() => setActiveTab("request_card")}
                className="px-3.5 py-1.5 bg-amber-500 text-gray-900 text-xs font-bold rounded-lg hover:bg-amber-600 shadow-xs transition"
              >
                + {isArabic ? "طلب بطاقة" : "New Card"}
              </button>
            </div>
          </div>

          {/* Account Opening Requests List */}
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 space-y-4">
            <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider">
              {isArabic ? "طلبات فتح الحسابات المسجلة" : "Account Opening Requests"} ({accountRequests.length})
            </h3>
            {accountRequests.length === 0 ? (
              <p className="text-xs text-gray-400 italic py-3">
                {isArabic ? "لم تقم بتقديم أي طلبات فتح حساب بعد." : "No account opening requests recorded."}
              </p>
            ) : (
              <div className="space-y-4">
                {accountRequests.map((req) => (
                  <div key={req.id} className="p-5 rounded-xl border border-gray-200 bg-gray-50/60 space-y-3">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-gray-200 pb-3">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-black text-nile-900">{req.reference_number}</span>
                        {getStatusBadge(req.status)}
                      </div>
                      <span className="text-[11px] text-gray-500 font-mono">
                        {formatCustomerTimestamp(req.created_at)}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                      <div>
                        <span className="text-gray-400 text-[10px] block">{isArabic ? "اسم المنتج المصرفي:" : "Product Name:"}</span>
                        <span className="font-bold text-gray-900">{req.product_name || getAccountProductName(req.product_id)}</span>
                      </div>
                      <div>
                        <span className="text-gray-400 text-[10px] block">{isArabic ? "الإيداع المبدئي:" : "Initial Deposit:"}</span>
                        <span className="font-mono font-bold text-emerald-700">{formatCurrency(req.initial_deposit, req.currency)}</span>
                      </div>
                      <div>
                        <span className="text-gray-400 text-[10px] block">{isArabic ? "الدخل الشهري:" : "Monthly Income:"}</span>
                        <span className="font-mono text-gray-800">{formatCurrency(req.monthly_income, req.currency)}</span>
                      </div>
                      <div>
                        <span className="text-gray-400 text-[10px] block">{isArabic ? "الفرع:" : "Branch:"}</span>
                        <span className="text-gray-800 font-medium">{req.branch_code}</span>
                      </div>
                    </div>

                    {/* Timeline visualization */}
                    <div className="bg-white p-3 rounded-lg border border-gray-200">
                      <span className="text-[10px] font-bold text-gray-400 block mb-1 uppercase tracking-wider">
                        {isArabic ? "مسار معالجة الطلب (Request Progression):" : "Lifecycle Progression:"}
                      </span>
                      {renderTimeline(req.status, req.reviewer_notes, req.rejection_reason)}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Card Issuance Requests List */}
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 space-y-4">
            <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider">
              {isArabic ? "طلبات إصدار البطاقات المسجلة" : "Card Issuance Requests"} ({cardRequests.length})
            </h3>
            {cardRequests.length === 0 ? (
              <p className="text-xs text-gray-400 italic py-3">
                {isArabic ? "لم تقم بتقديم أي طلبات إصدار بطاقة بعد." : "No card requests recorded."}
              </p>
            ) : (
              <div className="space-y-4">
                {cardRequests.map((req) => (
                  <div key={req.id} className="p-5 rounded-xl border border-gray-200 bg-gray-50/60 space-y-3">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-gray-200 pb-3">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-black text-nile-900">{req.reference_number}</span>
                        {getStatusBadge(req.status)}
                      </div>
                      <span className="text-[11px] text-gray-500 font-mono">
                        {formatCustomerTimestamp(req.created_at)}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                      <div>
                        <span className="text-gray-400 text-[10px] block">{isArabic ? "اسم البطاقة المصرفية:" : "Card Name:"}</span>
                        <span className="font-bold text-gray-900">{req.card_name || getCardProductName(req.card_type)}</span>
                      </div>
                      <div>
                        <span className="text-gray-400 text-[10px] block">{isArabic ? "الاسم المطبوع:" : "Embossed Name:"}</span>
                        <span className="font-mono font-bold text-gray-800">{req.embossed_name}</span>
                      </div>
                      <div>
                        <span className="text-gray-400 text-[10px] block">{isArabic ? "فرع الاستلام:" : "Delivery Branch:"}</span>
                        <span className="text-gray-800 font-medium">{req.delivery_branch}</span>
                      </div>
                      <div>
                        <span className="text-gray-400 text-[10px] block">{isArabic ? "الحساب المرتبط:" : "Account ID:"}</span>
                        <span className="font-mono text-gray-500 text-[11px] truncate block">{req.linked_account_id.slice(0, 8)}...</span>
                      </div>
                    </div>

                    {/* Timeline visualization */}
                    <div className="bg-white p-3 rounded-lg border border-gray-200">
                      <span className="text-[10px] font-bold text-gray-400 block mb-1 uppercase tracking-wider">
                        {isArabic ? "مسار معالجة الطلب (Request Progression):" : "Lifecycle Progression:"}
                      </span>
                      {renderTimeline(req.status, req.reviewer_notes, req.rejection_reason)}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 5: KYC ID UPDATE */}
      {activeTab === "kyc_update" && (
        <div className="space-y-6">
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
            <h2 className="text-xl font-black text-gray-900 mb-1">
              {isArabic ? "تحديث بيانات الهوية الوطنية (KYC)" : "National ID Self-Service Update (KYC)"}
            </h2>
            <p className="text-xs text-gray-500 mb-6">
              {isArabic
                ? "قم برفع صورة واضحة لبطاقة الرقم القومي (الوجه الأمامي) لتحديث بياناتك البنكية طبقاً لتعليمات البنك المركزي المصري."
                : "Upload a clear synthetic Egyptian National ID card front image to update your profile under CBE regulations."}
            </p>

            {/* Current KYC Verification Status Card */}
            {kycRecord ? (
              <div className="bg-gray-50 border border-gray-200 rounded-xl p-5 mb-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
                  <div>
                    <span className="text-[10px] uppercase font-bold text-gray-400 tracking-wider block">
                      {isArabic ? "رقم تتبع طلب التحقق" : "Verification Tracking Number"}
                    </span>
                    <span className="font-mono font-bold text-gray-900 text-sm">{kycRecord.tracking_number}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800">
                      {kycRecord.status}
                    </span>
                    <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-gray-200 text-gray-700">
                      {kycRecord.identity_verification_status || "NOT_VERIFIED"}
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
                  <div>
                    <span className="text-gray-400 block mb-0.5">{isArabic ? "الرقم القومي (محمي):" : "National ID (Masked):"}</span>
                    <span className="font-mono font-bold text-gray-800">{kycRecord.synthetic_national_id}</span>
                  </div>
                  <div>
                    <span className="text-gray-400 block mb-0.5">{isArabic ? "نوع الوثيقة:" : "Document Type:"}</span>
                    <span className="font-medium text-gray-700">{kycRecord.document_type}</span>
                  </div>
                  <div>
                    <span className="text-gray-400 block mb-0.5">{isArabic ? "تاريخ التقديم:" : "Submission Date:"}</span>
                    <span className="font-medium text-gray-700">{formatCustomerTimestamp(kycRecord.created_at)}</span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6 text-xs text-blue-900">
                ℹ️ {isArabic
                  ? "لا يوجد سجل تحديث هوية مسجل لك حالياً. يمكنك رفع بطاقتك الآن لتنشيط المراجعة الدورية."
                  : "No prior KYC update record found on file. You can upload an ID card below to trigger compliance review."}
              </div>
            )}

            {/* Document Upload Form */}
            <form onSubmit={handleKycSubmit} className="space-y-5">
              <div className="border-2 border-dashed border-gray-300 rounded-xl p-6 text-center hover:border-nile-600 transition">
                <input
                  type="file"
                  id="kyc-file-input"
                  accept="image/png,image/jpeg,image/webp"
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      setKycFile(e.target.files[0]);
                    }
                  }}
                  className="hidden"
                />
                <label htmlFor="kyc-file-input" className="cursor-pointer block">
                  <div className="text-3xl mb-2">📷</div>
                  <span className="text-xs font-bold text-nile-800 hover:text-nile-900 block">
                    {kycFile ? kycFile.name : (isArabic ? "اختر صورة بطاقة الرقم القومي (PNG, JPEG, WebP)" : "Select National ID Card Image (PNG, JPEG, WebP)")}
                  </span>
                  <span className="text-[11px] text-gray-400 mt-1 block">
                    {isArabic ? "الحد الأقصى لحجم الملف: 10 ميجابايت" : "Max file size: 10 MB"}
                  </span>
                </label>
              </div>

              {/* Four-Eyes and NOT_VERIFIED Invariant Callout */}
              <div className="bg-amber-50 border-l-4 border-amber-500 p-3 rounded-r-lg text-xs text-amber-900 space-y-1">
                <div className="font-bold flex items-center gap-1.5">
                  <span>🔒</span>
                  <span>{isArabic ? "ضوابط وسياسات الامتثال المصرفي (Four-Eyes & NOT_VERIFIED)" : "Banking Compliance Controls"}</span>
                </div>
                <p className="text-amber-800 text-[11px]">
                  {isArabic
                    ? "يتم فحص الوثيقة آلياً عبر محرك الذكاء الاصطناعي لاستخراج البيانات واكتشاف أي تعارض، وتظل حالة الهوية (NOT_VERIFIED) لحين مراجعتها واعتمادها بشرياً من قبل مسؤول الامتثال وفق مبدأ الرقابة الثنائية."
                    : "Uploaded documents are processed by Document AI OCR with automated cross-field validation. Identity status strictly remains NOT_VERIFIED pending dual-control review by an authorized compliance officer."}
                </p>
              </div>

              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={!kycFile || kycUploading}
                  className="px-6 py-2.5 bg-nile-800 hover:bg-nile-900 disabled:opacity-50 text-white font-bold text-xs rounded-lg shadow transition flex items-center gap-2"
                >
                  {kycUploading && <span className="inline-block w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>}
                  <span>{isArabic ? "رفع الوثيقة وبدء التحقق" : "Upload Document & Verify"}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      </div>

      {/* Complaint Submission Modal */}
      {showComplaintModal && (
        <div className="fixed inset-0 !m-0 z-[100] bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl relative">
            <button
              onClick={() => setShowComplaintModal(false)}
              className="absolute top-4 right-4 rtl:left-4 rtl:right-auto text-gray-400 hover:text-gray-700 w-8 h-8 rounded-full flex items-center justify-center hover:bg-gray-100 transition"
              aria-label="Close"
            >
              ✕
            </button>

            <h3 className="text-lg font-bold text-gray-900 mb-1">
              {isArabic ? "تسجيل شكوى أو طلب مساعدة" : "Submit Operational Complaint"}
            </h3>
            <p className="text-xs text-gray-500 mb-4">
              {isArabic
                ? "سيتم تحويل طلبك لفريق العمليات وخدمة العملاء لمتابعته فوراً"
                : "Your ticket will be routed to customer service & operations staff"}
            </p>

            {formSuccess && (
              <div className="p-3 mb-4 bg-green-50 border border-green-200 text-green-800 text-xs rounded-lg">
                {formSuccess}
              </div>
            )}
            {formError && (
              <div className="p-3 mb-4 bg-red-50 border border-red-200 text-red-800 text-xs rounded-lg">
                {formError}
              </div>
            )}

            <form onSubmit={handleComplaintSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  {isArabic ? "فئة الشكوى" : "Category"}
                </label>
                <select
                  value={complaintForm.category}
                  onChange={(e) => setComplaintForm({ ...complaintForm, category: e.target.value })}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg"
                >
                  <option value="ATM_CARD">{isArabic ? "بطاقات الصراف الآلي" : "ATM & Debit Cards"}</option>
                  <option value="TRANSFER">{isArabic ? "التحويلات والمدفوعات (إنستاباي/فوري)" : "Transfers & Payments"}</option>
                  <option value="MOBILE_BANKING">{isArabic ? "الخدمات المصرفية عبر الهاتف" : "Mobile Banking"}</option>
                  <option value="FRAUD_DISPUTE">{isArabic ? "نزاعات الاحتيال والعمليات غير المصرح بها" : "Fraud & Unauthorized Transactions"}</option>
                  <option value="LOANS_CREDIT">{isArabic ? "القروض والتسهيلات الائتمانية" : "Loans & Credit Facilities"}</option>
                  <option value="FEES_CHARGES">{isArabic ? "الرسوم والعمولات" : "Fees & Charges"}</option>
                  <option value="ACCOUNT_SERVICES">{isArabic ? "خدمات الحسابات والشهادات" : "Account & Deposit Services"}</option>
                  <option value="GENERAL_INQUIRY">{isArabic ? "استفسارات عامة" : "General Inquiry"}</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  {isArabic ? "موضوع الشكوى" : "Subject"}
                </label>
                <input
                  type="text"
                  required
                  value={complaintForm.subject}
                  onChange={(e) => setComplaintForm({ ...complaintForm, subject: e.target.value })}
                  placeholder={isArabic ? "مثال: عدم خروج النقدية من ماكينة الصراف" : "e.g. ATM debited cash without dispensing"}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  {isArabic ? "تفاصيل الواقعة" : "Details"}
                </label>
                <textarea
                  required
                  rows={4}
                  value={complaintForm.details}
                  onChange={(e) => setComplaintForm({ ...complaintForm, details: e.target.value })}
                  placeholder={isArabic ? "اذكر مكان الواقعة والتاريخ والمبلغ التقريبي..." : "Describe what happened, branch/ATM location, amount..."}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg"
                />
              </div>

              <div className="flex justify-end space-x-2 rtl:space-x-reverse pt-2">
                <button
                  type="button"
                  onClick={() => setShowComplaintModal(false)}
                  className="px-4 py-2 border border-gray-300 text-gray-700 text-xs font-semibold rounded-lg hover:bg-gray-50"
                >
                  {isArabic ? "إلغاء" : "Cancel"}
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2 bg-nile-700 text-white text-xs font-bold rounded-lg hover:bg-nile-800 disabled:opacity-50"
                >
                  {isSubmitting ? (isArabic ? "جاري الإرسال..." : "Submitting...") : (isArabic ? "تأكيد الإرسال" : "Submit Ticket")}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Floating AI Banking Assistant Widget */}
      <RAGAssistant portalType="customer" mode="floating" />
    </>
  );
};
