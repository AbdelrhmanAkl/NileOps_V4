/**
 * NileOps Frontend API Client — Connects to FastAPI Backend.
 */

const API_BASE = "/api/v1";

function getAuthHeader(): Record<string, string> {
  const token = localStorage.getItem("nileops_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// 1. Health & Status
export async function fetchHealth() {
  const res = await fetch("/health");
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

export async function fetchAllComplaints(statusFilter?: string) {
  const url = statusFilter ? `${API_BASE}/employee/complaints?status=${statusFilter}` : `${API_BASE}/employee/complaints`;
  const res = await fetch(url, { headers: { ...getAuthHeader() } });
  if (!res.ok) throw new Error("Failed to load complaints.");
  return res.json();
}

export async function updateComplaintStatus(
  complaintId: string,
  data: { status: string; staff_notes?: string; resolution_notes?: string }
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

export async function fetchAuditLogs() {
  const res = await fetch(`${API_BASE}/employee/audit-logs`, {
    headers: { ...getAuthHeader() },
  });
  if (!res.ok) throw new Error("Failed to load audit logs.");
  return res.json();
}

export async function fetchKycVerifications() {
  const res = await fetch(`${API_BASE}/employee/kyc-verifications`, {
    headers: { ...getAuthHeader() },
  });
  if (!res.ok) throw new Error("Failed to load KYC verifications.");
  return res.json();
}

export async function updateKycStatus(id: string, status: string, notes?: string) {
  const res = await fetch(`${API_BASE}/employee/kyc-verifications/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", ...getAuthHeader() },
    body: JSON.stringify({ status, reviewer_notes: notes }),
  });
  if (!res.ok) throw new Error("Failed to update KYC record.");
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
