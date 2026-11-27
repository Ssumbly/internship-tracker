import { FormEvent, useCallback, useEffect, useState } from "react";
import {
  Application,
  ApplicationInput,
  Stats,
  Status,
  createApplication,
  deleteApplication,
  fetchApplications,
  fetchStats,
  isLoggedIn,
  login,
  logout,
  register,
  updateApplication,
} from "./api";

const STATUSES: Status[] = ["saved", "applied", "oa", "interview", "offer", "rejected"];
const STATUS_LABELS: Record<Status, string> = {
  saved: "Saved",
  applied: "Applied",
  oa: "Online Assessment",
  interview: "Interview",
  offer: "Offer",
  rejected: "Rejected",
};

const emptyForm: ApplicationInput = {
  company: "",
  role: "",
  location: "",
  status: "saved",
  deadline: "",
  job_url: "",
  notes: "",
  resume_version: "",
};

function toInput(a: Application): ApplicationInput {
  return {
    company: a.company,
    role: a.role,
    location: a.location ?? "",
    status: a.status,
    deadline: a.deadline ?? "",
    job_url: a.job_url ?? "",
    notes: a.notes ?? "",
    resume_version: a.resume_version ?? "",
  };
}

function normalize(input: ApplicationInput): ApplicationInput {
  return {
    ...input,
    location: input.location || null,
    deadline: input.deadline || null,
    job_url: input.job_url || null,
    notes: input.notes || null,
    resume_version: input.resume_version || null,
  } as ApplicationInput;
}

export default function App() {
  const [authed, setAuthed] = useState(isLoggedIn());
  return authed ? <Dashboard onLogout={() => { logout(); setAuthed(false); }} /> : <AuthPage onAuth={() => setAuthed(true)} />;
}

function AuthPage({ onAuth }: { onAuth: () => void }) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState("");

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError("");
    try {
      if (mode === "register") {
        await register(email, password, fullName);
      }
      await login(email, password);
      onAuth();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    }
  }

  return (
    <div className="auth-wrap">
      <form className="card auth-card" onSubmit={submit}>
        <h1>Internship Tracker</h1>
        <p className="muted">Track applications, deadlines, and resume versions in one place.</p>
        {mode === "register" && (
          <label>
            Full name
            <input value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder="Your name" />
          </label>
        )}
        <label>
          Email
          <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@university.edu" />
        </label>
        <label>
          Password
          <input type="password" required minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} placeholder="At least 8 characters" />
        </label>
        {error && <p className="error">{error}</p>}
        <button type="submit">{mode === "login" ? "Log in" : "Create account"}</button>
        <button type="button" className="link" onClick={() => setMode(mode === "login" ? "register" : "login")}>
          {mode === "login" ? "No account? Register" : "Already have an account? Log in"}
        </button>
      </form>
    </div>
  );
}

function Dashboard({ onLogout }: { onLogout: () => void }) {
  const [apps, setApps] = useState<Application[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [filter, setFilter] = useState<string>("");
  const [form, setForm] = useState<ApplicationInput>(emptyForm);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      const [a, s] = await Promise.all([fetchApplications(filter || undefined), fetchStats()]);
      setApps(a);
      setStats(s);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data");
    }
  }, [filter]);

  useEffect(() => {
    load();
  }, [load]);

  async function submit(e: FormEvent) {
    e.preventDefault();
    try {
      if (editingId !== null) {
        await updateApplication(editingId, normalize(form));
      } else {
        await createApplication(normalize(form));
      }
      setForm(emptyForm);
      setEditingId(null);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save");
    }
  }

  async function remove(id: number) {
    if (!confirm("Delete this application?")) return;
    await deleteApplication(id);
    load();
  }

  return (
    <div className="layout">
      <header>
        <h1>Internship Tracker</h1>
        <button className="secondary" onClick={onLogout}>Log out</button>
      </header>

      {error && <p className="error">{error}</p>}

      {stats && (
        <section className="stats-grid">
          <div className="card stat"><span className="stat-num">{stats.total}</span><span>Total</span></div>
          {STATUSES.map((s) => (
            <div className="card stat" key={s}>
              <span className="stat-num">{stats.by_status[s] ?? 0}</span>
              <span>{STATUS_LABELS[s]}</span>
            </div>
          ))}
        </section>
      )}

      {stats && stats.upcoming_deadlines.length > 0 && (
        <section className="card">
          <h2>Upcoming deadlines (next 30 days)</h2>
          <ul className="deadlines">
            {stats.upcoming_deadlines.map((a) => (
              <li key={a.id}>
                <strong>{a.company}</strong> — {a.role}
                <span className="muted"> due {a.deadline}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="card">
        <h2>{editingId !== null ? "Edit application" : "Add application"}</h2>
        <form className="app-form" onSubmit={submit}>
          <input required placeholder="Company *" value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} />
          <input required placeholder="Role *" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })} />
          <input placeholder="Location" value={form.location ?? ""} onChange={(e) => setForm({ ...form, location: e.target.value })} />
          <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value as Status })}>
            {STATUSES.map((s) => (
              <option key={s} value={s}>{STATUS_LABELS[s]}</option>
            ))}
          </select>
          <input type="date" value={form.deadline ?? ""} onChange={(e) => setForm({ ...form, deadline: e.target.value })} />
          <input placeholder="Job posting URL" value={form.job_url ?? ""} onChange={(e) => setForm({ ...form, job_url: e.target.value })} />
          <input placeholder="Resume version (e.g. lucid-v1)" value={form.resume_version ?? ""} onChange={(e) => setForm({ ...form, resume_version: e.target.value })} />
          <input placeholder="Notes" value={form.notes ?? ""} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
          <button type="submit">{editingId !== null ? "Save changes" : "Add"}</button>
          {editingId !== null && (
            <button type="button" className="secondary" onClick={() => { setEditingId(null); setForm(emptyForm); }}>
              Cancel
            </button>
          )}
        </form>
      </section>

      <section className="card">
        <div className="list-head">
          <h2>Applications</h2>
          <select value={filter} onChange={(e) => setFilter(e.target.value)}>
            <option value="">All statuses</option>
            {STATUSES.map((s) => (
              <option key={s} value={s}>{STATUS_LABELS[s]}</option>
            ))}
          </select>
        </div>
        {apps.length === 0 ? (
          <p className="muted">No applications yet. Add your first one above.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Company</th><th>Role</th><th>Status</th><th>Deadline</th><th>Resume</th><th></th>
              </tr>
            </thead>
            <tbody>
              {apps.map((a) => (
                <tr key={a.id}>
                  <td>
                    {a.job_url ? <a href={a.job_url} target="_blank" rel="noreferrer">{a.company}</a> : a.company}
                    {a.location && <div className="muted">{a.location}</div>}
                  </td>
                  <td>{a.role}</td>
                  <td><span className={`badge badge-${a.status}`}>{STATUS_LABELS[a.status]}</span></td>
                  <td>{a.deadline ?? "—"}</td>
                  <td>{a.resume_version ?? "—"}</td>
                  <td className="row-actions">
                    <button className="secondary" onClick={() => { setEditingId(a.id); setForm(toInput(a)); }}>Edit</button>
                    <button className="danger" onClick={() => remove(a.id)}>Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
