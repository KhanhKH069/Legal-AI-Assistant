"use client";
import React, { useState, useEffect } from "react";
import { getNotifications, getAnnouncements } from "@/lib/api";

const MODULES = [
    {
        href: "/chat",
        icon: "🤖",
        title: "AI Chatbot",
        desc: "Hỏi đáp thông minh về HR, chính sách, onboarding",
        gradient: "linear-gradient(135deg,#22c55e,#16a34a)",
        badge: null,
    },
    {
        href: "/attendance",
        icon: "🕐",
        title: "Chấm Công",
        desc: "Xem giờ làm, OT, nộp đơn nghỉ phép",
        gradient: "linear-gradient(135deg,#10b981,#059669)",
        badge: null,
    },
    {
        href: "/helpdesk",
        icon: "🎫",
        title: "HR Helpdesk",
        desc: "Tạo & theo dõi ticket hỗ trợ HR",
        gradient: "linear-gradient(135deg,#fb923c,#ea580c)",
        badge: null,
    },
    {
        href: "/benefits",
        icon: "🎁",
        title: "Phúc Lợi",
        desc: "Bảo hiểm, phụ cấp, đào tạo",
        gradient: "linear-gradient(135deg,#a78bfa,#7c3aed)",
        badge: null,
    },
    {
        href: "/notifications",
        icon: "🔔",
        title: "Thông Báo",
        desc: "Thông báo nội bộ và công bố từ HR",
        gradient: "linear-gradient(135deg,#60a5fa,#2563eb)",
        badge: "unread",
    },
    {
        href: "/hr-dashboard",
        icon: "📊",
        title: "HR Dashboard",
        desc: "Báo cáo, KPIs và analytics tổng hợp",
        gradient: "linear-gradient(135deg,#f59e0b,#d97706)",
        badge: null,
    },
    {
        href: "/apply",
        icon: "💼",
        title: "Tuyển Dụng",
        desc: "Nộp CV và quản lý ứng viên",
        gradient: "linear-gradient(135deg,#ec4899,#be185d)",
        badge: null,
    },
];

