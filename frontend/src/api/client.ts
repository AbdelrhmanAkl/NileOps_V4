/**
 * NileOps Frontend API Client — Connects to FastAPI Backend.
 */

const SERVER_URL = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");
const API_BASE = `${SERVER_URL}/api/v1`;

function getAuthHeader(): Record<string, string> {
  const token = localStorage.getItem("nileops_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// 1. Health & Status
export async function fetchHealth() {
  const res = await fetch(`${SERVER_URL}/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return res.json();
}

export async function fetchApiStatus() {
  const res = await fetch(`${API_BASE}/status`);
  if (!res.ok) throw new Error(`API status failed: ${res.status}`);
  return res.json();
}

// 2. Authentication
export async function apiLogin(email: string, password: string) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Authentication failed.");
  }
  return res.json();
}

export async function apiSeedDemo() {
  const res = await fetch(`${API_BASE}/auth/seed`, { method: "POST" });
  return res.json();
}

// 3. Customer Portal
export async function fetchCustomerAccounts() {
  const res = await fetch(`${API_BASE}/customer/accounts`, {
    headers: { ...getAuthHeader() },
  });
  if (!res.ok) throw new Error("Failed to load customer accounts.");
  return res.json();
}

export async function fetchCustomerTransactions(accountId?: string) {
  const url = accountId
    ? `${API_BASE}/customer/transactions?account_id=${accountId}`
    : `${API_BASE}/customer/transactions`;
  const res = await fetch(url, { headers: { ...getAuthHeader() } });
  if (!res.ok) throw new Error("Failed to load transactions.");
  return res.json();
}

export async function fetchCustomerComplaints() {
  const res = await fetch(`${API_BASE}/customer/complaints`, {
    headers: { ...getAuthHeader() },
  });
  if (!res.ok) throw new Error("Failed to load complaints.");
  return res.json();
}

export async function submitCustomerComplaint(data: { category: string; subject: string; details: string }) {
  const res = await fetch(`${API_BASE}/customer/complaints`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeader() },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to submit complaint.");
  }
  return res.json();
}

// 4. Employee Portal
export async function fetchEmployeeDashboard() {
  const res = await fetch(`${API_BASE}/employee/dashboard`, {
    headers: { ...getAuthHeader() },
  });
  if (!res.ok) throw new Error("Failed to load employee dashboard metrics.");
  return res.json();
}

export async function searchCustomers(query?: string) {
  const url = query ? `${API_BASE}/employee/customers?q=${encodeURIComponent(query)}` : `${API_BASE}/employee/customers`;
  const res = await fetch(url, { headers: { ...getAuthHeader() } });
  if (!res.ok) throw new Error("Failed to search customers.");
  return res.json();
}

export async function fetchAllComplaints(
  params?:
    | string
    | {
        status?: string;
        category?: string;
        priority?: string;
        team?: string;
        search?: string;
        include_test?: boolean;
        sort_by?: string;
        sort_order?: string;
        page?: number;
        page_size?: number;
      }
) {
  let url = `${API_BASE}/employee/complaints`;
  if (typeof params === "string") {
    if (params) url += `?status=${params}`;
  } else if (params) {
    const q = new URLSearchParams();
    if (params.status) q.append("status", params.status);
    if (params.category) q.append("category", params.category);
    if (params.priority) q.append("priority", params.priority);
    if (params.team) q.append("team", params.team);
    if (params.search) q.append("search", params.search);
    if (params.include_test) q.append("include_test", "true");
    if (params.sort_by) q.append("sort_by", params.sort_by);
    if (params.sort_order) q.append("sort_order", params.sort_order);
    if (params.page) q.append("page", params.page.toString());
    if (params.page_size) q.append("page_size", params.page_size.toString());
    const queryStr = q.toString();
    if (queryStr) url += `?${queryStr}`;
  }
  const res = await fetch(url, { headers: { ...getAuthHeader() } });
  if (!res.ok) throw new Error("Failed to load complaints.");
  return res.json();
}

export async function updateComplaintStatus(
  complaintId: string,
  data: {
    status?: string;
    priority?: string;
    assigned_team?: string;
    assigned_to_id?: string;
    staff_notes?: string;
    resolution_notes?: string;
    customer_reply?: string;
    ai_draft_status?: string;
  }
) {
  const res = await fetch(`${API_BASE}/employee/complaints/${complaintId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", ...getAuthHeader() },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to update complaint status.");
  }
  return res.json();
}

export async function fetchComplaintAdvisory(complaintId: string) {
  const res = await fetch(`${API_BASE}/employee/complaints/${complaintId}/advisory`, {
    method: "POST",
    headers: { ...getAuthHeader() },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to generate advisory suggestions.");
  }
  return res.json();
}

export async function fetchAuditLogs() {
  const res = await fetch(`${API_BASE}/employee/audit-logs`, {
    headers: { ...getAuthHeader() },
  });
  if (!res.ok) throw new Error("Failed to load audit logs.");
  return res.json();
}

export async function fetchKycVerifications(statusFilter?: string) {
  const url = statusFilter && statusFilter !== "ALL"
    ? `${API_BASE}/employee/kyc-verifications?status=${encodeURIComponent(statusFilter)}`
    : `${API_BASE}/employee/kyc-verifications`;
  const res = await fetch(url, {
    headers: { ...getAuthHeader() },
  });
  if (!res.ok) throw new Error("Failed to load KYC verifications.");
  return res.json();
}

export async function uploadKycDocument(file: File, customerId?: string) {
  const formData = new FormData();
  formData.append("file", file);
  if (customerId) formData.append("customer_id", customerId);

  const token = localStorage.getItem("nileops_token");
  const res = await fetch(`${API_BASE}/employee/kyc-verifications/upload`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to upload and process KYC document.");
  }
  return res.json();
}

export async function updateKycStatus(id: string, status: string, notes?: string) {
  const res = await fetch(`${API_BASE}/employee/kyc-verifications/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", ...getAuthHeader() },
    body: JSON.stringify({ status, reviewer_notes: notes }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to update KYC record.");
  }
  return res.json();
}

// 5. Policy Governance
export async function fetchPolicies(query?: string, domain?: string, statusFilter?: string) {
  const params = new URLSearchParams();
  if (query) params.append("q", query);
  if (domain) params.append("domain", domain);
  if (statusFilter) params.append("status", statusFilter);

  const res = await fetch(`${API_BASE}/policies?${params.toString()}`, {
    headers: { ...getAuthHeader() },
  });
  if (!res.ok) throw new Error("Failed to load policies.");
  return res.json();
}

export async function createPolicyDraft(data: any) {
  const res = await fetch(`${API_BASE}/policies`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeader() },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to create policy draft.");
  }
  return res.json();
}

export async function submitPolicyForApproval(policyId: string) {
  const res = await fetch(`${API_BASE}/policies/${policyId}/submit`, {
    method: "POST",
    headers: { ...getAuthHeader() },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to submit policy.");
  }
  return res.json();
}

export async function approvePolicy(policyId: string, notes?: string) {
  const res = await fetch(`${API_BASE}/policies/${policyId}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeader() },
    body: JSON.stringify({ approval_notes: notes || "Approved" }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Approval failed.");
  }
  return res.json();
}

export async function rejectPolicy(policyId: string, reason: string) {
  const res = await fetch(`${API_BASE}/policies/${policyId}/reject`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeader() },
    body: JSON.stringify({ rejection_reason: reason }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Rejection failed.");
  }
  return res.json();
}

// 6. Public
export async function fetchPublicProducts() {
  const res = await fetch(`${API_BASE}/public/products`);
  return res.json();
}

export async function fetchPublicBranches() {
  const res = await fetch(`${API_BASE}/public/branches`);
  return res.json();
}

export async function fetchPublicFaqs() {
  const res = await fetch(`${API_BASE}/public/faqs`);
  return res.json();
}

export async function fetchPublicCards() {
  const res = await fetch(`${API_BASE}/public/cards`);
  if (!res.ok) throw new Error("Failed to load card products.");
  return res.json();
}

// 7. Customer Requests (Simulated Account Opening & Cards)
export async function fetchCustomerAccountRequests() {
  const res = await fetch(`${API_BASE}/customer/account-requests`, {
    headers: { ...getAuthHeader() },
  });
  if (!res.ok) throw new Error("Failed to load account requests.");
  return res.json();
}

export async function createCustomerAccountRequest(data: {
  product_id: string;
  account_type?: string;
  currency?: string;
  initial_deposit: number;
  monthly_income: number;
  employment_status?: string;
  branch_code?: string;
  idempotency_key?: string;
}) {
  const res = await fetch(`${API_BASE}/customer/account-requests`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeader() },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to submit account opening request.");
  }
  return res.json();
}

export async function fetchCustomerCardRequests() {
  const res = await fetch(`${API_BASE}/customer/card-requests`, {
    headers: { ...getAuthHeader() },
  });
  if (!res.ok) throw new Error("Failed to load card requests.");
  return res.json();
}

export async function createCustomerCardRequest(data: {
  linked_account_id: string;
  card_type: string;
  embossed_name: string;
  delivery_branch?: string;
  idempotency_key?: string;
}) {
  const res = await fetch(`${API_BASE}/customer/card-requests`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeader() },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to submit card issuance request.");
  }
  return res.json();
}

// 8. Employee Requests Queue & Dual-Control Review
export async function fetchEmployeeAccountRequests(statusFilter?: string) {
  const url = statusFilter && statusFilter !== "ALL"
    ? `${API_BASE}/employee/account-requests?status=${encodeURIComponent(statusFilter)}`
    : `${API_BASE}/employee/account-requests`;
  const res = await fetch(url, { headers: { ...getAuthHeader() } });
  if (!res.ok) throw new Error("Failed to load account requests queue.");
  return res.json();
}

export async function evaluateAccountRequest(id: string) {
  const res = await fetch(`${API_BASE}/employee/account-requests/${id}/evaluate`, {
    headers: { ...getAuthHeader() },
  });
  if (!res.ok) throw new Error("Failed to evaluate compliance rules.");
  return res.json();
}

export async function reviewAccountRequest(id: string, action: {
  status: string;
  notes?: string;
  rejection_reason?: string;
}) {
  const res = await fetch(`${API_BASE}/employee/account-requests/${id}/review`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", ...getAuthHeader() },
    body: JSON.stringify(action),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to update account request.");
  }
  return res.json();
}

export async function fetchEmployeeCardRequests(statusFilter?: string) {
  const url = statusFilter && statusFilter !== "ALL"
    ? `${API_BASE}/employee/card-requests?status=${encodeURIComponent(statusFilter)}`
    : `${API_BASE}/employee/card-requests`;
  const res = await fetch(url, { headers: { ...getAuthHeader() } });
  if (!res.ok) throw new Error("Failed to load card requests queue.");
  return res.json();
}

export async function reviewCardRequest(id: string, action: {
  status: string;
  notes?: string;
  rejection_reason?: string;
}) {
  const res = await fetch(`${API_BASE}/employee/card-requests/${id}/review`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", ...getAuthHeader() },
    body: JSON.stringify(action),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to update card request.");
  }
  return res.json();
}

// 7. RAG Knowledge Base Assistant
export interface RAGCitation {
  code: string;
  title: string;
  domain: string;
  version: string;
  portal_access: string;
  score: number;
  passage?: string;
}

export interface RAGResponse {
  query: string;
  portal_type: "customer" | "employee";
  language: "ar" | "en";
  answer: string;
  confidence_score: number;
  abstained: boolean;
  fallback_used: boolean;
  citations: RAGCitation[];
}

export async function askBankingAssistant(params: {
  query: string;
  portal_type: "customer" | "employee";
  language: "ar" | "en";
  threshold?: number;
}): Promise<RAGResponse> {
  const res = await fetch(`${API_BASE}/rag/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeader() },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to query NileOps AI Policy Assistant.");
  }
  return res.json();
}
