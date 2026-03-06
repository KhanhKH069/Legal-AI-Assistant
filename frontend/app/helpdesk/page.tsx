"use client";
import React, { useState, useEffect } from "react";
import { listEmployeeTickets, createTicket, getHelpdeskCategories, HelpdeskTicket } from "@/lib/api";

const PRIORITY_COLOR: Record<string, string> = { Low: "#60a5fa", Medium: "#fbbf24", High: "#f97316", Critical: "#ef4444" };
const STATUS_COLOR: Record<string, string> = { "Open": "#22c55e", "In Progress": "#60a5fa", "Pending Employee": "#fbbf24", "Resolved": "#a78bfa", "Closed": "#475569" };
const STATUS_ICON: Record<string, string> = { "Open": "🔓", "In Progress": "🔄", "Pending Employee": "⏳", "Resolved": "✅", "Closed": "🔒" };

export default function HelpdeskPage() {
    const [empId, setEmpId] = useState("EMP001");
    const [input, setInput] = useState("EMP001");
    const [tickets, setTickets] = useState<HelpdeskTicket[]>([]);
    const [categories, setCategories] = useState<string[]>([]);
    const [priorities, setPriorities] = useState<string[]>([]);
    const [loading, setLoading] = useState(false);
    const [showForm, setShowForm] = useState(false);
    const [success, setSuccess] = useState("");
    const [error, setError] = useState("");
    const [form, setForm] = useState({ category: "Equipment", subject: "", description: "", priority: "Medium" });
    const [submitting, setSubmitting] = useState(false);
    const [selected, setSelected] = useState<HelpdeskTicket | null>(null);

    const load = async (id: string) => {
        setLoading(true); setError("");
        try {
            const [tickRes, catRes] = await Promise.all([listEmployeeTickets(id), getHelpdeskCategories()]);
            setTickets(tickRes.tickets);
            setCategories(catRes.categories);
            setPriorities(catRes.priority_levels);
        } catch (e: any) { setError(e.message); }
        finally { setLoading(false); }
    };

    useEffect(() => { load(empId); }, [empId]);

    const handleSearch = (e: React.FormEvent) => { e.preventDefault(); setEmpId(input.trim().toUpperCase()); };

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault(); setSubmitting(true); setSuccess("");
        try {
            const r = await createTicket({ employee_id: empId, ...form });
            setSuccess(`✅ Ticket ${r.ticket_id} đã được tạo thành công!`);
            setShowForm(false);
            setForm({ category: "Equipment", subject: "", description: "", priority: "Medium" });
            load(empId);
        } catch (e: any) { setError(e.message); }
        finally { setSubmitting(false); }
    };

    return (
        <div style={{ minHeight: "100vh", background: "linear-gradient(135deg,#0f172a 0%,#1e293b 100%)", color: "#e2e8f0", fontFamily: "'Inter',sans-serif", padding: "32px 24px" }}>
            <div style={{ maxWidth: 960, margin: "0 auto" }}>
                {/* Header */}
                <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 32 }}>
                    <a href="/" style={{ color: "#94a3b8", textDecoration: "none", fontSize: 13 }}>← Trang chủ</a>
                    <div style={{ flex: 1 }}>
                        <h1 style={{ margin: 0, fontSize: 28, fontWeight: 700, background: "linear-gradient(90deg,#fb923c,#f97316)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
                            🎫 HR Helpdesk
                        </h1>
                        <p style={{ margin: "4px 0 0", color: "#64748b", fontSize: 14 }}>Tạo và theo dõi yêu cầu hỗ trợ HR</p>
                    </div>
                </div>

                <div style={{ display: "flex", gap: 24 }}>
                    {/* Left: Ticket List */}
                    <div style={{ flex: 1 }}>
                        <form onSubmit={handleSearch} style={{ display: "flex", gap: 10, marginBottom: 20 }}>
                            <input value={input} onChange={e => setInput(e.target.value)} placeholder="Mã nhân viên (VD: EMP001)"
                                style={{ flex: 1, padding: "11px 14px", borderRadius: 9, background: "#1e293b", border: "1px solid #334155", color: "#e2e8f0", fontSize: 13, outline: "none" }} />
                            <button type="submit" style={{ padding: "11px 20px", borderRadius: 9, background: "linear-gradient(90deg,#fb923c,#f97316)", border: "none", color: "white", fontWeight: 600, cursor: "pointer" }}>Xem</button>
                        </form>

                        {success && <div style={{ padding: 14, borderRadius: 9, background: "rgba(34,197,94,0.1)", color: "#22c55e", marginBottom: 16, fontSize: 13 }}>{success}</div>}
                        {error && <div style={{ padding: 14, borderRadius: 9, background: "rgba(239,68,68,0.1)", color: "#ef4444", marginBottom: 16, fontSize: 13 }}>❌ {error}</div>}

                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                            <h3 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>Tickets của {empId} ({tickets.length})</h3>
                            <button onClick={() => setShowForm(!showForm)}
                                style={{ padding: "8px 18px", borderRadius: 8, background: "linear-gradient(90deg,#fb923c,#f97316)", border: "none", color: "white", fontSize: 13, fontWeight: 600, cursor: "pointer" }}>
                                + Tạo Ticket
                            </button>
                        </div>

                        {loading && <div style={{ textAlign: "center", padding: 40, color: "#64748b" }}>⏳ Đang tải...</div>}

                        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                            {tickets.map(t => (
                                <div key={t.ticket_id} onClick={() => setSelected(t)}
                                    style={{ background: "#1e293b", borderRadius: 12, padding: "16px 20px", border: `1px solid ${selected?.ticket_id === t.ticket_id ? "#fb923c44" : "#334155"}`, cursor: "pointer", transition: "all 0.2s" }}>
                                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
                                        <div>
                                            <span style={{ fontSize: 11, color: "#64748b", fontFamily: "monospace" }}>{t.ticket_id}</span>
                                            <div style={{ fontSize: 14, fontWeight: 600, marginTop: 2 }}>{t.subject}</div>
                                        </div>
                                        <div style={{ display: "flex", gap: 8, flexShrink: 0 }}>
                                            <span style={{ padding: "3px 10px", borderRadius: 12, fontSize: 11, fontWeight: 700, background: `${PRIORITY_COLOR[t.priority]}22`, color: PRIORITY_COLOR[t.priority] }}>{t.priority}</span>
                                            <span style={{ padding: "3px 10px", borderRadius: 12, fontSize: 11, fontWeight: 700, background: `${STATUS_COLOR[t.status]}22`, color: STATUS_COLOR[t.status] }}>{STATUS_ICON[t.status]} {t.status}</span>
                                        </div>
                                    </div>
                                    <div style={{ fontSize: 12, color: "#64748b" }}>{t.category} · {t.created_at.slice(0, 10)}</div>
                                </div>
                            ))}
                            {!loading && tickets.length === 0 && <div style={{ textAlign: "center", padding: 40, color: "#475569" }}>Chưa có ticket nào</div>}
                        </div>
                    </div>

                    {/* Right: Detail / Form */}
                    <div style={{ width: 340, flexShrink: 0 }}>
                        {showForm && (
                            <div style={{ background: "#1e293b", borderRadius: 14, border: "1px solid #334155", padding: "20px", marginBottom: 20 }}>
                                <h3 style={{ margin: "0 0 16px", fontSize: 15, fontWeight: 600 }}>Tạo Ticket Mới</h3>
                                <form onSubmit={handleCreate}>
                                    {[
                                        { label: "Danh mục", key: "category", type: "select", options: categories },
                                        { label: "Mức độ ưu tiên", key: "priority", type: "select", options: priorities },
                                        { label: "Tiêu đề", key: "subject", type: "input", placeholder: "Nhập tiêu đề ngắn gọn" },
                                        { label: "Mô tả chi tiết", key: "description", type: "textarea", placeholder: "Mô tả vấn đề..." },
                                    ].map(f => (
                                        <div key={f.key} style={{ marginBottom: 14 }}>
                                            <label style={{ fontSize: 12, color: "#64748b", display: "block", marginBottom: 5 }}>{f.label}</label>
                                            {f.type === "select" ? (
                                                <select value={(form as any)[f.key]} onChange={e => setForm({ ...form, [f.key]: e.target.value })}
                                                    style={{ width: "100%", padding: "9px 10px", borderRadius: 7, background: "#0f172a", border: "1px solid #334155", color: "#e2e8f0", fontSize: 13 }}>
                                                    {f.options?.map(o => <option key={o}>{o}</option>)}
                                                </select>
                                            ) : f.type === "textarea" ? (
                                                <textarea value={(form as any)[f.key]} onChange={e => setForm({ ...form, [f.key]: e.target.value })} required rows={4}
                                                    placeholder={f.placeholder}
                                                    style={{ width: "100%", padding: "9px 10px", borderRadius: 7, background: "#0f172a", border: "1px solid #334155", color: "#e2e8f0", fontSize: 13, resize: "vertical", boxSizing: "border-box" }} />
                                            ) : (
                                                <input value={(form as any)[f.key]} onChange={e => setForm({ ...form, [f.key]: e.target.value })} required placeholder={f.placeholder}
                                                    style={{ width: "100%", padding: "9px 10px", borderRadius: 7, background: "#0f172a", border: "1px solid #334155", color: "#e2e8f0", fontSize: 13, boxSizing: "border-box" }} />
                                            )}
                                        </div>
                                    ))}
                                    <button type="submit" disabled={submitting}
                                        style={{ width: "100%", padding: "11px", borderRadius: 8, background: "linear-gradient(90deg,#fb923c,#f97316)", border: "none", color: "white", fontWeight: 600, cursor: "pointer", opacity: submitting ? 0.6 : 1 }}>
                                        {submitting ? "Đang tạo..." : "Tạo Ticket"}
                                    </button>
                                </form>
                            </div>
                        )}

                        {selected && (
                            <div style={{ background: "#1e293b", borderRadius: 14, border: "1px solid #334155", padding: "20px" }}>
                                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16 }}>
                                    <h3 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>Chi Tiết Ticket</h3>
                                    <button onClick={() => setSelected(null)} style={{ background: "none", border: "none", color: "#64748b", cursor: "pointer", fontSize: 18 }}>×</button>
                                </div>
                                <div style={{ fontSize: 11, color: "#64748b", fontFamily: "monospace", marginBottom: 8 }}>{selected.ticket_id}</div>
                                <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 16 }}>{selected.subject}</div>
                                {[
                                    { label: "Danh mục", value: selected.category },
                                    { label: "Mức độ", value: selected.priority },
                                    { label: "Trạng thái", value: `${STATUS_ICON[selected.status]} ${selected.status}` },
                                    { label: "Xử lý bởi", value: selected.assigned_to },
                                    { label: "Tạo lúc", value: selected.created_at.slice(0, 10) },
                                ].map(r => (
                                    <div key={r.label} style={{ display: "flex", justifyContent: "space-between", padding: "8px 0", borderBottom: "1px solid #0f172a", fontSize: 13 }}>
                                        <span style={{ color: "#64748b" }}>{r.label}</span>
                                        <span style={{ fontWeight: 500 }}>{r.value}</span>
                                    </div>
                                ))}
                                <div style={{ marginTop: 16 }}>
                                    <div style={{ fontSize: 12, color: "#64748b", marginBottom: 8 }}>Mô tả</div>
                                    <div style={{ fontSize: 13, color: "#94a3b8", lineHeight: 1.6 }}>{selected.description}</div>
                                </div>
                                {selected.resolution && (
                                    <div style={{ marginTop: 16, padding: "12px", borderRadius: 8, background: "rgba(167,139,250,0.1)", border: "1px solid rgba(167,139,250,0.2)" }}>
                                        <div style={{ fontSize: 12, color: "#a78bfa", fontWeight: 600, marginBottom: 4 }}>✅ Giải pháp</div>
                                        <div style={{ fontSize: 13, color: "#94a3b8" }}>{selected.resolution}</div>
                                    </div>
                                )}
                                {selected.comments.length > 0 && (
                                    <div style={{ marginTop: 16 }}>
                                        <div style={{ fontSize: 12, color: "#64748b", marginBottom: 8 }}>Cập nhật</div>
                                        {selected.comments.map((c, i) => (
                                            <div key={i} style={{ fontSize: 12, color: "#94a3b8", padding: "8px 12px", background: "#0f172a", borderRadius: 7, marginBottom: 6 }}>
                                                <strong style={{ color: "#e2e8f0" }}>{c.author}:</strong> {c.message}
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
