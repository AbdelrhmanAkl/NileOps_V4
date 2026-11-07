/**
 * NileOps Core Frontend TypeScript Definitions
 * Fictional Institution: NileOps Demo Bank
 */

export type UserRole =
  | "admin"
  | "operations_officer"
  | "customer_service"
  | "compliance_reviewer"
  | "branch_manager";

export type PortalType = "customer" | "employee";

export type SupportedLanguage = "en" | "ar";

export interface UserProfile {
  id: string;
  email: string;
  fullName: string;
  role: UserRole;
  portal: PortalType;
}

export interface HealthCheckResponse {
  status: string;
  service: string;
  version: string;
}
