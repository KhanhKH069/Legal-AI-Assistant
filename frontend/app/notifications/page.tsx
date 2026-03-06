"use client";
import React, { useState, useEffect } from "react";
import { getNotifications, getAnnouncements, HRNotification } from "@/lib/api";

const TYPE_ICON: Record<string, string> = {
    "Leave Approval": "🏖️", "Ticket Update": "🎫", "Announcement": "📢", "Payroll": "💰", "Benefits": "🎁"
};
const TYPE_COLOR: Record<string, string> = {
    "Leave Approval": "#22c55e", "Ticket Update": "#fb923c", "Announcement": "#60a5fa", "Payroll": "#f59e0b", "Benefits": "#a78bfa"
};

export default function NotificationsPage() {
    const [empId, setEmpId] = useState("EMP001");
    const [input, setInput] = useState("EMP001");
    const [notifs, setNotifs] = useState<HRNotification[]>([]);
    const [announcements, setAnnouncements] = useState<any[]>([]);
    const [unread, setUnread] = useState(0);
    const [loading, setLoading] = useState(false);
    const [tab, setTab] = useState<"personal" | "announcements">("personal");

    const load = async (id: string) => {
        setLoading(true);
        try {
            const [n, a] = await Promise.all([getNotifications(id), getAnnouncements()]);
            setNotifs(n.notifications);
            setUnread(n.unread);
            setAnnouncements(a.announcements);
        } catch { }
        finally { setLoading(false); }
    };

    useEffect(() => { load(empId); }, [empId]);

    const handleSearch = (e: React.FormEvent) => { e.preventDefault(); setEmpId(input.trim().toUpperCase()); };

    return (
        <div style={{ minHeight: "100vh", background: "linear-gradient(135deg,#0f172a 0%,#1e293b 100%)", color: "#e2e8f0", fontFamily: "'Inter',sans-serif", padding: "32px 24px" }}>
            <div style={{ maxWidth: 800, margin: "0 auto" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 32 }}>
                    <a href="/" style={{ color: "#94a3b8", textDecoration: "none", fontSize: 13 }}>← Trang chủ</a>
                    <div style={{ flex: 1 }}>
                        <h1 style={{ margin: 0, fontSize: 28, fontWeight: 700, background: "linear-gradient(90deg,#60a5fa,#3b82f6)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
                            🔔 Thông Báo HR
                        </h1>
                        <p style={{ margin: "4px 0 0", color: "#64748b", fontSize: 14 }}>Thông báo nội bộ và công bố từ HR</p>
                    </div>
                    {unread > 0 && (
                        <div style={{ padding: "6px 14px", borderRadius: 20, background: "rgba(239,68,68,0.15)", color: "#ef4444", fontSize: 13, fontWeight: 700 }}>
                            🔴 {unread} chưa đọc
                        </div>
                    )}
                </div>

                <form onSubmit={handleSearch} style={{ display: "flex", gap: 10, marginBottom: 24 }}>
                    <input value={input} onChange={e => setInput(e.target.value)} placeholder="Mã nhân viên (VD: EMP001)"
                        style={{ flex: 1, padding: "12px 16px", borderRadius: 10, background: "#1e293b", border: "1px solid #334155", color: "#e2e8f0", fontSize: 14, outline: "none" }} />
                    <button type="submit" style={{ padding: "12px 24px", borderRadius: 10, background: "linear-gradient(90deg,#60a5fa,#3b82f6)", border: "none", color: "white", fontWeight: 600, cursor: "pointer" }}>Xem</button>
                </form>

                {/* Tabs */}
                <div style={{ display: "flex", gap: 4, marginBottom: 20, background: "#1e293b", borderRadius: 10, padding: 4, border: "1px solid #334155" }}>
                    {(["personal", "announcements"] as const).map(t => (
                        <button key={t} onClick={() => setTab(t)}
                            style={{
                                flex: 1, padding: "10px", borderRadius: 7, border: "none", cursor: "pointer", fontWeight: 600, fontSize: 13, transition: "all 0.2s",
                                background: tab === t ? "linear-gradient(90deg,#60a5fa,#3b82f6)" : "transparent",
                                color: tab === t ? "white" : "#64748b"
                            }}>
                            {t === "personal" ? `🔔 Cá nhân (${notifs.length})` : `📢 Thông báo chung (${announcements.length})`}
                        </button>
                    ))}
                </div>

                {loading && <div style={{ textAlign: "center", padding: 40, color: "#64748b" }}>⏳ Đang tải...</div>}

                {tab === "personal" && (
                    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                        {notifs.length === 0 && !loading && <div style={{ textAlign: "center", padding: 40, color: "#475569" }}>Không có thông báo</div>}
                        {notifs.map(n => (
                            <div key={n.notification_id}
                                style={{
                                    background: "#1e293b", borderRadius: 12, padding: "18px 20px", border: `1px solid ${n.is_read ? "#334155" : "#3b82f644"}`,
                                    borderLeft: `4px solid ${n.is_read ? "#334155" : (TYPE_COLOR[n.type] || "#3b82f6")}`
                                }}>
                                <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
                                    <span style={{ fontSize: 20 }}>{TYPE_ICON[n.type] || "📌"}</span>
                                    <div style={{ flex: 1 }}>
                                        <div style={{ fontWeight: 600, fontSize: 14 }}>{n.title} {!n.is_read && <span style={{ marginLeft: 8, padding: "2px 8px", borderRadius: 20, background: "rgba(239,68,68,0.15)", color: "#ef4444", fontSize: 11 }}>Mới</span>}</div>
                                        <div style={{ fontSize: 12, color: "#64748b", marginTop: 2 }}>{n.type} · {n.created_at.slice(0, 10)}</div>
                                    </div>
                                </div>
                                <div style={{ fontSize: 13, color: "#94a3b8", lineHeight: 1.6 }}>{n.message}</div>
                            </div>
                        ))}
                    </div>
                )}

                {tab === "announcements" && (
                    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                        {announcements.length === 0 && !loading && <div style={{ textAlign: "center", padding: 40, color: "#475569" }}>Chưa có thông báo chung</div>}
                        {announcements.map(a => (
                            <div key={a.announcement_id} style={{ background: "#1e293b", borderRadius: 14, border: "1px solid #334155", overflow: "hidden" }}>
                                <div style={{ padding: "6px 20px", background: "rgba(96,165,250,0.1)", borderBottom: "1px solid #334155", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                                    <span style={{ fontSize: 12, color: "#60a5fa", fontWeight: 600 }}>📢 {a.department}</span>
                                    <span style={{ fontSize: 12, color: "#475569" }}>{a.published_at?.slice(0, 10)}</span>
                                </div>
                                <div style={{ padding: "18px 20px" }}>
                                    <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 10 }}>{a.title}</div>
                                    <div style={{ fontSize: 13, color: "#94a3b8", lineHeight: 1.7 }}>{a.content}</div>
                                    <div style={{ marginTop: 12, fontSize: 12, color: "#475569" }}>— {a.published_by}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