export default function PortalPage() {
    const [unread, setUnread] = useState(0);
    const [announcements, setAnnouncements] = useState<any[]>([]);

    useEffect(() => {
        getNotifications("EMP001").then((n: { unread: number; notifications: any[] }) => setUnread(n.unread)).catch(() => { });
        getAnnouncements().then((a: { announcements: any[] }) => setAnnouncements(a.announcements.slice(0, 3))).catch(() => { });
    }, []);

    return (
        <div style={{
            minHeight: "100vh",
            background: "linear-gradient(135deg,#0f172a 0%,#1e293b 60%,#0f172a 100%)",
            color: "#e2e8f0",
            fontFamily: "'Inter',system-ui,sans-serif",
        }}>
            {/* Top Nav */}
            <nav style={{ padding: "20px 32px", display: "flex", alignItems: "center", justifyContent: "space-between", borderBottom: "1px solid #1e293b" }}>
                <div style={{ fontSize: 22, fontWeight: 800, letterSpacing: "3px" }}>
                    Para<span style={{ color: "#22c55e" }}>line</span>
                    <span style={{ marginLeft: 10, fontSize: 12, fontWeight: 500, letterSpacing: "1px", color: "#64748b", background: "rgba(34,197,94,0.1)", padding: "3px 10px", borderRadius: 20 }}>HR Portal</span>
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                    <a href="/chat" style={{ padding: "8px 18px", borderRadius: 8, background: "rgba(34,197,94,0.1)", color: "#22c55e", fontSize: 13, fontWeight: 600, textDecoration: "none", border: "1px solid rgba(34,197,94,0.2)" }}>
                        💬 Chat với AI
                    </a>
                </div>
            </nav>

            <div style={{ maxWidth: 1100, margin: "0 auto", padding: "48px 32px" }}>
                {/* Hero */}
                <div style={{ textAlign: "center", marginBottom: 56 }}>
                    <div style={{ display: "inline-block", padding: "6px 16px", borderRadius: 20, background: "rgba(34,197,94,0.1)", color: "#22c55e", fontSize: 13, fontWeight: 600, marginBottom: 20, border: "1px solid rgba(34,197,94,0.2)" }}>
                        🚀 Paraline HR AI Platform — Powered by Gemini
                    </div>
                    <h1 style={{ fontSize: 48, fontWeight: 800, margin: "0 0 16px", lineHeight: 1.15 }}>
                        HR Portal{" "}
                        <span style={{ background: "linear-gradient(90deg,#22c55e,#60a5fa,#a78bfa)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
                            Tất cả trong một
                        </span>
                    </h1>
                    <p style={{ fontSize: 18, color: "#64748b", maxWidth: 500, margin: "0 auto" }}>
                        Quản lý chấm công, phúc lợi, helpdesk và nhiều hơn nữa — ngay trong một nền tảng duy nhất.
                    </p>
                </div>

                {/* Module Grid */}
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(280px,1fr))", gap: 20, marginBottom: 48 }}>
                    {MODULES.map(mod => (
                        <a key={mod.href} href={mod.href} style={{ textDecoration: "none" }}>
                            <div style={{
                                background: "#1e293b",
                                borderRadius: 18,
                                padding: "28px 24px",
                                border: "1px solid #334155",
                                cursor: "pointer",
                                transition: "all 0.25s",
                                position: "relative",
                                overflow: "hidden",
                            }}
                                onMouseEnter={e => {
                                    const el = e.currentTarget as HTMLDivElement;
                                    el.style.transform = "translateY(-4px)";
                                    el.style.borderColor = "#475569";
                                    el.style.boxShadow = "0 20px 40px rgba(0,0,0,0.3)";
                                }}
                                onMouseLeave={e => {
                                    const el = e.currentTarget as HTMLDivElement;
                                    el.style.transform = "";
                                    el.style.borderColor = "#334155";
                                    el.style.boxShadow = "";
                                }}
                            >
                                {/* Gradient accent */}
                                <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 3, background: mod.gradient }} />

                                <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 16 }}>
                                    <div style={{
                                        width: 52, height: 52, borderRadius: 14, display: "flex", alignItems: "center", justifyContent: "center",
                                        fontSize: 24, background: mod.gradient + "33",
                                    }}>
                                        {mod.icon}
                                    </div>
                                    {mod.badge === "unread" && unread > 0 && (
                                        <span style={{ padding: "3px 10px", borderRadius: 20, background: "rgba(239,68,68,0.15)", color: "#ef4444", fontSize: 12, fontWeight: 700 }}>
                                            {unread} mới
                                        </span>
                                    )}
                                </div>

                                <div style={{ fontSize: 17, fontWeight: 700, marginBottom: 8, color: "#f1f5f9" }}>{mod.title}</div>
                                <div style={{ fontSize: 13, color: "#64748b", lineHeight: 1.6 }}>{mod.desc}</div>

                                <div style={{ marginTop: 20, fontSize: 12, fontWeight: 600, display: "flex", alignItems: "center", gap: 6 }}>
                                    <span style={{ background: mod.gradient, WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>Mở →</span>
                                </div>
                            </div>
                        </a>
                    ))}
                </div>

                {/* Recent Announcements */}
                {announcements.length > 0 && (
                    <div>
                        <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 20 }}>📢 Thông Báo Gần Đây</h2>
                        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                            {announcements.map(a => (
                                <div key={a.announcement_id} style={{ background: "#1e293b", borderRadius: 12, padding: "18px 22px", border: "1px solid #334155", display: "flex", gap: 16, alignItems: "flex-start" }}>
                                    <div style={{ width: 40, height: 40, borderRadius: 10, background: "rgba(96,165,250,0.1)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18, flexShrink: 0 }}>📢</div>
                                    <div>
                                        <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 4 }}>{a.title}</div>
                                        <div style={{ fontSize: 13, color: "#94a3b8", lineHeight: 1.6, marginBottom: 6 }}>{a.content.slice(0, 120)}...</div>
                                        <div style={{ fontSize: 11, color: "#475569" }}>{a.department} · {a.published_at?.slice(0, 10)}</div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
