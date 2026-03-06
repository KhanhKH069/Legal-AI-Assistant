"use client";
import React, { useState, useEffect } from "react";
import { getEmployeeBenefits, getBenefitsCatalog, requestBenefitChange, EmployeeBenefits } from "@/lib/api";

const PKG_COLOR: Record<string, string> = { Basic: "#60a5fa", Standard: "#22c55e", Premium: "#f59e0b" };
const PKG_DESC: Record<string, string> = {
    Basic: "Cơ bản · Nội trú + Cấp cứu",
    Standard: "Tiêu chuẩn · + Nha khoa",
    Premium: "Cao cấp · + Quốc tế + Thị lực"
};

export default function BenefitsPage() {
    const [empId, setEmpId] = useState("EMP001");
    const [input, setInput] = useState("EMP001");
    const [benefits, setBenefits] = useState<EmployeeBenefits | null>(null);
    const [catalog, setCatalog] = useState<Record<string, any>>({});
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");
    const [showChange, setShowChange] = useState(false);
    const [changeForm, setChangeForm] = useState({ benefit_type: "health_insurance", requested_change: "" });

    const load = async (id: string) => {
        setLoading(true); setError("");
        try {
            const [b, c] = await Promise.all([getEmployeeBenefits(id), getBenefitsCatalog()]);
            setBenefits(b.benefits);
            setCatalog(c.benefits_catalog);
        } catch (e: any) { setError(e.message); }
        finally { setLoading(false); }
    };

    useEffect(() => { load(empId); }, [empId]);

    const handleSearch = (e: React.FormEvent) => { e.preventDefault(); setEmpId(input.trim().toUpperCase()); };

    const handleChange = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await requestBenefitChange({ employee_id: empId, ...changeForm });
            setSuccess("✅ Yêu cầu thay đổi phúc lợi đã được gửi!");
            setShowChange(false);
            load(empId);
        } catch (e: any) { setError(e.message); }
    };

    const pkg = benefits?.health_insurance_package;
    const pkgInfo = pkg ? catalog?.health_insurance?.packages?.[pkg] : null;
    const trainTotal = (benefits?.training_budget_used ?? 0) + (benefits?.training_budget_remaining ?? 0);
    const trainPct = trainTotal > 0 ? Math.round(((benefits?.training_budget_used ?? 0) / trainTotal) * 100) : 0;

    return (
        <div style={{ minHeight: "100vh", background: "linear-gradient(135deg,#0f172a 0%,#1e293b 100%)", color: "#e2e8f0", fontFamily: "'Inter',sans-serif", padding: "32px 24px" }}>
            <div style={{ maxWidth: 900, margin: "0 auto" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 32 }}>
                    <a href="/" style={{ color: "#94a3b8", textDecoration: "none", fontSize: 13 }}>← Trang chủ</a>
                    <div style={{ flex: 1 }}>
                        <h1 style={{ margin: 0, fontSize: 28, fontWeight: 700, background: "linear-gradient(90deg,#a78bfa,#7c3aed)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
                            🎁 Phúc Lợi Nhân Viên
                        </h1>
                        <p style={{ margin: "4px 0 0", color: "#64748b", fontSize: 14 }}>Quản lý bảo hiểm, phụ cấp và quyền lợi</p>
                    </div>
                </div>

                <form onSubmit={handleSearch} style={{ display: "flex", gap: 10, marginBottom: 28 }}>
                    <input value={input} onChange={e => setInput(e.target.value)} placeholder="Mã nhân viên (VD: EMP001)"
                        style={{ flex: 1, padding: "12px 16px", borderRadius: 10, background: "#1e293b", border: "1px solid #334155", color: "#e2e8f0", fontSize: 14, outline: "none" }} />
                    <button type="submit" style={{ padding: "12px 24px", borderRadius: 10, background: "linear-gradient(90deg,#a78bfa,#7c3aed)", border: "none", color: "white", fontWeight: 600, cursor: "pointer" }}>Xem</button>
                </form>

                {loading && <div style={{ textAlign: "center", padding: 40, color: "#64748b" }}>⏳ Đang tải...</div>}
                {error && <div style={{ padding: 14, borderRadius: 9, background: "rgba(239,68,68,0.1)", color: "#ef4444", marginBottom: 16 }}>❌ {error}</div>}
                {success && <div style={{ padding: 14, borderRadius: 9, background: "rgba(34,197,94,0.1)", color: "#22c55e", marginBottom: 16 }}>{success}</div>}

                {benefits && (
                    <>
                        {/* Health Insurance Card */}
                        <div style={{ background: "#1e293b", borderRadius: 16, border: "1px solid #334155", padding: "24px", marginBottom: 20 }}>
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                                <div>
                                    <div style={{ fontSize: 12, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 8 }}>🏥 Bảo Hiểm Sức Khỏe</div>
                                    <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                                        <span style={{ fontSize: 28, fontWeight: 800, color: PKG_COLOR[pkg ?? ""] || "#e2e8f0" }}>Gói {pkg}</span>
                                        <span style={{ padding: "4px 14px", borderRadius: 20, background: `${PKG_COLOR[pkg ?? ""]}22`, color: PKG_COLOR[pkg ?? ""] || "#94a3b8", fontSize: 12, fontWeight: 600 }}>{PKG_DESC[pkg ?? ""] || ""}</span>
                                    </div>
                                </div>
                                <button onClick={() => setShowChange(!showChange)}
                                    style={{ padding: "8px 18px", borderRadius: 8, background: "rgba(167,139,250,0.15)", border: "1px solid rgba(167,139,250,0.3)", color: "#a78bfa", fontSize: 13, fontWeight: 600, cursor: "pointer" }}>
                                    Đổi gói
                                </button>
                            </div>
                            {pkgInfo && (
                                <div style={{ marginTop: 16, display: "flex", gap: 32 }}>
                                    <div>
                                        <div style={{ fontSize: 12, color: "#64748b" }}>Công ty đóng</div>
                                        <div style={{ fontSize: 16, fontWeight: 700, color: "#22c55e" }}>{(pkgInfo.monthly_cost_company ?? 0).toLocaleString()}đ/tháng</div>
                                    </div>
                                    <div>
                                        <div style={{ fontSize: 12, color: "#64748b" }}>Nhân viên đóng</div>
                                        <div style={{ fontSize: 16, fontWeight: 700, color: "#60a5fa" }}>{(pkgInfo.monthly_cost_employee ?? 0).toLocaleString()}đ/tháng</div>
                                    </div>
                                    <div>
                                        <div style={{ fontSize: 12, color: "#64748b" }}>Bảo hiểm tối đa</div>
                                        <div style={{ fontSize: 16, fontWeight: 700, color: "#f59e0b" }}>{((pkgInfo.max_annual_coverage ?? 0) / 1_000_000).toFixed(0)}M đ/năm</div>
                                    </div>
                                </div>
                            )}
                            {pkgInfo?.coverage && (
                                <div style={{ marginTop: 12, display: "flex", gap: 8, flexWrap: "wrap" }}>
                                    {pkgInfo.coverage.map((c: string) => (
                                        <span key={c} style={{ padding: "3px 10px", borderRadius: 20, background: "rgba(34,197,94,0.1)", color: "#22c55e", fontSize: 12 }}>✓ {c}</span>
                                    ))}
                                </div>
                            )}
                        </div>

                        {showChange && (
                            <form onSubmit={handleChange} style={{ background: "#1e293b", borderRadius: 12, border: "1px solid #a78bfa33", padding: "20px", marginBottom: 20 }}>
                                <h4 style={{ margin: "0 0 14px", fontSize: 14, color: "#a78bfa" }}>Yêu Cầu Thay Đổi Phúc Lợi</h4>
                                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                                    <div>
                                        <label style={{ fontSize: 12, color: "#64748b", display: "block", marginBottom: 5 }}>Loại phúc lợi</label>
                                        <select value={changeForm.benefit_type} onChange={e => setChangeForm({ ...changeForm, benefit_type: e.target.value })}
                                            style={{ width: "100%", padding: "9px 10px", borderRadius: 7, background: "#0f172a", border: "1px solid #334155", color: "#e2e8f0", fontSize: 13 }}>
                                            {["health_insurance", "wfh_allowance", "transportation_allowance"].map(t => <option key={t}>{t}</option>)}
                                        </select>
                                    </div>
                                    <div>
                                        <label style={{ fontSize: 12, color: "#64748b", display: "block", marginBottom: 5 }}>Thay đổi yêu cầu</label>
                                        <input value={changeForm.requested_change} onChange={e => setChangeForm({ ...changeForm, requested_change: e.target.value })} required
                                            placeholder="VD: Upgrade từ Basic lên Standard"
                                            style={{ width: "100%", padding: "9px 10px", borderRadius: 7, background: "#0f172a", border: "1px solid #334155", color: "#e2e8f0", fontSize: 13, boxSizing: "border-box" }} />
                                    </div>
                                </div>
                                <button type="submit" style={{ marginTop: 14, padding: "10px 24px", borderRadius: 8, background: "linear-gradient(90deg,#a78bfa,#7c3aed)", border: "none", color: "white", fontWeight: 600, cursor: "pointer" }}>Gửi yêu cầu</button>
                            </form>
                        )}

                        {/* Other Benefits Grid */}
                        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(200px,1fr))", gap: 14, marginBottom: 24 }}>
                            {[
                                { icon: "🍱", label: "Phụ cấp ăn trưa", value: "40,000đ/ngày", active: benefits.meal_allowance },
                                { icon: "🚌", label: "Phụ cấp đi lại", value: benefits.transportation_allowance_tier, active: true },
                                { icon: "💻", label: "Phụ cấp WFH", value: "500,000đ/tháng", active: benefits.wfh_allowance },
                                { icon: "🏥", label: "Khám SK định kỳ", value: benefits.annual_checkup_done ? "Đã khám 2026" : "Chưa khám 2026", active: benefits.annual_checkup_done },
                            ].map(b => (
                                <div key={b.label} style={{ background: "#1e293b", borderRadius: 12, padding: "18px", border: `1px solid ${b.active ? "#334155" : "#1e293b"}`, opacity: b.active ? 1 : 0.55 }}>
                                    <div style={{ fontSize: 22, marginBottom: 8 }}>{b.icon}</div>
                                    <div style={{ fontSize: 12, color: "#64748b", marginBottom: 4 }}>{b.label}</div>
                                    <div style={{ fontSize: 14, fontWeight: 600, color: b.active ? "#e2e8f0" : "#475569" }}>{b.value}</div>
                                    <div style={{ marginTop: 8, fontSize: 11, color: b.active ? "#22c55e" : "#475569" }}>{b.active ? "✅ Đang hưởng" : "❌ Chưa đăng ký"}</div>
                                </div>
                            ))}
                        </div>

                        {/* Training Budget Progress */}
                        <div style={{ background: "#1e293b", borderRadius: 14, border: "1px solid #334155", padding: "20px 24px" }}>
                            <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 16 }}>📚 Ngân Sách Đào Tạo</div>
                            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, marginBottom: 10 }}>
                                <span style={{ color: "#64748b" }}>Đã sử dụng: <strong style={{ color: "#e2e8f0" }}>{((benefits.training_budget_used) / 1000).toFixed(0)}K đ</strong></span>
                                <span style={{ color: "#64748b" }}>Còn lại: <strong style={{ color: "#22c55e" }}>{((benefits.training_budget_remaining) / 1000).toFixed(0)}K đ</strong></span>
                            </div>
                            <div style={{ height: 10, background: "#0f172a", borderRadius: 99, overflow: "hidden" }}>
                                <div style={{ height: "100%", width: `${trainPct}%`, background: "linear-gradient(90deg,#a78bfa,#7c3aed)", borderRadius: 99, transition: "width 0.5s" }} />
                            </div>
                            <div style={{ fontSize: 12, color: "#64748b", marginTop: 6 }}>{trainPct}% đã dùng ({(trainTotal / 1000).toFixed(0)}K tổng)</div>
                        </div>

                        {/* Pending changes */}
                        {benefits.benefit_changes_pending.length > 0 && (
                            <div style={{ marginTop: 20, background: "#1e293b", borderRadius: 12, border: "1px solid #fbbf2433", padding: "18px 20px" }}>
                                <div style={{ fontSize: 14, fontWeight: 600, color: "#fbbf24", marginBottom: 12 }}>⏳ Yêu Cầu Đang Chờ Duyệt</div>
                                {benefits.benefit_changes_pending.map((p, i) => (
                                    <div key={i} style={{ fontSize: 13, color: "#94a3b8", padding: "8px 0", borderBottom: "1px solid #0f172a" }}>
                                        {p.type}: {p.from} → {p.to} · <span style={{ color: "#fbbf24" }}>{p.status}</span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
}
