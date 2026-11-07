/**
 * NileOps Core Frontend TypeScript Definitions
 * Fictional Institution: NileOps Demo Bank
 */

export type UserRole =
  | "admin"
  | "operations_officer"
  | "customer_service"
  | "compliance_reviewer"
  | "branch_manager"
  | "customer";

export type PortalType = "customer" | "employee";

export type SupportedLanguage = "en" | "ar";

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  user_type: "employee" | "customer";
  is_active: boolean;
  phone_number?: string;
}

export interface BankAccount {
  id: string;
  account_number: string;
  account_type: "current" | "savings" | "certificate";
  currency: string;
  balance: number;
  interest_rate: number;
  status: string;
  created_at: string;
}

export interface Transaction {
  id: string;
  reference_number: string;
  transaction_type: string;
  amount: number;
  currency: string;
  description: string;
  description_ar: string;
  counterparty?: string;
  status: string;
  timestamp: string;
}

export interface Complaint {
  id: string;
  ticket_number: string;
  customer_id: string;
  category: string;
  category_ar: string;
  subject: string;
  details: string;
  status: "OPEN" | "IN_PROGRESS" | "RESOLVED" | "REJECTED";
  priority: string;
  staff_notes?: string;
  resolution_notes?: string;
  created_at: string;
  updated_at: string;
}

export interface PolicyDocument {
  id: string;
  code: string;
  title_en: string;
  title_ar: string;
  domain: string;
  content_en: string;
  content_ar: string;
  version: string;
  status: "DRAFT" | "PENDING_APPROVAL" | "APPROVED" | "INDEXED" | "REJECTED";
  created_by_id: string;
  approved_by_id?: string;
  approved_at?: string;
  approval_notes?: string;
  rejected_by_id?: string;
  rejected_at?: string;
  rejection_reason?: string;
  created_at: string;
  updated_at: string;
}

export interface KycVerification {
  id: string;
  tracking_number: string;
  customer_id: string;
  synthetic_national_id: string;
  document_type: string;
  status: "PENDING_REVIEW" | "VERIFIED_SYNTHETIC" | "REJECTED" | "FLAGGED";
  extracted_data_json: string;
  reviewer_id?: string;
  reviewer_notes?: string;
  created_at: string;
  updated_at: string;
}

export interface AuditLog {
  id: string;
  user_id?: string;
  user_email?: string;
  user_role?: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  details_json: string;
  ip_address?: string;
  timestamp: string;
}

export interface ProductInfo {
  id: string;
  category: string;
  name_en: string;
  name_ar: string;
  description_en: string;
  description_ar: string;
  interest_rate: number;
  min_balance: number;
  term_months?: number;
  features_en: string[];
  features_ar: string[];
}
