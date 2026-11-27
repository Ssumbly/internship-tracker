export type Status = "saved" | "applied" | "oa" | "interview" | "offer" | "rejected";

export interface Application {
  id: number;
  owner_id: number;
  company: string;
  role: string;
  location: string | null;
  status: Status;
  deadline: string | null;
  job_url: string | null;
  notes: string | null;
  resume_version: string | null;
  created_at: string;
  updated_at: string;
}

export interface Stats {
  total: number;
  by_status: Record<Status, number>;
  upcoming_deadlines: Application[];
}

export type ApplicationInput = Omit<Application, "id" | "owner_id" | "created_at" | "updated_at">;

const BASE = import.meta.env.VITE_API_URL ?? "/api";

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...authHeaders(), ...(options.headers ?? {}) },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `Request failed (${res.status})`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export async function login(email: string, password: string): Promise<void> {
  const form = new URLSearchParams({ username: email, password });
  const res = await fetch(`${BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: form,
  });
  if (!res.ok) throw new Error("Incorrect email or password");
  const data = await res.json();
  localStorage.setItem("token", data.access_token);
}

export function register(email: string, password: string, fullName: string) {
  return request("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, full_name: fullName || null }),
  });
}

export function logout() {
  localStorage.removeItem("token");
}

export const isLoggedIn = () => !!localStorage.getItem("token");

export const fetchApplications = (status?: string) =>
  request<Application[]>(`/applications${status ? `?status=${status}` : ""}`);

export const fetchStats = () => request<Stats>("/stats");

export const createApplication = (input: ApplicationInput) =>
  request<Application>("/applications", { method: "POST", body: JSON.stringify(input) });

export const updateApplication = (id: number, input: Partial<ApplicationInput>) =>
  request<Application>(`/applications/${id}`, { method: "PUT", body: JSON.stringify(input) });

export const deleteApplication = (id: number) =>
  request<void>(`/applications/${id}`, { method: "DELETE" });
