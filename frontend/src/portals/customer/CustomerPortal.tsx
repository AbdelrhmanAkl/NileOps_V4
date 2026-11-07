import React, { useState, useEffect } from "react";
import { useLanguage } from "../../contexts/LanguageContext";
import { useAuth } from "../../contexts/AuthContext";
import {
  fetchCustomerAccounts,
  fetchCustomerTransactions,
  fetchCustomerComplaints,
  submitCustomerComplaint,
  fetchPublicProducts,
} from "../../api/client";
import { BankAccount, Transaction, Complaint, ProductInfo } from "../../types";

export const CustomerPortal: React.FC = () => {
  const { isArabic } = useLanguage();
  const { user } = useAuth();

  const [accounts, setAccounts] = useState<BankAccount[]>([]);
  const [selectedAccountId, setSelectedAccountId] = useState<string>("");
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [products, setProducts] = useState<ProductInfo[]>([]);

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [showComplaintModal, setShowComplaintModal] = useState<boolean>(false);
  const [complaintForm, setComplaintForm] = useState({
    category: "ATM_CARD",
    subject: "",
    details: "",
  });
  const [formSuccess, setFormSuccess] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  // Interest Calculator State
  const [calcAmount, setCalcAmount] = useState<number>(100000);
  const [calcRate, setCalcRate] = useState<number>(23.5);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [accs, cmps, prods] = await Promise.all([
        fetchCustomerAccounts(),
        fetchCustomerComplaints(),
        fetchPublicProducts(),
      ]);
      setAccounts(accs);
      setComplaints(cmps);
      setProducts(prods);

      if (accs.length > 0) {
        setSelectedAccountId(accs[0].id);
        const txs = await fetchCustomerTransactions(accs[0].id);
        setTransactions(txs);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

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

  const formatCurrency = (val: number, cur: string = "EGP") => {
    return `${val.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${
      isArabic ? "ج.م" : cur
    }`;
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
                  <span>{acc.account_number.slice(0, 10)}...{acc.account_number.slice(-4)}</span>
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
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {complaints.map((c) => (
              <div key={c.id} className="p-4 rounded-lg border border-gray-200 bg-gray-50/50 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-nile-800">{c.ticket_number}</span>
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
                </div>
                <div className="text-xs font-bold text-gray-900">{c.subject}</div>
                <p className="text-xs text-gray-600 leading-relaxed">{c.details}</p>
                {c.staff_notes && (
                  <div className="text-xs bg-white p-2.5 rounded border border-gray-200 text-gray-700 mt-2">
                    <strong className="text-nile-800 block text-[11px] mb-0.5">
                      {isArabic ? "إفادة موظف خدمة العملاء:" : "Support Team Note:"}
                    </strong>
                    {c.staff_notes}
                  </div>
                )}
                {c.resolution_notes && (
                  <div className="text-xs bg-green-50 p-2.5 rounded border border-green-200 text-green-900 mt-2">
                    <strong className="block text-[11px] mb-0.5">
                      {isArabic ? "قرار الإغلاق والحل النهائي:" : "Final Resolution:"}
                    </strong>
                    {c.resolution_notes}
                  </div>
                )}
              </div>
            ))}
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

      {/* Complaint Submission Modal */}
      {showComplaintModal && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl relative">
            <button
              onClick={() => setShowComplaintModal(false)}
              className="absolute top-4 right-4 rtl:left-4 rtl:right-auto text-gray-400 hover:text-gray-700"
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
                  <option value="ATM_CARD">{isArabic ? "بطاقات وصراف آلي" : "ATM & Debit Cards"}</option>
                  <option value="TRANSFER">{isArabic ? "تحويلات ومدفوعات (إنستاباي/فوري)" : "Transfers & Payments"}</option>
                  <option value="ACCOUNT_FEES">{isArabic ? "رسوم ومصاريف" : "Account Fees"}</option>
                  <option value="MOBILE_BANKING">{isArabic ? "الخدمات المصرفية عبر الهاتف" : "Mobile Banking"}</option>
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
    </div>
  );
};
