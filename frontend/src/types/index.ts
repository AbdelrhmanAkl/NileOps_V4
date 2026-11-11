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
  customer_name?: string;
  category: string;
  category_ar: string;
  subject: string;
  details: string;
  status: "OPEN" | "IN_PROGRESS" | "RESOLVED" | "REJECTED";
  priority: "LOW" | "MEDIUM" | "HIGH" | "URGENT";
  assigned_to_id?: string;
  assigned_to_name?: string;
  assigned_team?: string;
  staff_notes?: string;
  resolution_notes?: string;
  is_test?: boolean;
  sla_due_at?: string;
  sla_breached?: boolean;
  sla_remaining_hours?: number;
  sla_status_label?: "ON_TRACK" | "APPROACHING_BREACH" | "BREACHED" | "RESOLVED_ON_TIME" | "RESOLVED_BREACHED";
  ai_suggested_category?: string;
  ai_suggested_team?: string;
  ai_suggested_priority?: string;
  ai_matched_keywords?: string;
  ai_draft_reply?: string;
  ai_draft_status?: string;
  customer_reply?: string;
  customer_reply_at?: string;
  customer_replied_by_id?: string;
  created_at: string;
  updated_at: string;
}

export interface PaginatedComplaints {
  items: Complaint[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface AdvisoryClassificationResult {
  advisory_label: string;
  suggested_category: string;
  suggested_team: string;
  suggested_priority: string;
  matched_keywords: string[];
  draft_reply: string;
  generation_source: string;
  confidence_claimed: boolean;
  confidence_note: string;
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
  status: "PENDING_REVIEW" | "APPROVED_SIMULATED" | "VERIFIED_SYNTHETIC" | "REJECTED" | "FLAGGED" | "INFO_REQUESTED";
  extracted_data_json: string;
  mismatch_reasons_json?: string;
  image_url?: string;
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

export type RequestStatus =
  | "DRAFT"
  | "SUBMITTED"
  | "UNDER_REVIEW"
  | "APPROVED_SIMULATED"
  | "REJECTED"
  | "MORE_INFO_REQUIRED"
  | "SIMULATED_COMPLETED";

export interface AccountOpeningRequest {
  id: string;
  reference_number: string;
  customer_id: string;
  customer_name?: string;
  product_id: string;
  product_name?: string;
  account_type: "current" | "savings" | "certificate";
  currency: string;
  initial_deposit: number;
  monthly_income: number;
  employment_status: string;
  branch_code: string;
  status: RequestStatus;
  idempotency_key?: string;
  submitted_by_id: string;
  submitted_at: string;
  reviewer_id?: string;
  reviewer_notes?: string;
  rejection_reason?: string;
  reviewed_at?: string;
  completed_at?: string;
  created_at: string;
  updated_at: string;
}

export interface CardRequest {
  id: string;
  reference_number: string;
  customer_id: string;
  customer_name?: string;
  linked_account_id: string;
  card_type: string;
  card_name?: string;
  embossed_name: string;
  delivery_branch: string;
  status: RequestStatus;
  idempotency_key?: string;
  submitted_by_id: string;
  submitted_at: string;
  reviewer_id?: string;
  reviewer_notes?: string;
  rejection_reason?: string;
  reviewed_at?: string;
  completed_at?: string;
  created_at: string;
  updated_at: string;
}

export interface CardProduct {
  id: string;
  name_en: string;
  name_ar: string;
  type: string;
  features_en: string[];
  features_ar: string[];
}

export interface RuleDetail {
  code: string;
  name: string;
  passed: boolean;
  message: string;
}

export interface RequestRuleEvaluation {
  eligible: boolean;
  recommendation: string;
  rules: {
    code: string;
    name: string;
    passed: boolean;
    message: string;
  }[];
}

export interface KpiMetric {
  key: string;
  title_en: string;
  title_ar: string;
  value: number;
  formatted_value: string;
  numerator?: number;
  denominator?: number;
  sample_size: number;
  definition: string;
  definition_ar: string;
  target_benchmark: string;
  status: "MET" | "NOT MET" | "NO TARGET" | "NOT MEASURED";
  date_range: string;
  breakdown?: Record<string, any>;
}

export interface KpiSummary {
  calculated_at: string;
  environment_mode: string;
  metrics: Record<string, KpiMetric>;
}
