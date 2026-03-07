"use client";
import React, { useState, useEffect, useCallback } from "react";
import { getPayrollHistory, getPayrollMonth, PayrollEntry, PayrollRecord } from "@/lib/api";

const fmtVND = (n: number) =>
    new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(n);

const MONTHS = [
    { value: "2026-03", label: "Tháng 3/2026" },
    { value: "2026-02", label: "Tháng 2/2026" },
    { value: "2026-01", label: "Tháng 1/2026" },
];

type BreakdownItem = { label: string; value: number; color: string; type: "income" | "deduction" };

function PayrollBreakdown({ entry }: { entry: PayrollEntry }) {
    const incomes: BreakdownItem[] = [
        { label: "Lương cơ bản", value: entry.base_salary, color: "#22c55e", type: "income" as const },
        { label: `Phụ cấp OT (${entry.ot_hours}h × ${entry.ot_rate})`, value: entry.ot_pay, color: "#60a5fa", type: "income" as const },
        { label: "Thưởng KPI", value: entry.kpi_bonus, color: "#a78bfa", type: "income" as const },
        { label: "Thưởng khác", value: entry.other_bonus, color: "#f59e0b", type: "income" as const },
    ].filter(i => i.value > 0);

    const deductions: BreakdownItem[] = [
        { label: "BHXH (8%)", value: entry.social_insurance, color: "#f87171", type: "deduction" as const },
        { label: "BHYT (1.5%)", value: entry.health_insurance, color: "#fb923c", type: "deduction" as const },
        { label: "BHTN (1%)", value: entry.unemployment_insurance, color: "#fbbf24", type: "deduction" as const },
        { label: "Thuế TNCN", value: entry.income_tax, color: "#ef4444", type: "deduction" as const },
    ].filter(i => i.value > 0);

    const maxVal = Math.max(entry.gross_salary, 1);

    return (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
            {/* Income */}
            <div style={{ background: "#0f172a", borderRadius: 12, padding: "20px" }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: "#22c55e", marginBottom: 14, letterSpacing: "0.05em", textTransform: "uppercase" }}> Thu Nhập</div>
                {incomes.map(item => (
                    <div key={item.label} style={{ marginBottom: 14 }}>
                        <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, marginBottom: 6 }}>
                            <span style={{ color: "#94a3b8" }}>{item.label}</span>
                            <span style={{ fontWeight: 600, color: item.color }}>{fmtVND(item.value)}</span>
                        </div>
                        <div style={{ height: 4, borderRadius: 4, background: "#1e293b", overflow: "hidden" }}>
                            <div style={{ height: "100%", width: `${(item.value / maxVal) * 100}%`, background: item.color, borderRadius: 4, transition: "width 0.6s ease" }} />
                        </div>
                    </div>
                ))}
                <div style={{ borderTop: "1px solid #1e293b", marginTop: 12, paddingTop: 12, display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "#64748b", fontSize: 13 }}>Tổng Gross</span>
                    <span style={{ fontWeight: 700, color: "#22c55e" }}>{fmtVND(entry.gross_salary)}</span>
                </div>
            </div>

            {/* Deductions */}
            <div style={{ background: "#0f172a", borderRadius: 12, padding: "20px" }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: "#ef4444", marginBottom: 14, letterSpacing: "0.05em", textTransform: "uppercase" }}> Khấu Trừ</div>
                {deductions.map(item => (
                    <div key={item.label} style={{ marginBottom: 14 }}>
                        <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, marginBottom: 6 }}>
                            <span style={{ color: "#94a3b8" }}>{item.label}</span>
                            <span style={{ fontWeight: 600, color: item.color }}>{fmtVND(item.value)}</span>
                        </div>
                        <div style={{ height: 4, borderRadius: 4, background: "#1e293b", overflow: "hidden" }}>
                            <div style={{ height: "100%", width: `${(item.value / maxVal) * 100}%`, background: item.color, borderRadius: 4, transition: "width 0.6s ease" }} />
                        </div>
                    </div>
                ))}
                <div style={{ borderTop: "1px solid #1e293b", marginTop: 12, paddingTop: 12, display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "#64748b", fontSize: 13 }}>Tổng Khấu Trừ</span>
                    <span style={{ fontWeight: 700, color: "#ef4444" }}>−{fmtVND(entry.total_deductions)}</span>
                </div>
            </div>
        </div>
    );
}

