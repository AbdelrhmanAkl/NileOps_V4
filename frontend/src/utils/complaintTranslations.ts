/**
 * NileOps Complaint Operational Translations (English & Arabic).
 * Maps backend identifiers to localized user-facing display names.
 * Raw codes are preserved in data models and API payloads.
 */

export const STATUS_TRANSLATIONS: Record<string, { en: string; ar: string }> = {
  OPEN: { en: "OPEN", ar: "مفتوحة" },
  IN_PROGRESS: { en: "IN_PROGRESS", ar: "قيد المعالجة" },
  RESOLVED: { en: "RESOLVED", ar: "تم الحل" },
  REJECTED: { en: "REJECTED", ar: "مرفوضة" },
};

export const PRIORITY_TRANSLATIONS: Record<string, { en: string; ar: string }> = {
  URGENT: { en: "URGENT", ar: "عاجلة" },
  HIGH: { en: "HIGH", ar: "عالية" },
  MEDIUM: { en: "MEDIUM", ar: "متوسطة" },
  LOW: { en: "LOW", ar: "منخفضة" },
};

export const SLA_STATUS_TRANSLATIONS: Record<string, { en: string; ar: string }> = {
  ON_TRACK: { en: "ON_TRACK", ar: "ضمن المهلة" },
  APPROACHING_BREACH: { en: "APPROACHING_BREACH", ar: "تقترب من المهلة" },
  BREACHED: { en: "BREACHED", ar: "تجاوزت المهلة" },
  RESOLVED_ON_TIME: { en: "RESOLVED_ON_TIME", ar: "تم الحل في الموعد" },
  RESOLVED_BREACHED: { en: "RESOLVED_BREACHED", ar: "تم الحل بعد المهلة" },
};

export const TEAM_TRANSLATIONS: Record<string, { en: string; ar: string }> = {
  CARDS_PAYMENTS: { en: "Cards & Payments Team", ar: "فريق البطاقات والمدفوعات" },
  OPERATIONS: { en: "Banking Operations Team", ar: "فريق العمليات المصرفية" },
  FRAUD_RISK: { en: "Fraud & Risk Team", ar: "فريق الاحتيال والمخاطر" },
  RETAIL_CREDIT: { en: "Retail Credit Team", ar: "فريق ائتمان الأفراد" },
  FINANCE_OPERATIONS: { en: "Finance Operations Team", ar: "فريق العمليات المالية" },
  BRANCH_SUPPORT: { en: "Branch Support Team", ar: "فريق دعم الفروع" },
  BRANCH_NETWORK: { en: "Branch Network Team", ar: "فريق شبكة الفروع" },
  CUSTOMER_SERVICE: { en: "Customer Service Team", ar: "فريق خدمة العملاء" },
  COMPLIANCE: { en: "Compliance Team", ar: "فريق الامتثال والرقابة" },
};

export const CATEGORY_TRANSLATIONS: Record<string, { en: string; ar: string }> = {
  ATM_CARD: { en: "ATM & Debit Cards", ar: "بطاقات الصراف الآلي" },
  MOBILE_BANKING: { en: "Mobile & Digital Banking", ar: "الخدمات المصرفية عبر الهاتف" },
  FRAUD_DISPUTE: { en: "Fraud & Disputes", ar: "نزاعات الاحتيال" },
  LOANS_CREDIT: { en: "Loans & Credit", ar: "القروض والتمويل" },
  FEES_CHARGES: { en: "Fees & Charges", ar: "الرسوم والعمولات" },
  ACCOUNT_SERVICES: { en: "Account Services", ar: "خدمات الحسابات" },
  TRANSFER: { en: "Transfers & InstaPay", ar: "التحويلات والمدفوعات" },
  GENERAL_INQUIRY: { en: "General Inquiries", ar: "استفسارات عامة" },
};

export const getStatusLabel = (status: string, isArabic: boolean): string =>
  isArabic ? STATUS_TRANSLATIONS[status]?.ar || status : STATUS_TRANSLATIONS[status]?.en || status;

export const getPriorityLabel = (priority: string, isArabic: boolean): string =>
  isArabic ? PRIORITY_TRANSLATIONS[priority]?.ar || priority : PRIORITY_TRANSLATIONS[priority]?.en || priority;

export const getSlaLabel = (sla: string, isArabic: boolean): string =>
  isArabic ? SLA_STATUS_TRANSLATIONS[sla]?.ar || sla : SLA_STATUS_TRANSLATIONS[sla]?.en || sla;

export const getTeamLabel = (team: string, isArabic: boolean): string =>
  isArabic ? TEAM_TRANSLATIONS[team]?.ar || team : TEAM_TRANSLATIONS[team]?.en || team;

export const getCategoryLabel = (category: string, isArabic: boolean): string =>
  isArabic ? CATEGORY_TRANSLATIONS[category]?.ar || category : CATEGORY_TRANSLATIONS[category]?.en || category;

