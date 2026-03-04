"use client";

import React, { useState, useRef, useEffect } from "react";
import "../globals.css";
import { chat } from "../../lib/api";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type Message = { role: "user" | "assistant"; content: string };

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // You would typically get this from an auth context
  const userId = "demo-user";

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  async function handleSend() {
    if (!input.trim() || loading) return;
    const content = input.trim();
    setInput("");

    // Add user message
    setMessages((prev) => [...prev, { role: "user", content }]);
    setLoading(true);

    try {
      let res = { response: `Hệ thống phản hồi: ${content}` } as any;
      try {
        const apiRes = await chat({ user_id: userId, message: content });
        if (apiRes && apiRes.response) res = apiRes;
      } catch (err) {
        console.error("API Error:", err);
      }
      // Add assistant message
      setMessages((prev) => [...prev, { role: "assistant", content: res.response }]);
    } catch (e: any) {
      setMessages((prev) => [...prev, { role: "assistant", content: `Lỗi gọi API: ${e?.message ?? e}` }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #f0f4f8 0%, #e1e8ed 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px',
      fontFamily: "'Inter', 'Segoe UI', sans-serif"
    }}>

      <div style={{
        width: '100%',
        maxWidth: 800,
        background: '#ffffff',
        borderRadius: 24,
        boxShadow: '0 10px 40px -10px rgba(0,0,0,0.1)',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        height: '85vh'
      }}>

        {/* Header Streamlined */}
        <div style={{
          background: '#ffffff',
          padding: '24px 32px',
          borderBottom: '1px solid #f0f0f0',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexShrink: 0
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <div style={{
              width: 48,
              height: 48,
              background: 'linear-gradient(135deg, #2563eb 0%, #3b82f6 100%)',
              borderRadius: 14,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 4px 12px rgba(37, 99, 235, 0.2)',
            }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
              </svg>
            </div>
            <div>
              <h1 style={{ fontSize: 20, fontWeight: 700, color: '#1e293b', margin: 0 }}>Paraline HR Assistant</h1>
              <p style={{ fontSize: 13, color: '#64748b', margin: '4px 0 0 0' }}>Sẵn sàng giải đáp mọi thắc mắc Nhân sự</p>
            </div>
          </div>

          <a href="/apply" style={{
            padding: '10px 20px',
            borderRadius: 8,
            background: '#f1f5f9',
            color: '#334155',
            fontWeight: 600,
            fontSize: 14,
            textDecoration: 'none',
            transition: 'all 0.2s',
            border: '1px solid #e2e8f0'
          }}
            onMouseEnter={(e) => { e.currentTarget.style.background = '#e2e8f0'; }}
            onMouseLeave={(e) => { e.currentTarget.style.background = '#f1f5f9'; }}
          >
            Ứng tuyển ngay
          </a>
        </div>

        {/* Chat Area */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: '32px',
          display: 'flex',
          flexDirection: 'column',
          gap: '24px',
          background: '#f8fafc'
        }}>
          {messages.length === 0 && (
            <div style={{
              margin: 'auto',
              textAlign: 'center',
              color: '#94a3b8',
              maxWidth: 400
            }}>
              <div style={{
                width: 80, height: 80,
                background: '#f1f5f9',
                borderRadius: '50%',
                margin: '0 auto 20px',
                display: 'flex', alignItems: 'center', justifyContent: 'center'
              }}>
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#cbd5e1" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"></circle>
                  <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
                  <line x1="12" y1="17" x2="12.01" y2="17"></line>
                </svg>
              </div>
              <p style={{ fontSize: 16, lineHeight: 1.6 }}>Xin chào! Tôi có thể giúp bạn các vấn đề về chính sách, nghỉ phép, lương, lịch làm việc hoặc thủ tục Onboarding.</p>
            </div>
          )}

          {messages.map((m, i) => (
            <div key={i} style={{
              display: 'flex',
              justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start',
              padding: '0 10px'
            }}>
              <div className="message-bubble" style={{
                maxWidth: '85%',
                borderRadius: m.role === 'user' ? '20px 20px 4px 20px' : '20px 20px 20px 4px',
                padding: '16px 20px',
                fontSize: 15,
                lineHeight: 1.6,
                background: m.role === 'user' ? '#2563eb' : '#ffffff',
                color: m.role === 'user' ? '#ffffff' : '#334155',
                boxShadow: '0 2px 10px rgba(0,0,0,0.05)',
                border: m.role === 'assistant' ? '1px solid #e2e8f0' : 'none',
              }}>
                {m.role === 'assistant' ? (
                  <div className="markdown-container">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {m.content}
                    </ReactMarkdown>
                  </div>
                ) : (
                  m.content
                )}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div style={{
          borderTop: '1px solid #e2e8f0',
          padding: '24px 32px',
          background: '#ffffff',
          flexShrink: 0
        }}>
          <div style={{
            display: 'flex',
            gap: 12,
            background: '#f1f5f9',
            borderRadius: 16,
            padding: '8px 8px 8px 20px',
            border: '1px solid #e2e8f0',
            transition: 'border-color 0.2s, box-shadow 0.2s',
          }}
            onFocus={(e) => { e.currentTarget.style.borderColor = '#3b82f6'; e.currentTarget.style.boxShadow = '0 0 0 3px rgba(59, 130, 246, 0.1)'; }}
            onBlur={(e) => { e.currentTarget.style.borderColor = '#e2e8f0'; e.currentTarget.style.boxShadow = 'none'; }}
          >
            <input
              style={{
                flex: 1,
                background: 'transparent',
                border: 'none',
                outline: 'none',
                fontSize: 15,
                color: '#1e293b'
              }}
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Nhập câu hỏi tại đây..."
              onKeyDown={e => e.key === 'Enter' && handleSend()}
              disabled={loading}
            />
            <button
              onClick={handleSend}
              disabled={loading}
              style={{
                borderRadius: 12,
                background: loading ? '#94a3b8' : '#2563eb',
                color: '#fff',
                fontWeight: 600,
                fontSize: 14,
                padding: '0 24px',
                border: 'none',
                height: 44,
                cursor: loading ? 'not-allowed' : 'pointer',
                transition: 'background 0.2s',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 8
              }}
            >
              {loading ? (
                <>Đang xử lý...</>
              ) : (
                <>Gửi <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg></>
              )}
            </button>
          </div>
          <div style={{ textAlign: 'center', marginTop: 12, fontSize: 12, color: '#94a3b8' }}>
            Powered by LangGraph & Gemini AI
          </div>
        </div>

      </div>

      <style dangerouslySetInnerHTML={{
        __html: `
        .markdown-container h1,
        .markdown-container h2,
        .markdown-container h3 {
          margin-top: 0;
          margin-bottom: 12px;
          color: #1e293b;
        }
        .markdown-container p { margin-top: 0; margin-bottom: 12px; }
        .markdown-container p:last-child { margin-bottom: 0; }
        .markdown-container ul, .markdown-container ol {
          margin-top: 0;
          margin-bottom: 12px;
          padding-left: 24px;
        }
        .markdown-container li { margin-bottom: 6px; }
        .markdown-container code {
          background: #f1f5f9;
          padding: 2px 6px;
          borderRadius: 4px;
          fontSize: 85%;
          color: #db2777;
        }
        .markdown-container pre {
          background: #1e293b;
          color: #f8fafc;
          padding: 16px;
          borderRadius: 8px;
          overflow-x: auto;
          margin-bottom: 12px;
        }
        .markdown-container pre code {
          background: transparent;
          color: inherit;
          padding: 0;
        }
        .markdown-container table {
          border-collapse: collapse;
          width: 100%;
          margin-bottom: 12px;
        }
        .markdown-container th, .markdown-container td {
          border: 1px solid #e2e8f0;
          padding: 8px 12px;
          text-align: left;
        }
        .markdown-container th {
          background: #f8fafc;
          font-weight: 600;
        }
        ::-webkit-scrollbar {
          width: 8px;
        }
        ::-webkit-scrollbar-track {
          background: transparent;
        }
        ::-webkit-scrollbar-thumb {
          background: #cbd5e1;
          border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
          background: #94a3b8;
        }
      `}} />
    </div>
  );
}
