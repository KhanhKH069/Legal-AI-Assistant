"use client";

import React, { useState } from "react";
import "../globals.css";
import { chat } from "../../lib/api";

type Message = { role: "user" | "assistant"; content: string };


export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const userId = "demo-user";

  async function handleSend() {
    if (!input.trim() || loading) return;
    const content = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content }]);
    setLoading(true);
    try {
      let res = { response: `Echo: ${content}` } as any;
      try {
        const apiRes = await chat({ user_id: userId, message: content });
        if (apiRes && apiRes.response) res = apiRes;
      } catch (_) {}
      setMessages((prev) => [...prev, { role: "assistant", content: res.response }]);
    } catch (e: any) {
      setMessages((prev) => [...prev, { role: "assistant", content: `Lỗi gọi API: ${e?.message ?? e}` }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ minHeight: '100vh', background: '#f5f7fa', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: 32 }}>
        <div style={{
          width: 90,
          height: 90,
          background: 'linear-gradient(135deg, #27ae60 60%, #1e8449 100%)',
          borderRadius: '50%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 4px 32px 0 rgba(39,174,96,0.18)',
          marginBottom: 18,
          border: '4px solid #fff',
        }}>
          <svg width="54" height="54" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <rect x="2" y="7" width="20" height="10" rx="5" fill="#27ae60" stroke="#fff" strokeWidth="2.5"/>
            <path d="M7 17v2a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2v-2" stroke="#fff" strokeWidth="2.5"/>
            <circle cx="12" cy="12" r="3" fill="#fff"/>
          </svg>
        </div>
        <h1 style={{ fontSize: 32, fontWeight: 700, color: '#222', marginBottom: 6, letterSpacing: 1 }}>Paraline HR Assistant</h1>
        <div style={{ color: '#666', fontSize: 16, marginBottom: 8, textAlign: 'center', maxWidth: 420 }}>
          Hỏi về chính sách nghỉ phép, lương, giờ làm việc, onboarding hoặc screening CV.<br />Hệ thống multi-agent sẽ tự động route câu hỏi của bạn.
        </div>
        <a href="/apply" style={{
          marginTop: 18,
          display: 'inline-block',
          padding: '12px 32px',
          borderRadius: 10,
          background: 'linear-gradient(135deg, #27ae60 60%, #1e8449 100%)',
          color: '#fff',
          fontWeight: 700,
          fontSize: 17,
          boxShadow: '0 2px 12px 0 rgba(39,174,96,0.12)',
          textDecoration: 'none',
          letterSpacing: 1,
          transition: 'background 0.2s',
        }}>Ứng tuyển ngay</a>
      </div>
      <div style={{ width: '100%', maxWidth: 520, background: '#fff', borderRadius: 18, boxShadow: '0 2px 16px 0 rgba(44,62,80,0.08)', padding: 0, border: '1px solid #e0e0e0' }}>
        <div style={{ height: 340, overflowY: 'auto', padding: '24px 24px 0 24px', borderRadius: 18 }}>
          {messages.length === 0 && (
            <div style={{ color: '#aaa', fontSize: 15, textAlign: 'center', marginTop: 60 }}>
               Xin chào, hãy đặt câu hỏi đầu tiên của bạn về HR (VD: "Nghỉ phép mấy ngày mỗi năm?", "Thời gian thử việc bao lâu?")
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} style={{ display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start', marginBottom: 12 }}>
              <span style={{
                display: 'inline-block',
                maxWidth: '80%',
                borderRadius: 12,
                padding: '10px 16px',
                fontSize: 15,
                background: m.role === 'user' ? '#27ae60' : '#f5f5f5',
                color: m.role === 'user' ? '#fff' : '#222',
                boxShadow: m.role === 'user' ? '0 2px 8px 0 rgba(39,174,96,0.08)' : 'none',
                border: m.role === 'assistant' ? '1px solid #e0e0e0' : 'none',
              }}>
                {m.content}
              </span>
            </div>
          ))}
        </div>
        <div style={{ display: 'flex', gap: 8, borderTop: '1px solid #f0f0f0', padding: 20, background: '#fafbfc', borderRadius: '0 0 18px 18px' }}>
          <input
            style={{ flex: 1, borderRadius: 8, border: '1px solid #e0e0e0', padding: '12px 16px', fontSize: 15, outline: 'none' }}
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="Nhập câu hỏi..."
            onKeyDown={e => e.key === 'Enter' && handleSend()}
            disabled={loading}
          />
          <button
            onClick={handleSend}
            disabled={loading}
            style={{ borderRadius: 8, background: '#27ae60', color: '#fff', fontWeight: 600, fontSize: 15, padding: '0 28px', border: 'none', height: 44, boxShadow: '0 2px 8px 0 rgba(39,174,96,0.08)', cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.7 : 1 }}
          >
            {loading ? 'Đang gửi...' : 'Gửi'}
          </button>
        </div>
      </div>
    </div>
  );
}

