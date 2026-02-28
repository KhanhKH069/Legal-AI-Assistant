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

