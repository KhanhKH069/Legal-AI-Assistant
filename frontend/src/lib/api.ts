const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface User {
  username: string;
  role: 'admin' | 'manager' | 'employee';
  employee_id: string;
}

export interface Employee {
  employee_id: string;
  name: string;
  department: string;
  position: string;
  level: string;
  email: string;
  phone: string;
  hire_date: string;
  status: string;
  manager_id?: string;
  salary_vnd?: number;
  leave_balance?: number;
  performance_rating?: number;
  address?: string;
  education?: string;
  skills?: string[];
  contract?: { start: string; end: string };
  emergency_contact?: { name: string; phone: string; relation: string };
  manager_name?: string;
  manager_position?: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatResponse {
  status: string;
  response: string;
  intent?: string;
  agent_name?: string;
  user_id: string;
  timestamp: string;
}

function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('access_token');
}

function authHeaders(): HeadersInit {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' } : { 'Content-Type': 'application/json' };
}

export async function login(username: string, password: string): Promise<{ access_token: string; user: User } | null> {
  const form = new URLSearchParams();
  form.append('username', username);
  form.append('password', password);
  const res = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: form.toString(),
  });
  if (!res.ok) return null;
  return res.json();
}

export async function getMe(): Promise<User | null> {
  const res = await fetch(`${API_URL}/auth/me`, { headers: authHeaders() });
  if (!res.ok) return null;
  return res.json();
}

export async function getEmployees(params?: { search?: string; department?: string; page?: number; size?: number }) {
  const q = new URLSearchParams();
  if (params?.search) q.set('search', params.search);
  if (params?.department) q.set('department', params.department);
  if (params?.page) q.set('page', String(params.page));
  if (params?.size) q.set('size', String(params.size));
  const res = await fetch(`${API_URL}/employees/all-profiles?${q}`, { headers: authHeaders() });
  if (!res.ok) return null;
  return res.json();
}

export async function getEmployeeProfile(id: string): Promise<Employee | null> {
  const res = await fetch(`${API_URL}/employees/${id}/profile`, { headers: authHeaders() });
  if (!res.ok) return null;
  return res.json();
}

export async function getMonthlyInfo(id: string, month?: string) {
  const q = month ? `?month=${month}` : '';
  const res = await fetch(`${API_URL}/employees/${id}/monthly${q}`, { headers: authHeaders() });
  if (!res.ok) return null;
  return res.json();
}

export async function submitLeave(data: { type: string; start: string; end: string; reason: string }, userId: string) {
  const res = await fetch(`${API_URL}/attendance/leave?user_id=${userId}`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify(data),
  });
  if (!res.ok) return null;
  return res.json();
}

// ==========================================
// Recruitment APIs
// ==========================================
export async function getApplicants() {
  const res = await fetch(`${API_URL}/applicants/`, { headers: authHeaders() });
  if (!res.ok) return null;
  return res.json();
}

export async function getScreeningResults() {
  const res = await fetch(`${API_URL}/screening/results`, { headers: authHeaders() });
  if (!res.ok) return null;
  return res.json();
}

export async function runScreening(applicantId?: number) {
  const url = applicantId ? `${API_URL}/screening/run?applicant_id=${applicantId}` : `${API_URL}/screening/run`;
  const res = await fetch(url, {
    method: 'POST',
    headers: authHeaders()
  });
  if (!res.ok) return null;
  return res.json();
}

export async function sendChat(message: string, userId: string): Promise<ChatResponse | null> {
  const res = await fetch(`${API_URL}/chat`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({ user_id: userId, message }),
  });
  if (!res.ok) return null;
  return res.json();
}

export async function sendChatStream(message: string, userId: string, onToken: (token: string, intent: string | null) => void): Promise<ChatResponse | null> {
  const res = await fetch(`${API_URL}/chat/stream`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({ user_id: userId, message }),
  });

  if (!res.ok || !res.body) return null;

  const reader = res.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let done = false;
  let fullText = "";
  let finalIntent = "OFFLINE";

  while (!done) {
    const { value, done: readerDone } = await reader.read();
    done = readerDone;
    if (value) {
      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split('\n');
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.error) throw new Error(data.error);
            if (data.token) {
              fullText += data.token;
              onToken(data.token, data.intent);
            }
            if (data.intent) finalIntent = data.intent;
            if (data.done) done = true;
          } catch (e) {}
        }
      }
    }
  }

  return {
    status: 'success',
    response: fullText,
    intent: finalIntent,
    user_id: userId,
    timestamp: new Date().toISOString()
  };
}

export async function approveAction(userId: string, approve: boolean): Promise<ChatResponse | null> {
  const res = await fetch(`${API_URL}/chat/approve`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({ user_id: userId, approve }),
  });
  if (!res.ok) return null;
  return res.json();
}

export async function getChatHistory(userId: string) {
  const res = await fetch(`${API_URL}/chat/history/${userId}`, { headers: authHeaders() });
  if (!res.ok) return null;
  return res.json();
}

export async function clearChatHistory(userId: string) {
  const res = await fetch(`${API_URL}/chat/history/${userId}`, { method: 'DELETE', headers: authHeaders() });
  return res.ok;
}

export async function getHealth() {
  const res = await fetch(`${API_URL}/health`);
  if (!res.ok) return null;
  return res.json();
}

// ── Guest / Applicant API (no auth required) ──────────────────────────────────

export async function sendGuestChatStream(
  message: string,
  sessionId: string,
  onToken: (token: string, intent?: string) => void
): Promise<{ fullText: string }> {
  const res = await fetch(`${API_URL}/chat/guest/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId }),
  });

  if (!res.ok || !res.body) {
    throw new Error('Guest stream request failed');
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let fullText = '';
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() ?? '';
    for (const line of lines) {
      if (!line.startsWith('data: ')) continue;
      try {
        const parsed = JSON.parse(line.slice(6));
        if (parsed.done) break;
        if (parsed.token) {
          fullText += parsed.token;
          onToken(parsed.token, parsed.intent);
        }
      } catch {
        /* skip malformed lines */
      }
    }
  }

  return { fullText };
}

// ── AI Performance Metrics ────────────────────────────────────────────────────

export async function getMetrics() {
  const res = await fetch(`${API_URL}/metrics/summary`);
  if (!res.ok) return null;
  return res.json();
}

export async function uploadCV(file: File): Promise<{ filename: string; cv_path: string }> {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_URL}/files/upload-cv`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    throw new Error('Upload failed');
  }

  return res.json();
}

export async function getMyMetrics() {
  const res = await fetch(`${API_URL}/employees/me/metrics`, {
    headers: authHeaders()
  });
  if (!res.ok) return null;
  return res.json();
}

export async function uploadPolicy(file: File) {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_URL}/policies/upload`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`
    },
    body: formData,
  });

  if (!res.ok) {
    const data = await res.json().catch(() => null);
    throw new Error(data?.detail || 'Upload failed');
  }

  return res.json();
}
