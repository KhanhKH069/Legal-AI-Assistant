"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import "../globals.css";
import { chat, listEmployees, getEmployeeMonthly } from "../../lib/api";
import type { EmployeeSummary, EmployeeMonthly } from "../../lib/api";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type Message = { role: "user" | "assistant"; content: string };

// ─── Utilities ────────────────────────────────────────────────────────────────

function Avatar({ name }: { name: string }) {
  const initials = name.split(" ").slice(-2).map(w => w[0]).join("").toUpperCase();
  const hue = name.charCodeAt(0) * 17 % 360;
  return (
    <div style={{
      width: 42, height: 42, borderRadius: "50%",
      background: `linear-gradient(135deg, hsl(${hue},65%,55%), hsl(${hue + 40},65%,45%))`,
      display: "flex", alignItems: "center", justifyContent: "center",
      color: "#fff", fontWeight: 700, fontSize: 15, flexShrink: 0,
      boxShadow: `0 4px 12px hsla(${hue},60%,40%,0.35)`,
    }}>{initials}</div>
  );
}

function StatCard({ icon, label, value, accent }: { icon: string; label: string; value: string; accent?: string }) {
  return (
    <div style={{
      background: "rgba(255,255,255,0.05)", borderRadius: 14,
      border: "1px solid rgba(255,255,255,0.1)",
      padding: "14px 16px", display: "flex", flexDirection: "column", gap: 4,
      transition: "background 0.2s",
    }}
      onMouseEnter={e => (e.currentTarget.style.background = "rgba(255,255,255,0.09)")}
      onMouseLeave={e => (e.currentTarget.style.background = "rgba(255,255,255,0.05)")}
    >
      <div style={{ fontSize: 20 }}>{icon}</div>
      <div style={{ fontWeight: 700, fontSize: 18, color: accent ?? "#fff", marginTop: 2 }}>{value}</div>
      <div style={{ fontSize: 12, color: "rgba(255,255,255,0.5)", letterSpacing: "0.3px" }}>{label}</div>
    </div>
  );
}

const LEVEL_COLORS: Record<string, string> = {
  L1: "#94a3b8", L2: "#60a5fa", L3: "#34d399", L4: "#f59e0b", L5: "#a78bfa",
};

function LevelPill({ level }: { level: string }) {
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 5,
      padding: "3px 12px", borderRadius: 20,
      background: `${LEVEL_COLORS[level] ?? "#94a3b8"}25`,
      border: `1px solid ${LEVEL_COLORS[level] ?? "#94a3b8"}60`,
      color: LEVEL_COLORS[level] ?? "#94a3b8",
      fontWeight: 700, fontSize: 12,
    }}>
      <span style={{ width: 6, height: 6, borderRadius: "50%", background: LEVEL_COLORS[level] ?? "#94a3b8", display: "inline-block" }} />
      {level}
    </span>
  );
}

function Stars({ value }: { value: number }) {
  return (
    <div style={{ display: "flex", gap: 3 }}>
      {Array.from({ length: 5 }, (_, i) => (
        <svg key={i} width="14" height="14" viewBox="0 0 24 24"
          fill={i < Math.round(value) ? "#f59e0b" : "none"}
          stroke={i < Math.round(value) ? "#f59e0b" : "rgba(255,255,255,0.2)"}
          strokeWidth="2">
          <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
        </svg>
      ))}
    </div>
  );
}

// ─── Employee Panel ───────────────────────────────────────────────────────────