export default function PayrollPage() {
    const [empId, setEmpId] = useState("EMP001");
    const [input, setInput] = useState("EMP001");
    const [selectedMonth, setSelectedMonth] = useState("2026-03");
    const [record, setRecord] = useState<PayrollRecord | null>(null);
    const [currentEntry, setCurrentEntry] = useState<PayrollEntry | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const load = useCallback(async (id: string, month: string) => {
        setLoading(true); setError("");
        try {
            const [hist, monthly] = await Promise.all([
                getPayrollHistory(id),
                getPayrollMonth(id, month),
            ]);
            setRecord(hist);
            setCurrentEntry(monthly.payroll);
        } catch (e: any) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { load(empId, selectedMonth); }, [empId, selectedMonth, load]);

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        setEmpId(input.trim().toUpperCase());
    };

    const statusColor = currentEntry?.status === "Paid" ? "#22c55e" : "#f59e0b";
    const statusLabel = currentEntry?.status === "Paid" ? " Đã thanh toán" : " Chờ thanh toán";

    return (
        <div style={{ minHeight: "100vh", background: "linear-gradient(135deg,#0f172a 0%,#1e293b 100%)", color: "#e2e8f0", fontFamily: "'Inter',sans-serif", padding: "32px 24px" }}>
            <div style={{ maxWidth: 1000, margin: "0 auto" }}>
                {/* Header */}
                <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 32 }}>
                    <a href="/" style={{ color: "#94a3b8", textDecoration: "none", fontSize: 13 }}>← Trang chủ</a>
                    <div style={{ flex: 1 }}>
                        <h1 style={{ margin: 0, fontSize: 28, fontWeight: 700, background: "linear-gradient(90deg,#f59e0b,#fbbf24)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
                             Bảng Lương
                        </h1>
                        <p style={{ margin: "4px 0 0", color: "#64748b", fontSize: 14 }}>Xem chi tiết lương, OT, thưởng và khấu trừ theo tháng</p>
                    </div>
                </div>

                {/* Search + Month picker */}
                <div style={{ display: "flex", gap: 12, marginBottom: 28, flexWrap: "wrap" }}>
                    <form onSubmit={handleSearch} style={{ display: "flex", gap: 10, flex: 1, minWidth: 280 }}>
                        <input value={input} onChange={e => setInput(e.target.value)}
                            placeholder="Nhập mã nhân viên (VD: EMP001)"
                            style={{ flex: 1, padding: "12px 16px", borderRadius: 10, background: "#1e293b", border: "1px solid #334155", color: "#e2e8f0", fontSize: 14, outline: "none" }} />
                        <button type="submit" style={{ padding: "12px 24px", borderRadius: 10, background: "linear-gradient(90deg,#f59e0b,#d97706)", border: "none", color: "white", fontWeight: 600, cursor: "pointer" }}>
                            Xem
                        </button>
                    </form>
                    <select value={selectedMonth} onChange={e => setSelectedMonth(e.target.value)}
                        style={{ padding: "12px 16px", borderRadius: 10, background: "#1e293b", border: "1px solid #334155", color: "#e2e8f0", fontSize: 14, cursor: "pointer", minWidth: 160 }}>
                        {MONTHS.map(m => <option key={m.value} value={m.value}>{m.label}</option>)}
                    </select>
                </div>

                {loading && <div style={{ textAlign: "center", padding: 40, color: "#64748b" }}> Đang tải...</div>}
                {error && <div style={{ padding: 16, borderRadius: 10, background: "rgba(239,68,68,0.1)", color: "#ef4444", marginBottom: 20 }}>❌ {error}</div>}

                {currentEntry && record && (
                    <>
                        {/* Employee info + Net Salary hero */}
                        <div style={{ background: "#1e293b", borderRadius: 18, padding: "28px 32px", border: "1px solid #334155", marginBottom: 24, position: "relative", overflow: "hidden" }}>
                            <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 3, background: "linear-gradient(90deg,#f59e0b,#fbbf24,#f59e0b)" }} />
                            <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", flexWrap: "wrap", gap: 20 }}>
                                <div>
                                    <div style={{ fontSize: 22, fontWeight: 800, marginBottom: 4 }}>{record.name}</div>
                                    <div style={{ fontSize: 14, color: "#64748b" }}>{record.department} · {record.position} · {empId}</div>
                                    <div style={{ marginTop: 10, fontSize: 13, color: "#94a3b8" }}>
                                        📅 {currentEntry.month_label} &nbsp;·&nbsp;
                                        Công chuẩn: <strong>{currentEntry.working_days}</strong> ngày &nbsp;·&nbsp;
                                        Thực tế: <strong>{currentEntry.days_worked}</strong> ngày &nbsp;·&nbsp;
                                        Nghỉ phép: <strong>{currentEntry.leave_days}</strong> ngày
                                    </div>
                                    <div style={{ marginTop: 6, fontSize: 13 }}>
                                        <span style={{ padding: "3px 12px", borderRadius: 20, background: `${statusColor}22`, color: statusColor, fontWeight: 600 }}>
                                            {statusLabel}
                                        </span>
                                        <span style={{ marginLeft: 8, color: "#475569", fontSize: 12 }}>Ngày TT: {currentEntry.payment_date}</span>
                                    </div>
                                </div>
                                <div style={{ textAlign: "right" }}>
                                    <div style={{ fontSize: 12, color: "#64748b", marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.1em" }}>Lương Thực Nhận</div>
                                    <div style={{ fontSize: 36, fontWeight: 900, background: "linear-gradient(90deg,#f59e0b,#fbbf24)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", lineHeight: 1.1 }}>
                                        {fmtVND(currentEntry.net_salary)}
                                    </div>
                                    <div style={{ fontSize: 13, color: "#475569", marginTop: 4 }}>
                                        Gross: {fmtVND(currentEntry.gross_salary)}
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Summary cards */}
                        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(160px,1fr))", gap: 14, marginBottom: 24 }}>
                            {[
                                { label: "Lương cơ bản", value: fmtVND(currentEntry.base_salary), color: "#22c55e", icon: "" },
                                { label: `OT (${currentEntry.ot_hours}h)`, value: fmtVND(currentEntry.ot_pay), color: "#60a5fa", icon: "" },
                                { label: "Thưởng KPI", value: fmtVND(currentEntry.kpi_bonus), color: "#a78bfa", icon: "" },
                                { label: "Tổng khấu trừ", value: `−${fmtVND(currentEntry.total_deductions)}`, color: "#ef4444", icon: "" },
                                { label: "Lương thực nhận", value: fmtVND(currentEntry.net_salary), color: "#f59e0b", icon: "" },
                            ].map(c => (
                                <div key={c.label} style={{ background: "#1e293b", borderRadius: 12, padding: "18px 16px", border: "1px solid #334155" }}>
                                    <div style={{ fontSize: 18, marginBottom: 6 }}>{c.icon}</div>
                                    <div style={{ fontSize: 15, fontWeight: 700, color: c.color }}>{c.value}</div>
                                    <div style={{ fontSize: 11, color: "#64748b", marginTop: 4 }}>{c.label}</div>
                                </div>
                            ))}
                        </div>

                        {/* Breakdown chart */}
                        <div style={{ background: "#1e293b", borderRadius: 14, border: "1px solid #334155", marginBottom: 24, overflow: "hidden" }}>
                            <div style={{ padding: "18px 24px", borderBottom: "1px solid #334155" }}>
                                <h3 style={{ margin: 0, fontSize: 16, fontWeight: 600 }}> Chi Tiết Thu Nhập & Khấu Trừ</h3>
                            </div>
                            <div style={{ padding: "20px 24px" }}>
                                <PayrollBreakdown entry={currentEntry} />
                            </div>
                        </div>

                        {/* Salary history table */}
                        {record.salary_history.length > 1 && (
                            <div style={{ background: "#1e293b", borderRadius: 14, border: "1px solid #334155", overflow: "hidden" }}>
                                <div style={{ padding: "18px 24px", borderBottom: "1px solid #334155" }}>
                                    <h3 style={{ margin: 0, fontSize: 16, fontWeight: 600 }}>📈 Lịch Sử Lương 3 Tháng Gần Nhất</h3>
                                </div>
                                <div style={{ overflowX: "auto" }}>
                                    <table style={{ width: "100%", borderCollapse: "collapse" }}>
                                        <thead>
                                            <tr style={{ background: "#0f172a" }}>
                                                {["Tháng", "Gross", "Khấu Trừ", "Thực Nhận", "OT (h)", "Ngày Làm", "Trạng Thái"].map(h => (
                                                    <th key={h} style={{ padding: "12px 16px", textAlign: "left", fontSize: 11, fontWeight: 600, color: "#64748b", letterSpacing: "0.07em", textTransform: "uppercase", whiteSpace: "nowrap" }}>{h}</th>
                                                ))}
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {[...record.salary_history].reverse().map((entry, i) => {
                                                const prev = [...record.salary_history].reverse()[i + 1];
                                                const diff = prev ? entry.net_salary - prev.net_salary : 0;
                                                const isSelected = entry.month === selectedMonth;
                                                return (
                                                    <tr key={entry.month}
                                                        onClick={() => setSelectedMonth(entry.month)}
                                                        style={{ borderTop: "1px solid #0f172a", cursor: "pointer", background: isSelected ? "rgba(245,158,11,0.08)" : "transparent", transition: "background 0.2s" }}>
                                                        <td style={{ padding: "14px 16px", fontSize: 13, fontWeight: isSelected ? 700 : 400, color: isSelected ? "#f59e0b" : "#e2e8f0" }}>{entry.month_label}</td>
                                                        <td style={{ padding: "14px 16px", fontSize: 13, color: "#22c55e" }}>{fmtVND(entry.gross_salary)}</td>
                                                        <td style={{ padding: "14px 16px", fontSize: 13, color: "#ef4444" }}>−{fmtVND(entry.total_deductions)}</td>
                                                        <td style={{ padding: "14px 16px", fontSize: 13, fontWeight: 700, color: "#f59e0b" }}>
                                                            {fmtVND(entry.net_salary)}
                                                            {diff !== 0 && <span style={{ marginLeft: 6, fontSize: 11, color: diff > 0 ? "#22c55e" : "#ef4444" }}>{diff > 0 ? "▲" : "▼"}{fmtVND(Math.abs(diff))}</span>}
                                                        </td>
                                                        <td style={{ padding: "14px 16px", fontSize: 13, color: "#60a5fa" }}>{entry.ot_hours}h</td>
                                                        <td style={{ padding: "14px 16px", fontSize: 13, color: "#94a3b8" }}>{entry.days_worked}/{entry.working_days}</td>
                                                        <td style={{ padding: "14px 16px" }}>
                                                            <span style={{ padding: "3px 12px", borderRadius: 20, fontSize: 12, fontWeight: 600, background: entry.status === "Paid" ? "rgba(34,197,94,0.15)" : "rgba(245,158,11,0.15)", color: entry.status === "Paid" ? "#22c55e" : "#f59e0b" }}>
                                                                {entry.status === "Paid" ? " Đã TT" : " Pending"}
                                                            </span>
                                                        </td>
                                                    </tr>
                                                );
                                            })}
                                        </tbody>
                                    </table>
                                </div>
                                <div style={{ padding: "12px 24px", borderTop: "1px solid #0f172a", fontSize: 12, color: "#475569" }}>
                                     Click vào dòng để xem chi tiết tháng đó
                                </div>
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
}
