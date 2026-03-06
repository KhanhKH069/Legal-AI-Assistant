import {
  Applicant,
  ChatRequestPayload,
  ChatResponse,
  CreateApplicantPayload,
  JobRequirement,
  RunScreeningResponse,
  ScreeningResult,
  UpdateApplicantPayload
} from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    },
    ...options
  });

  if (!res.ok) {
    let detail: string;
    try {
      const data = await res.json();
      detail = (data as any)?.detail || JSON.stringify(data);
    } catch {
      detail = await res.text();
    }
    throw new Error(detail || `Request failed: ${res.status}`);
  }

  return res.json();
}

export async function uploadCv(file: File): Promise<{ filename: string; cv_path: string }> {
  const form = new FormData();
  form.append("file", file);

  const res = await fetch(`${API_BASE}/files/upload-cv`, {
    method: "POST",
    body: form
  });

  if (!res.ok) {
    let detail: string;
    try {
      const data = await res.json();
      detail = (data as any)?.detail || JSON.stringify(data);
    } catch {
      detail = await res.text();
    }
    throw new Error(detail || `Upload failed: ${res.status}`);
  }

  return res.json();
}

export async function chat(
  payload: ChatRequestPayload
): Promise<ChatResponse> {
  return apiFetch<ChatResponse>("/chat", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function listApplicants(params?: {
  status?: string;
  position?: string;
}): Promise<Applicant[]> {
  const qs = new URLSearchParams();
  if (params?.status) qs.set("status", params.status);
  if (params?.position) qs.set("position", params.position);
  const query = qs.toString() ? `?${qs.toString()}` : "";
  return apiFetch<Applicant[]>(`/applicants${query}`);
}

export async function createApplicant(
  payload: CreateApplicantPayload
): Promise<Applicant> {
  return apiFetch<Applicant>("/applicants", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function getApplicant(id: number): Promise<Applicant> {
  return apiFetch<Applicant>(`/applicants/${id}`);
}

export async function updateApplicant(
  id: number,
  payload: UpdateApplicantPayload
): Promise<Applicant> {
  return apiFetch<Applicant>(`/applicants/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export async function runScreening(
  applicantId?: number
): Promise<RunScreeningResponse> {
  const query = applicantId ? `?applicant_id=${applicantId}` : "";
  return apiFetch<RunScreeningResponse>(`/screening/run${query}`, {
    method: "POST"
  });
}

export async function listScreeningResults(params?: {
  position?: string;
  recommendation?: string;
}): Promise<ScreeningResult[]> {
  const qs = new URLSearchParams();
  if (params?.position) qs.set("position", params.position);
  if (params?.recommendation) qs.set("recommendation", params.recommendation);
  const query = qs.toString() ? `?${qs.toString()}` : "";
  return apiFetch<ScreeningResult[]>(`/screening/results${query}`);
}

export async function getScreeningResult(
  id: number
): Promise<ScreeningResult> {
  return apiFetch<ScreeningResult>(`/screening/results/${id}`);
}

export async function listJobRequirements(): Promise<JobRequirement[]> {
  return apiFetch<JobRequirement[]>("/job-requirements");
}

export async function getJobRequirement(
  id: number
): Promise<JobRequirement> {
  return apiFetch<JobRequirement>(`/job-requirements/${id}`);
}

export async function createJobRequirement(
  payload: Omit<JobRequirement, "id" | "created_at">
): Promise<JobRequirement> {
  return apiFetch<JobRequirement>("/job-requirements", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function updateJobRequirement(
  id: number,
  payload: Partial<Omit<JobRequirement, "id" | "created_at">>
): Promise<JobRequirement> {
  return apiFetch<JobRequirement>(`/job-requirements/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

// ── Employee endpoints ──────────────────────────────────────────────────────

export interface EmployeeSummary {
  employee_id: string;
  name: string;
  department: string;
  position: string;
}

export interface EmployeeMonthly {
  employee_id: string;
  name: string;
  department: string;
  position: string;
  hire_date: string;
  status: string;
  salary_level: string;
  performance_rating: number;
  leave_balance: number;
  month: string;
  month_label: string;
  working_days_in_month: number;
  days_worked: number;
  leave_taken_this_month: number;
}

export async function listEmployees(search?: string): Promise<EmployeeSummary[]> {
  const qs = search ? `?search=${encodeURIComponent(search)}` : "";
  return apiFetch<EmployeeSummary[]>(`/employees${qs}`);
}

export async function getEmployeeMonthly(
  employeeId: string,
  month?: string
): Promise<EmployeeMonthly> {
  const qs = month ? `?month=${encodeURIComponent(month)}` : "";
  return apiFetch<EmployeeMonthly>(`/employees/${employeeId}/monthly${qs}`);
}

// ── Attendance endpoints ──────────────────────────────────────────────────────

export interface AttendanceRecord {
  employee_id: string;
  attendance: {
    name: string;
    week: string;
    daily_records: {
      date: string;
      day: string;
      check_in: string | null;
      check_out: string | null;
      total_hours: number;
      ot_hours: number;
      status: string;
    }[];
    weekly_summary: {
      total_working_days: number;
      total_hours: number;
      total_ot_hours: number;
      absent_days: number;
      leave_days: number;
    };
  };
}

export interface LeaveRequest {
  request_id: string;
  employee_id: string;
  type: string;
  start_date: string;
  end_date: string;
  days: number;
  reason: string;
  status: string;
  approved_by: string | null;
  submitted_at: string;
}

export async function getAttendance(employeeId: string): Promise<AttendanceRecord> {
  return apiFetch<AttendanceRecord>(`/attendance/${employeeId}`);
}

export async function getLeaveRequests(employeeId: string): Promise<{ employee_id: string; leave_requests: LeaveRequest[] }> {
  return apiFetch(`/attendance/${employeeId}/leave-requests`);
}

export async function submitLeaveRequest(payload: {
  employee_id: string;
  leave_type: string;
  start_date: string;
  end_date: string;
  reason: string;
}): Promise<{ status: string; request_id: string }> {
  return apiFetch(`/attendance/leave-request`, { method: "POST", body: JSON.stringify(payload) });
}

// ── Helpdesk endpoints ────────────────────────────────────────────────────────

export interface HelpdeskTicket {
  ticket_id: string;
  employee_id: string;
  category: string;
  subject: string;
  description: string;
  priority: string;
  status: string;
  assigned_to: string;
  created_at: string;
  updated_at: string;
  resolution: string | null;
  comments: { author: string; message: string; timestamp: string }[];
}

export async function listEmployeeTickets(employeeId: string): Promise<{ tickets: HelpdeskTicket[]; total: number }> {
  return apiFetch(`/helpdesk/tickets/employee/${employeeId}`);
}

export async function createTicket(payload: {
  employee_id: string;
  category: string;
  subject: string;
  description: string;
  priority: string;
}): Promise<{ status: string; ticket_id: string }> {
  return apiFetch(`/helpdesk/tickets`, { method: "POST", body: JSON.stringify(payload) });
}

export async function getHelpdeskCategories(): Promise<{ categories: string[]; priority_levels: string[] }> {
  return apiFetch(`/helpdesk/categories`);
}

// ── Benefits endpoints ────────────────────────────────────────────────────────

export interface EmployeeBenefits {
  health_insurance_package: string;
  meal_allowance: boolean;
  transportation_allowance_tier: string;
  training_budget_used: number;
  training_budget_remaining: number;
  wfh_allowance: boolean;
  annual_checkup_done: boolean;
  benefit_changes_pending: { type: string; from?: string; to?: string; status: string }[];
}

export async function getEmployeeBenefits(employeeId: string): Promise<{ employee_id: string; benefits: EmployeeBenefits }> {
  return apiFetch(`/benefits/${employeeId}`);
}

export async function getBenefitsCatalog(): Promise<{ benefits_catalog: Record<string, any> }> {
  return apiFetch(`/benefits/catalog`);
}

export async function requestBenefitChange(payload: {
  employee_id: string;
  benefit_type: string;
  requested_change: string;
}): Promise<{ status: string }> {
  return apiFetch(`/benefits/change-request`, { method: "POST", body: JSON.stringify(payload) });
}

// ── Notifications endpoints ───────────────────────────────────────────────────

export interface HRNotification {
  notification_id: string;
  recipient_id: string;
  type: string;
  title: string;
  message: string;
  channel: string;
  is_read: boolean;
  created_at: string;
}

export async function getNotifications(employeeId: string): Promise<{ notifications: HRNotification[]; unread: number }> {
  return apiFetch(`/notifications/${employeeId}`);
}

export async function getAnnouncements(): Promise<{ announcements: { announcement_id: string; title: string; content: string; department: string; published_by: string; published_at: string }[] }> {
  return apiFetch(`/notifications/announcements/all`);
}
