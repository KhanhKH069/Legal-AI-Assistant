"use client";
import React, { useState, useEffect } from "react";
import { getAttendance, getLeaveRequests, submitLeaveRequest, AttendanceRecord } from "@/lib/api";

type LeaveRequest = { request_id: string; type: string; start_date: string; end_date: string; days: number; reason: string; status: string; approved_by: string | null; submitted_at: string; employee_id: string };
type DayRecord = { date: string; day: string; check_in: string | null; check_out: string | null; total_hours: number; ot_hours: number; status: string };

const STATUS_STYLE: Record<string, { bg: string; text: string; icon: string }> = {
    Present: { bg: "rgba(34,197,94,0.15)", text: "#22c55e", icon: "✅" },
    Leave: { bg: "rgba(251,191,36,0.15)", text: "#fbbf24", icon: "🏖️" },
    Absent: { bg: "rgba(239,68,68,0.15)", text: "#ef4444", icon: "❌" },
};
const LEAVE_STATUS: Record<string, string> = {
    Approved: "#22c55e", Pending: "#fbbf24", Rejected: "#ef4444"
};

export default function AttendancePage() {
    const [empId, setEmpId] = useState("EMP001");
    const [input, setInput] = useState("EMP001");
    const [data, setData] = useState<AttendanceRecord | null>(null);
    const [leaves, setLeaves] = useState<LeaveRequest[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [showForm, setShowForm] = useState(false);
    const [form, setForm] = useState({ leave_type: "Annual Leave", start_date: "", end_date: "", reason: "" });
    const [submitting, setSubmitting] = useState(false);
    const [successMsg, setSuccessMsg] = useState("");

    const load = async (id: string) => {
        setLoading(true); setError("");
        try {
            const [att, lv] = await Promise.all([getAttendance(id), getLeaveRequests(id)]);
            setData(att);
            setLeaves(lv.leave_requests);
        } catch (e: any) { setError(e.message); }
        finally { setLoading(false); }
    };

    useEffect(() => { load(empId); }, [empId]);

    const handleSearch = (e: React.FormEvent) => { e.preventDefault(); setEmpId(input.trim().toUpperCase()); };

    const handleSubmitLeave = async (e: React.FormEvent) => {
        e.preventDefault(); setSubmitting(true); setSuccessMsg("");
        try {
            const r = await submitLeaveRequest({ employee_id: empId, ...form });
            setSuccessMsg(`✅ Đã tạo đơn nghỉ phép ${r.request_id}`);
            setShowForm(false);
            load(empId);
        } catch (e: any) { setError(e.message); }
        finally { setSubmitting(false); }
    };

    const summary = data?.attendance?.weekly_summary;

    return (
        <div style={{ minHeight: "100vh", background: "linear-gradient(135deg,#0f172a 0%,#1e293b 100%)", color: "#e2e8f0", fontFamily: "'Inter',sans-serif", padding: "32px 24px" }}>
            <div style={{ maxWidth: 900, margin: "0 auto" }}>
                {/* Header */}
                <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 32 }}>
                    <a href="/" style={{ color: "#94a3b8", textDecoration: "none", fontSize: 13 }}>← Trang chủ</a>
                    <div style={{ flex: 1 }}>
                        <h1 style={{ margin: 0, fontSize: 28, fontWeight: 700, background: "linear-gradient(90deg,#22c55e,#4ade80)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
                            🕐 Bảng Chấm Công
                        </h1>
                        <p style={{ margin: "4px 0 0", color: "#64748b", fontSize: 14 }}>Xem giờ làm, OT và quản lý đơn nghỉ phép</p>
                    </div>
                </div>

                {/* Search */}
                <form onSubmit={handleSearch} style={{ display: "flex", gap: 10, marginBottom: 28 }}>
                    <input value={input} onChange={e => setInput(e.target.value)}
                        placeholder="Nhập mã nhân viên (VD: EMP001)"
                        style={{ flex: 1, padding: "12px 16px", borderRadius: 10, background: "#1e293b", border: "1px solid #334155", color: "#e2e8f0", fontSize: 14, outline: "none" }} />
                    <button type="submit" style={{ padding: "12px 24px", borderRadius: 10, background: "linear-gradient(90deg,#22c55e,#16a34a)", border: "none", color: "white", fontWeight: 600, cursor: "pointer" }}>
                        Xem
                    </button>
                </form>

                {loading && <div style={{ textAlign: "center", padding: 40, color: "#64748b" }}>⏳ Đang tải...</div>}
                {error && <div style={{ padding: 16, borderRadius: 10, background: "rgba(239,68,68,0.1)", color: "#ef4444", marginBottom: 20 }}>❌ {error}</div>}
                {successMsg && <div style={{ padding: 16, borderRadius: 10, background: "rgba(34,197,94,0.1)", color: "#22c55e", marginBottom: 20 }}>{successMsg}</div>}

                {data && (
                    <>
                        {/* Summary Cards */}
                        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(160px,1fr))", gap: 16, marginBottom: 28 }}>
                            {[
                                { label: "Ngày làm việc", value: `${summary?.total_working_days}/5`, color: "#22c55e" },
                                { label: "Tổng giờ làm", value: `${summary?.total_hours}h`, color: "#60a5fa" },
                                { label: "Giờ OT", value: `${summary?.total_ot_hours}h`, color: "#f59e0b" },
                                { label: "Ngày vắng", value: `${summary?.absent_days}`, color: "#ef4444" },
                                { label: "Ngày nghỉ phép", value: `${summary?.leave_days}`, color: "#a78bfa" },
                            ].map(c => (
                                <div key={c.label} style={{ background: "#1e293b", borderRadius: 12, padding: "18px 20px", border: "1px solid #334155" }}>
                                    <div style={{ fontSize: 24, fontWeight: 700, color: c.color }}>{c.value}</div>
                                    <div style={{ fontSize: 12, color: "#64748b", marginTop: 4 }}>{c.label}</div>
                                </div>
                            ))}
                        </div>

                        {/* Daily Table */}
                        <div style={{ background: "#1e293b", borderRadius: 14, border: "1px solid #334155", marginBottom: 28, overflow: "hidden" }}>
                            <div style={{ padding: "18px 24px", borderBottom: "1px solid #334155" }}>
                                <h3 style={{ margin: 0, fontSize: 16, fontWeight: 600 }}>📋 Chi Tiết Tuần {data.attendance.week} — {data.attendance.name}</h3>
                            </div>
                            <div style={{ overflowX: "auto" }}>
                                <table style={{ width: "100%", borderCollapse: "collapse" }}>
                                    <thead>
                                        <tr style={{ background: "#0f172a" }}>
                                            {["Ngày", "Thứ", "Vào", "Ra", "Tổng giờ", "OT", "Trạng thái"].map(h => (
                                                <th key={h} style={{ padding: "12px 16px", textAlign: "left", fontSize: 12, fontWeight: 600, color: "#64748b", letterSpacing: "0.05em", textTransform: "uppercase" }}>{h}</th>
                                            ))}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {data.attendance.daily_records.map((day, i) => {
                                            const s = STATUS_STYLE[day.status] || STATUS_STYLE.Present;
                                            return (
                                                <tr key={i} style={{ borderTop: "1px solid #1e293b" }}>
                                                    <td style={{ padding: "14px 16px", fontSize: 13, color: "#cbd5e1" }}>{day.date}</td>
                                                    <td style={{ padding: "14px 16px", fontSize: 13, color: "#94a3b8" }}>{day.day}</td>
                                                    <td style={{ padding: "14px 16px", fontSize: 13, fontWeight: 600, color: "#22c55e" }}>{day.check_in || "—"}</td>
                                                    <td style={{ padding: "14px 16px", fontSize: 13, fontWeight: 600, color: "#60a5fa" }}>{day.check_out || "—"}</td>
                                                    <td style={{ padding: "14px 16px", fontSize: 13 }}>{day.total_hours}h</td>
                                                    <td style={{ padding: "14px 16px", fontSize: 13, color: day.ot_hours > 0 ? "#f59e0b" : "#475569" }}>{day.ot_hours > 0 ? `+${day.ot_hours}h` : "—"}</td>
                                                    <td style={{ padding: "14px 16px" }}>
                                                        <span style={{ padding: "4px 12px", borderRadius: 20, fontSize: 12, fontWeight: 600, background: s.bg, color: s.text }}>
                                                            {s.icon} {day.status}
                                                        </span>
                                                    </td>
                                                </tr>
                                            );
                                        })}
                                    </tbody>
                                </table>
                            </div>
                        </div>

                        {/* Leave Requests */}
                        <div style={{ background: "#1e293b", borderRadius: 14, border: "1px solid #334155", overflow: "hidden" }}>
                            <div style={{ padding: "18px 24px", borderBottom: "1px solid #334155", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                                <h3 style={{ margin: 0, fontSize: 16, fontWeight: 600 }}>📄 Danh Sách Đơn Nghỉ Phép</h3>
                                <button onClick={() => setShowForm(!showForm)}
                                    style={{ padding: "8px 18px", borderRadius: 8, background: "linear-gradient(90deg,#22c55e,#16a34a)", border: "none", color: "white", fontSize: 13, fontWeight: 600, cursor: "pointer" }}>
                                    + Nộp đơn
                                </button>
                            </div>

                            {showForm && (
                                <form onSubmit={handleSubmitLeave} style={{ padding: "20px 24px", borderBottom: "1px solid #334155", background: "#0f172a" }}>
                                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, marginBottom: 14 }}>
                                        <div>
                                            <label style={{ fontSize: 12, color: "#64748b", display: "block", marginBottom: 6 }}>Loại nghỉ phép</label>
                                            <select value={form.leave_type} onChange={e => setForm({ ...form, leave_type: e.target.value })}
                                                style={{ width: "100%", padding: "10px 12px", borderRadius: 8, background: "#1e293b", border: "1px solid #334155", color: "#e2e8f0", fontSize: 13 }}>
                                                {["Annual Leave", "Sick Leave", "Unpaid Leave", "Maternity Leave"].map(t => <option key={t}>{t}</option>)}
                                            </select>
                                        </div>
                                        <div>
                                            <label style={{ fontSize: 12, color: "#64748b", display: "block", marginBottom: 6 }}>Ngày bắt đầu</label>
                                            <input type="date" value={form.start_date} onChange={e => setForm({ ...form, start_date: e.target.value })} required
                                                style={{ width: "100%", padding: "10px 12px", borderRadius: 8, background: "#1e293b", border: "1px solid #334155", color: "#e2e8f0", fontSize: 13, boxSizing: "border-box" }} />
                                        </div>
                                        <div>
                                            <label style={{ fontSize: 12, color: "#64748b", display: "block", marginBottom: 6 }}>Ngày kết thúc</label>
                                            <input type="date" value={form.end_date} onChange={e => setForm({ ...form, end_date: e.target.value })} required
                                                style={{ width: "100%", padding: "10px 12px", borderRadius: 8, background: "#1e293b", border: "1px solid #334155", color: "#e2e8f0", fontSize: 13, boxSizing: "border-box" }} />
                                        </div>
                                        <div>
                                            <label style={{ fontSize: 12, color: "#64748b", display: "block", marginBottom: 6 }}>Lý do</label>
                                            <input value={form.reason} onChange={e => setForm({ ...form, reason: e.target.value })} required placeholder="Nhập lý do nghỉ phép"
                                                style={{ width: "100%", padding: "10px 12px", borderRadius: 8, background: "#1e293b", border: "1px solid #334155", color: "#e2e8f0", fontSize: 13, boxSizing: "border-box" }} />
                                        </div>
                                    </div>
                                    <button type="submit" disabled={submitting}
                                        style={{ padding: "10px 24px", borderRadius: 8, background: "linear-gradient(90deg,#22c55e,#16a34a)", border: "none", color: "white", fontWeight: 600, cursor: "pointer", opacity: submitting ? 0.6 : 1 }}>
                                        {submitting ? "Đang gửi..." : "Nộp đơn"}
                                    </button>
                                </form>
                            )}

                            <div style={{ padding: "8px 0" }}>
                                {leaves.length === 0 ? (
                                    <div style={{ padding: "32px", textAlign: "center", color: "#475569" }}>Chưa có đơn nghỉ phép nào</div>
                                ) : leaves.map(r => (
                                    <div key={r.request_id} style={{ padding: "16px 24px", borderBottom: "1px solid #0f172a", display: "flex", alignItems: "center", gap: 16 }}>
                                        <div style={{ flex: 1 }}>
                                            <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 4 }}>{r.type} <span style={{ fontSize: 12, color: "#64748b" }}>({r.request_id})</span></div>
                                            <div style={{ fontSize: 13, color: "#94a3b8" }}>{r.start_date} → {r.end_date} · {r.days} ngày · {r.reason}</div>
                                        </div>
                                        <span style={{ padding: "4px 14px", borderRadius: 20, fontSize: 12, fontWeight: 600, background: `${LEAVE_STATUS[r.status]}22`, color: LEAVE_STATUS[r.status] || "#94a3b8" }}>
                                            {r.status}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}