function EmployeePanel() {
  const [search, setSearch] = useState("");
  const [results, setResults] = useState<EmployeeSummary[]>([]);
  const [searching, setSearching] = useState(false);
  const [selected, setSelected] = useState<EmployeeSummary | null>(null);
  const [monthly, setMonthly] = useState<EmployeeMonthly | null>(null);
  const [loadingMonthly, setLoadingMonthly] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [month, setMonth] = useState(() => {
    const n = new Date();
    return `${n.getFullYear()}-${String(n.getMonth() + 1).padStart(2, "0")}`;
  });

  const doSearch = useCallback(async () => {
    if (!search.trim()) return;
    setSearching(true); setError(null); setResults([]);
    try {
      const data = await listEmployees(search.trim());
      setResults(data);
      if (!data.length) setError("Không tìm thấy nhân viên.");
    } catch {
      setError("Không thể kết nối API (port 8000).");
    } finally { setSearching(false); }
  }, [search]);

  const doSelect = useCallback(async (emp: EmployeeSummary) => {
    setSelected(emp); setResults([]); setMonthly(null);
    setLoadingMonthly(true); setError(null);
    try {
      setMonthly(await getEmployeeMonthly(emp.employee_id, month));
    } catch { setError("Không lấy được dữ liệu."); }
    finally { setLoadingMonthly(false); }
  }, [month]);

  const doMonthChange = useCallback(async (m: string) => {
    setMonth(m);
    if (!selected) return;
    setLoadingMonthly(true); setError(null);
    try { setMonthly(await getEmployeeMonthly(selected.employee_id, m)); }
    catch { setError("Không lấy được dữ liệu tháng này."); }
    finally { setLoadingMonthly(false); }
  }, [selected]);

  return (
    <div style={{
      width: 360, flexShrink: 0, background: "#0f172a",
      display: "flex", flexDirection: "column", height: "100%",
      borderLeft: "1px solid rgba(255,255,255,0.07)", overflow: "hidden"
    }}>

      {/* Panel header */}
      <div style={{
        padding: "22px 22px 18px",
        borderBottom: "1px solid rgba(255,255,255,0.08)", flexShrink: 0
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 18 }}>
          <div style={{
            width: 40, height: 40, borderRadius: 12,
            background: "linear-gradient(135deg,#6366f1,#8b5cf6)",
            display: "flex", alignItems: "center", justifyContent: "center",
            boxShadow: "0 4px 16px rgba(99,102,241,0.4)"
          }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" />
              <path d="M23 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" />
            </svg>
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: 15, color: "#f1f5f9" }}>Thông Tin Nhân Viên</div>
            <div style={{ fontSize: 12, color: "rgba(255,255,255,0.4)", marginTop: 1 }}>
              Tháng làm việc · {new Date(month + "-01").toLocaleString("vi-VN", { month: "long", year: "numeric" })}
            </div>
          </div>
        </div>

        {/* Month picker */}
        <div style={{ marginBottom: 12 }}>
          <label style={{ fontSize: 11, fontWeight: 600, color: "rgba(255,255,255,0.35)", letterSpacing: "0.8px", textTransform: "uppercase", display: "block", marginBottom: 6 }}>
            Chọn tháng
          </label>
          <input
            type="month"
            value={month}
            onChange={e => doMonthChange(e.target.value)}
            style={{
              width: "100%", padding: "9px 13px", borderRadius: 10, fontSize: 14,
              border: "1px solid rgba(255,255,255,0.12)", outline: "none",
              background: "rgba(255,255,255,0.07)", color: "#f1f5f9",
              colorScheme: "dark",
            }}
          />
        </div>

        {/* Search box */}
        <label style={{ fontSize: 11, fontWeight: 600, color: "rgba(255,255,255,0.35)", letterSpacing: "0.8px", textTransform: "uppercase", display: "block", marginBottom: 6 }}>
          Tìm nhân viên
        </label>
        <div style={{ display: "flex", gap: 8 }}>
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            onKeyDown={e => e.key === "Enter" && doSearch()}
            placeholder="Nhập tên..."
            style={{
              flex: 1, padding: "9px 14px", borderRadius: 10, fontSize: 14,
              border: "1px solid rgba(255,255,255,0.12)", outline: "none",
              background: "rgba(255,255,255,0.07)", color: "#f1f5f9",
            }}
          />
          <button
            onClick={doSearch}
            disabled={searching}
            style={{
              padding: "9px 18px", borderRadius: 10,
              background: "linear-gradient(135deg,#6366f1,#8b5cf6)",
              color: "#fff", fontWeight: 700, fontSize: 14, border: "none",
              cursor: searching ? "wait" : "pointer",
              boxShadow: "0 4px 12px rgba(99,102,241,0.4)",
              transition: "opacity 0.2s",
            }}
          >
            {searching ? "…" : "Tìm"}
          </button>
        </div>

        {/* Dropdown results */}
        {results.length > 0 && (
          <div style={{
            marginTop: 8, background: "#1e293b",
            border: "1px solid rgba(255,255,255,0.1)",
            borderRadius: 12, overflow: "hidden",
            boxShadow: "0 8px 24px rgba(0,0,0,0.4)"
          }}>
            {results.map(emp => (
              <div
                key={emp.employee_id}
                onClick={() => doSelect(emp)}
                style={{
                  padding: "11px 15px", cursor: "pointer",
                  borderBottom: "1px solid rgba(255,255,255,0.06)",
                  display: "flex", alignItems: "center", gap: 12,
                  transition: "background 0.15s",
                }}
                onMouseEnter={e => (e.currentTarget.style.background = "rgba(99,102,241,0.15)")}
                onMouseLeave={e => (e.currentTarget.style.background = "")}
              >
                <Avatar name={emp.name} />
                <div>
                  <div style={{ fontWeight: 600, fontSize: 14, color: "#f1f5f9" }}>{emp.name}</div>
                  <div style={{ fontSize: 12, color: "rgba(255,255,255,0.4)" }}>{emp.position} · {emp.department}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Scrollable content */}
      <div style={{ flex: 1, overflowY: "auto", padding: "18px 22px" }}>
        {error && (
          <div style={{
            background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)",
            borderRadius: 10, padding: "10px 14px", fontSize: 13, color: "#fca5a5", marginBottom: 14
          }}>
            ⚠ {error}
          </div>
        )}

        {!selected && !error && (
          <div style={{ textAlign: "center", paddingTop: 48, color: "rgba(255,255,255,0.2)" }}>
            <svg width="52" height="52" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" style={{ margin: "0 auto 16px", display: "block" }}>
              <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            <p style={{ fontSize: 14, lineHeight: 1.7, maxWidth: 240, margin: "0 auto" }}>
              Nhập tên nhân viên để xem thông tin tháng làm việc.
            </p>
          </div>
        )}

        {selected && (
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>

            {/* Identity hero */}
            <div style={{
              background: "linear-gradient(135deg,rgba(99,102,241,0.25),rgba(139,92,246,0.15))",
              border: "1px solid rgba(99,102,241,0.3)",
              borderRadius: 16, padding: "18px 18px 16px",
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 14 }}>
                <Avatar name={selected.name} />
                <div>
                  <div style={{ fontWeight: 700, fontSize: 16, color: "#f1f5f9" }}>{selected.name}</div>
                  <div style={{ fontSize: 13, color: "rgba(255,255,255,0.55)", marginTop: 2 }}>{selected.position}</div>
                  <div style={{ fontSize: 12, color: "rgba(255,255,255,0.35)", marginTop: 1 }}>{selected.department} · {selected.employee_id}</div>
                </div>
              </div>
              {monthly && (
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                  <span style={{
                    padding: "3px 12px", borderRadius: 20, fontSize: 12, fontWeight: 600,
                    background: monthly.status === "Active" ? "rgba(52,211,153,0.15)" : "rgba(239,68,68,0.15)",
                    color: monthly.status === "Active" ? "#6ee7b7" : "#fca5a5",
                    border: `1px solid ${monthly.status === "Active" ? "rgba(52,211,153,0.3)" : "rgba(239,68,68,0.3)"}`,
                  }}>
                    {monthly.status === "Active" ? "✓ Đang làm việc" : "✗ Đã nghỉ"}
                  </span>
                  <LevelPill level={monthly.salary_level} />
                </div>
              )}
            </div>

            {loadingMonthly ? (
              <div style={{ textAlign: "center", padding: "32px 0", color: "rgba(255,255,255,0.3)", fontSize: 14 }}>
                <div style={{ marginBottom: 8, fontSize: 24 }}>⏳</div>
                Đang tải dữ liệu tháng...
              </div>
            ) : monthly ? (
              <>
                {/* Month heading */}
                <div style={{
                  fontSize: 12, fontWeight: 700, color: "rgba(255,255,255,0.35)",
                  letterSpacing: "0.8px", textTransform: "uppercase",
                  display: "flex", alignItems: "center", gap: 8
                }}>
                  <span style={{ flex: 1, height: 1, background: "rgba(255,255,255,0.08)", display: "block" }} />
                  {monthly.month_label}
                  <span style={{ flex: 1, height: 1, background: "rgba(255,255,255,0.08)", display: "block" }} />
                </div>

                {/* 2×2 stat grid */}
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                  <StatCard icon="🗓️" label="Ngày làm việc" value={`${monthly.working_days_in_month} ngày`} />
                  <StatCard icon="✅" label="Đã làm" value={`${monthly.days_worked} ngày`} accent="#6ee7b7" />
                  <StatCard icon="🏖️" label="Nghỉ tháng này" value={`${monthly.leave_taken_this_month} ngày`} />
                  <StatCard icon="📋" label="Phép còn lại" value={`${monthly.leave_balance} ngày`} accent="#93c5fd" />
                </div>

                {/* Performance */}
                <div style={{
                  background: "rgba(255,255,255,0.04)", borderRadius: 14,
                  border: "1px solid rgba(255,255,255,0.08)", padding: "16px 18px"
                }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: "rgba(255,255,255,0.35)", letterSpacing: "0.8px", textTransform: "uppercase", marginBottom: 12 }}>
                    Hiệu suất
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                    <Stars value={monthly.performance_rating} />
                    <span style={{ fontWeight: 700, fontSize: 20, color: "#f59e0b" }}>
                      {monthly.performance_rating}<span style={{ fontSize: 13, color: "rgba(255,255,255,0.3)", fontWeight: 400 }}>/5.0</span>
                    </span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ fontSize: 13, color: "rgba(255,255,255,0.4)" }}>Salary Level</span>
                    <LevelPill level={monthly.salary_level} />
                  </div>
                </div>

                {/* Hire date */}
                <div style={{
                  background: "rgba(255,255,255,0.03)", borderRadius: 12,
                  border: "1px solid rgba(255,255,255,0.07)",
                  padding: "12px 16px", display: "flex", justifyContent: "space-between",
                  fontSize: 13
                }}>
                  <span style={{ color: "rgba(255,255,255,0.4)" }}>📅 Ngày vào làm</span>
                  <span style={{ fontWeight: 600, color: "#f1f5f9" }}>{monthly.hire_date}</span>
                </div>
              </>
            ) : null}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

const QUICK_PROMPTS = [
  "Chính sách nghỉ phép là gì?",
  "Quy trình onboarding gồm những bước nào?",
  "Các loại bảo hiểm cho nhân viên?",
  "Chế độ tăng ca được tính thế nào?",
];

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = useCallback(async (text: string) => {
    const content = text.trim();
    if (!content || loading) return;
    setInput("");
    setMessages(p => [...p, { role: "user", content }]);
    setLoading(true);
    try {
      let resp = "⚠️ Không kết nối được backend. Hãy đảm bảo FastAPI đang chạy ở port 8000.";
      try {
        const r = await chat({ user_id: "employee", message: content });
        if (r?.response) resp = r.response;
      } catch { /* keep fallback */ }
      setMessages(p => [...p, { role: "assistant", content: resp }]);
    } finally { setLoading(false); }
  }, [loading]);

  return (
    <div style={{
      height: "100vh", display: "flex", flexDirection: "column",
      fontFamily: "'Inter','Segoe UI',sans-serif",
      background: "#0f172a", overflow: "hidden"
    }}>

      {/* ── Top Nav ── */}
      <div style={{
        height: 58, background: "#0f172a",
        borderBottom: "1px solid rgba(255,255,255,0.08)",
        display: "flex", alignItems: "center",
        padding: "0 24px", justifyContent: "space-between", flexShrink: 0,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <div style={{
            width: 34, height: 34, borderRadius: 10,
            background: "linear-gradient(135deg,#2563eb,#3b82f6)",
            display: "flex", alignItems: "center", justifyContent: "center",
            boxShadow: "0 4px 12px rgba(37,99,235,0.4)"
          }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
          </div>
          <div style={{ display: "flex", alignItems: "baseline", gap: 5 }}>
            <span style={{ fontWeight: 800, fontSize: 16, color: "#f1f5f9", letterSpacing: "-0.3px" }}>Paraline</span>
            <span style={{ fontWeight: 400, fontSize: 16, color: "rgba(255,255,255,0.35)" }}>HR Assistant</span>
          </div>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <a href="/" style={{
            fontSize: 13, color: "rgba(255,255,255,0.5)", textDecoration: "none",
            padding: "6px 14px", borderRadius: 8, border: "1px solid rgba(255,255,255,0.1)",
            transition: "all 0.2s",
          }}
            onMouseEnter={e => { e.currentTarget.style.color = "#f1f5f9"; e.currentTarget.style.borderColor = "rgba(255,255,255,0.25)"; }}
            onMouseLeave={e => { e.currentTarget.style.color = "rgba(255,255,255,0.5)"; e.currentTarget.style.borderColor = "rgba(255,255,255,0.1)"; }}
          >
            Trang chủ
          </a>
          <a href="/apply" style={{
            fontSize: 13, color: "#fff", textDecoration: "none",
            padding: "6px 16px", borderRadius: 8,
            background: "linear-gradient(135deg,#2563eb,#3b82f6)",
            fontWeight: 600,
            boxShadow: "0 4px 12px rgba(37,99,235,0.35)",
          }}>
            Ứng tuyển
          </a>
        </div>
      </div>

      {/* ── Body ── */}
      <div style={{ flex: 1, display: "flex", overflow: "hidden" }}>

        {/* LEFT — HR Chatbot */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", background: "#0f172a" }}>

          {/* Chat header strip */}
          <div style={{
            padding: "14px 26px", borderBottom: "1px solid rgba(255,255,255,0.06)",
            background: "rgba(255,255,255,0.02)", flexShrink: 0,
            display: "flex", alignItems: "center", gap: 10
          }}>
            <div style={{
              width: 8, height: 8, borderRadius: "50%",
              background: "#34d399", boxShadow: "0 0 8px #34d399"
            }} />
            <span style={{ fontWeight: 600, fontSize: 14, color: "#f1f5f9" }}>HR Policy Assistant</span>
            <span style={{ fontSize: 13, color: "rgba(255,255,255,0.3)", marginLeft: 4 }}>
              Hỏi về chính sách · onboarding · benefits
            </span>
          </div>

          {/* Messages */}
          <div style={{
            flex: 1, overflowY: "auto", padding: "28px 28px 8px",
            display: "flex", flexDirection: "column", gap: 18
          }}>
            {messages.length === 0 && (
              <div style={{ margin: "auto 0", paddingBottom: 32 }}>
                <div style={{ fontSize: 28, marginBottom: 10, textAlign: "center" }}>👋</div>
                <p style={{ fontSize: 16, color: "rgba(255,255,255,0.5)", textAlign: "center", lineHeight: 1.7, marginBottom: 28 }}>
                  Xin chào! Tôi có thể giúp bạn tra cứu<br />
                  <strong style={{ color: "rgba(255,255,255,0.75)" }}>chính sách HR · onboarding · benefits</strong>
                </p>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                  {QUICK_PROMPTS.map(q => (
                    <button
                      key={q}
                      onClick={() => send(q)}
                      style={{
                        textAlign: "left", padding: "12px 16px", borderRadius: 12, fontSize: 13,
                        background: "rgba(255,255,255,0.05)", color: "rgba(255,255,255,0.65)",
                        border: "1px solid rgba(255,255,255,0.1)", cursor: "pointer",
                        lineHeight: 1.5, transition: "all 0.2s",
                      }}
                      onMouseEnter={e => { e.currentTarget.style.background = "rgba(99,102,241,0.15)"; e.currentTarget.style.borderColor = "rgba(99,102,241,0.4)"; e.currentTarget.style.color = "#f1f5f9"; }}
                      onMouseLeave={e => { e.currentTarget.style.background = "rgba(255,255,255,0.05)"; e.currentTarget.style.borderColor = "rgba(255,255,255,0.1)"; e.currentTarget.style.color = "rgba(255,255,255,0.65)"; }}
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((m, i) => (
              <div key={i} style={{
                display: "flex",
                flexDirection: m.role === "user" ? "row-reverse" : "row",
                alignItems: "flex-end", gap: 10
              }}>
                {/* Avatar */}
                {m.role === "assistant" && (
                  <div style={{
                    width: 30, height: 30, borderRadius: "50%",
                    background: "linear-gradient(135deg,#2563eb,#3b82f6)",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    flexShrink: 0, fontSize: 14
                  }}>🤖</div>
                )}

                <div style={{
                  maxWidth: "76%",
                  borderRadius: m.role === "user" ? "18px 18px 6px 18px" : "18px 18px 18px 6px",
                  padding: "13px 18px", fontSize: 14, lineHeight: 1.7,
                  background: m.role === "user"
                    ? "linear-gradient(135deg,#2563eb,#3b82f6)"
                    : "rgba(255,255,255,0.06)",
                  color: m.role === "user" ? "#fff" : "rgba(255,255,255,0.85)",
                  border: m.role === "assistant" ? "1px solid rgba(255,255,255,0.08)" : "none",
                  boxShadow: m.role === "user" ? "0 4px 16px rgba(37,99,235,0.35)" : "none",
                }}>
                  {m.role === "assistant" ? (
                    <div className="md-dark">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.content}</ReactMarkdown>
                    </div>
                  ) : m.content}
                </div>
              </div>
            ))}

            {loading && (
              <div style={{ display: "flex", alignItems: "flex-end", gap: 10 }}>
                <div style={{
                  width: 30, height: 30, borderRadius: "50%",
                  background: "linear-gradient(135deg,#2563eb,#3b82f6)",
                  display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14
                }}>🤖</div>
                <div style={{
                  padding: "13px 18px", borderRadius: "18px 18px 18px 6px",
                  background: "rgba(255,255,255,0.06)",
                  border: "1px solid rgba(255,255,255,0.08)",
                  display: "flex", gap: 5, alignItems: "center"
                }}>
                  {[0, 1, 2].map(i => (
                    <div key={i} style={{
                      width: 7, height: 7, borderRadius: "50%",
                      background: "rgba(255,255,255,0.4)",
                      animation: `pulse 1.4s ease-in-out ${i * 0.2}s infinite`
                    }} />
                  ))}
                </div>
              </div>
            )}
            <div ref={endRef} />
          </div>

          {/* Input */}
          <div style={{
            padding: "16px 28px 20px",
            borderTop: "1px solid rgba(255,255,255,0.06)",
            background: "#0f172a", flexShrink: 0
          }}>
            <div style={{
              display: "flex", gap: 10, alignItems: "center",
              background: "rgba(255,255,255,0.06)",
              border: "1px solid rgba(255,255,255,0.1)",
              borderRadius: 16, padding: "8px 8px 8px 18px",
              transition: "border-color 0.2s, box-shadow 0.2s",
            }}
              onFocusCapture={e => {
                e.currentTarget.style.borderColor = "rgba(99,102,241,0.5)";
                e.currentTarget.style.boxShadow = "0 0 0 3px rgba(99,102,241,0.12)";
              }}
              onBlurCapture={e => {
                e.currentTarget.style.borderColor = "rgba(255,255,255,0.1)";
                e.currentTarget.style.boxShadow = "none";
              }}
            >
              <input
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => e.key === "Enter" && !e.shiftKey && send(input)}
                placeholder="Hỏi về chính sách, onboarding, benefits..."
                disabled={loading}
                style={{
                  flex: 1, background: "transparent", border: "none", outline: "none",
                  fontSize: 14, color: "#f1f5f9",
                }}
              />
              <button
                onClick={() => send(input)}
                disabled={loading || !input.trim()}
                style={{
                  width: 40, height: 40, borderRadius: 12, border: "none",
                  background: input.trim() && !loading
                    ? "linear-gradient(135deg,#6366f1,#8b5cf6)"
                    : "rgba(255,255,255,0.08)",
                  color: "#fff", display: "flex", alignItems: "center", justifyContent: "center",
                  cursor: input.trim() && !loading ? "pointer" : "default",
                  transition: "all 0.2s",
                  flexShrink: 0,
                }}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" />
                </svg>
              </button>
            </div>
            <div style={{ textAlign: "center", marginTop: 8, fontSize: 11, color: "rgba(255,255,255,0.2)" }}>
              Powered by Vector DB · Paraline HR
            </div>
          </div>
        </div>

        {/* RIGHT — Employee Panel */}
        <EmployeePanel />
      </div>

      <style dangerouslySetInnerHTML={{
        __html: `
        ::placeholder { color: rgba(255,255,255,0.25) !important; }
        input[type="month"]::-webkit-calendar-picker-indicator { filter: invert(1) opacity(0.4); cursor: pointer; }
        .md-dark p { margin: 0 0 8px; }
        .md-dark p:last-child { margin: 0; }
        .md-dark ul, .md-dark ol { margin: 0 0 8px; padding-left: 20px; }
        .md-dark li { margin-bottom: 3px; }
        .md-dark strong { color: #f1f5f9; }
        .md-dark code { background: rgba(255,255,255,0.1); padding: 2px 6px; border-radius: 4px; font-size: 85%; color: #a78bfa; }
        .md-dark pre { background: rgba(0,0,0,0.4); color: #f8fafc; padding: 14px; border-radius: 10px; overflow-x: auto; margin-bottom: 8px; border: 1px solid rgba(255,255,255,0.08); }
        .md-dark h1, .md-dark h2, .md-dark h3 { color: #f1f5f9; margin: 0 0 8px; }
        ::-webkit-scrollbar { width: 5px; height: 5px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }
        @keyframes pulse {
          0%, 80%, 100% { transform: scale(0.8); opacity: 0.4; }
          40% { transform: scale(1.1); opacity: 1; }
        }
      `}} />
    </div>
  );
}
