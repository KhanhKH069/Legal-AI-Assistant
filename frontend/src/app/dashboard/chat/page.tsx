"use client";

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { sendChatStream, sendChat, approveAction, clearChatHistory, uploadCV } from '@/lib/api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  agent?: string;
  timestamp?: string;
  isStreaming?: boolean;
  requiresApproval?: boolean;
}

const SUGGESTED = [
  'Chính sách nghỉ phép của công ty như thế nào?',
  'Tôi còn bao nhiêu ngày nghỉ phép?',
  'Quy trình xin nghỉ phép ra sao?',
  'Lương tháng này của tôi là bao nhiêu?',
  'Chính sách bảo hiểm y tế thế nào?',
];

function TypingIndicator() {
  return (
    <div className="flex items-end gap-3">
      <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0"
        style={{ background: 'linear-gradient(135deg, #10b981, #059669)' }}>
        <svg width="14" height="14" fill="white" viewBox="0 0 24 24">
          <circle cx="12" cy="12" r="3"/><path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4"/>
        </svg>
      </div>
      <div className="chat-assistant px-4 py-3 flex items-center gap-1.5">
        <div className="typing-dot w-2 h-2 rounded-full bg-emerald-400" />
        <div className="typing-dot w-2 h-2 rounded-full bg-emerald-400" />
        <div className="typing-dot w-2 h-2 rounded-full bg-emerald-400" />
      </div>
    </div>
  );
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: 'Xin chào! Tôi là HR Assistant của Paraline. 🌿\n\nTôi có thể giúp bạn:\n• Tra cứu chính sách nhân sự\n• Xem thông tin cá nhân\n• Xin nghỉ phép\n• Kiểm tra lương & phúc lợi\n\nBạn cần hỗ trợ gì hôm nay?',
      timestamp: new Date().toISOString(),
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [user, setUser] = useState<{ name: string; employee_id: string; role?: string } | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const u = localStorage.getItem('current_user');
    if (u) setUser(JSON.parse(u));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const send = async (text: string) => {
    if (!text.trim() || loading || !user) return;
    const userMsg: Message = { role: 'user', content: text, timestamp: new Date().toISOString() };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    // Initial streaming message
    const streamId = Date.now().toString();
    setMessages(prev => [...prev, {
      role: 'assistant',
      content: '',
      isStreaming: true,
      timestamp: new Date().toISOString()
    }]);

    try {
      const res = await sendChatStream(text, user.employee_id, (token, intent) => {
        setMessages(prev => {
          const newMsgs = [...prev];
          const last = { ...newMsgs[newMsgs.length - 1] }; // Clone object to avoid React Strict Mode double mutation
          if (last.role === 'assistant' && last.isStreaming) {
            last.content += token;
            if (intent) last.agent = intent;
          }
          newMsgs[newMsgs.length - 1] = last;
          return newMsgs;
        });
      });

      if (res) {
        setMessages(prev => {
          const newMsgs = [...prev];
          const last = newMsgs[newMsgs.length - 1];
          if (last.role === 'assistant') {
            last.isStreaming = false;
            // Check if it's an approval request
            if (res.response?.includes('cần bạn xác nhận') || last.content.includes('cần bạn xác nhận')) {
              last.requiresApproval = true;
            }
          }
          return newMsgs;
        });
      }
    } catch (e) {
      setMessages(prev => {
        const newMsgs = [...prev];
        const last = newMsgs[newMsgs.length - 1];
        last.content = '❌ Không thể kết nối đến máy chủ. Vui lòng thử lại.';
        last.isStreaming = false;
        return newMsgs;
      });
    }
    setLoading(false);
  };

  const handleApprove = async (approve: boolean) => {
    if (!user) return;
    setLoading(true);
    setMessages(prev => {
      const newMsgs = [...prev];
      const last = newMsgs[newMsgs.length - 1];
      if (last.requiresApproval) {
        last.requiresApproval = false; // Hide buttons
      }
      return newMsgs;
    });

    const res = await approveAction(user.employee_id, approve);
    setLoading(false);

    if (res) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: res.response,
        agent: res.agent_name,
        timestamp: res.timestamp,
      }]);
    }
  };

  const handleClear = async () => {
    if (!user) return;
    await clearChatHistory(user.employee_id);
    setMessages([{
      role: 'assistant',
      content: 'Lịch sử trò chuyện đã được xóa. Bắt đầu cuộc hội thoại mới nhé! 🌿',
      timestamp: new Date().toISOString(),
    }]);
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setLoading(true);
    setMessages(prev => [...prev, {
      role: 'user',
      content: `📎 Tải lên: ${file.name}\nĐang tải...`,
      timestamp: new Date().toISOString(),
    }]);

    try {
      const res = await uploadCV(file);
      // Xóa message "Đang tải..." và thay bằng message thật
      setMessages(prev => {
        const msgs = [...prev];
        msgs.pop();
        return msgs;
      });
      // Gửi message yêu cầu phân tích CV vào chat
      send(`Tôi vừa tải lên file tài liệu/CV: ${res.cv_path}. Vui lòng giúp tôi phân tích hoặc xử lý.`);
    } catch (error) {
      setMessages(prev => {
        const msgs = [...prev];
        const last = msgs[msgs.length - 1];
        last.content = `❌ Tải lên thất bại: ${file.name}`;
        return msgs;
      });
      setLoading(false);
    }

    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div className="flex flex-col h-screen p-6" style={{ maxHeight: '100vh' }}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6 fade-in-up">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{ background: 'linear-gradient(135deg, #10b981, #059669)', boxShadow: '0 0 20px rgba(16,185,129,0.3)' }}>
            <svg width="18" height="18" fill="white" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="3"/><path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/>
            </svg>
          </div>
          <div>
            <h1 className="text-lg font-bold text-white">HR Assistant</h1>
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full bg-emerald-400" style={{ animation: 'pulse-glow 2s infinite' }} />
              <span className="text-xs text-emerald-400">8 Agents Online</span>
            </div>
          </div>
        </div>
        <button onClick={handleClear}
          className="flex items-center gap-2 px-3 py-2 rounded-xl text-xs text-slate-400 transition-colors hover:text-red-400"
          style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.07)' }}>
          <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6M10 11v6M14 11v6M9 6V4h6v2"/>
          </svg>
          Xóa lịch sử
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-2" style={{ minHeight: 0 }}>
        {messages.map((msg, i) => (
          <div key={i} className={`flex items-end gap-3 fade-in-up ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
            {msg.role === 'assistant' && (
              <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0"
                style={{ background: 'linear-gradient(135deg, #10b981, #059669)' }}>
                <svg width="14" height="14" fill="white" viewBox="0 0 24 24">
                  <circle cx="12" cy="12" r="3"/><path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4"/>
                </svg>
              </div>
            )}
            <div className={`max-w-[70%] ${msg.role === 'user' ? 'items-end' : 'items-start'} flex flex-col gap-1`}>
              {msg.agent && (
                <span className="text-xs px-2 py-0.5 rounded-full ml-1"
                  style={{ background: 'rgba(16,185,129,0.1)', color: '#10b981', border: '1px solid rgba(16,185,129,0.2)' }}>
                  {msg.agent}
                </span>
              )}
              <div className={`px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${msg.role === 'user' ? 'chat-user' : 'chat-assistant text-slate-200'}`}>
                {msg.content}
                {msg.isStreaming && <span className="inline-block w-1.5 h-3.5 bg-emerald-400 ml-1 animate-pulse" />}
              </div>

              {/* Interactive Approval Buttons */}
              {msg.requiresApproval && (user?.role === 'admin' || user?.role === 'manager') && (
                <div className="flex gap-2 mt-2">
                  <button onClick={() => handleApprove(true)}
                    className="px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all hover:scale-105"
                    style={{ background: 'rgba(16,185,129,0.15)', color: '#10b981', border: '1px solid rgba(16,185,129,0.3)' }}>
                    <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>
                    Duyệt Đơn
                  </button>
                  <button onClick={() => handleApprove(false)}
                    className="px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all hover:scale-105"
                    style={{ background: 'rgba(239,68,68,0.15)', color: '#f87171', border: '1px solid rgba(239,68,68,0.3)' }}>
                    <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                    Từ Chối
                  </button>
                </div>
              )}
              {msg.requiresApproval && user?.role === 'employee' && (
                <div className="mt-1 text-xs text-amber-400 flex items-center gap-1">
                  <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                  Đang chờ Quản lý duyệt
                </div>
              )}

              {msg.timestamp && !msg.isStreaming && (
                <span className="text-xs text-slate-600 px-1 mt-1">
                  {new Date(msg.timestamp).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })}
                </span>
              )}
            </div>
          </div>
        ))}
        {loading && !messages[messages.length - 1]?.isStreaming && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      {/* Suggestions */}
      {messages.length <= 2 && (
        <div className="py-3 flex gap-2 overflow-x-auto no-scrollbar">
          {SUGGESTED.map((s, i) => (
            <button key={i} onClick={() => send(s)}
              className="shrink-0 text-xs px-3 py-2 rounded-full transition-all hover:scale-105"
              style={{ background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.2)', color: '#6ee7b7', whiteSpace: 'nowrap' }}>
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="pt-4 border-t" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
        <form onSubmit={(e) => { e.preventDefault(); send(input); }}
          className="flex gap-3 items-end p-3 rounded-2xl"
          style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>

          {/* File Upload Button */}
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            className="hidden"
            accept=".pdf,.doc,.docx"
          />
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={loading}
            className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0 transition-all text-emerald-400 hover:bg-emerald-500/10"
          >
            <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path d="M12 5v14M5 12h14"/>
            </svg>
          </button>

          <textarea
            id="chat-input"
            ref={textareaRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(input); } }}
            placeholder="Nhập câu hỏi... (Enter để gửi, Shift+Enter xuống dòng)"
            rows={1}
            className="flex-1 px-2 py-2 text-sm resize-none bg-transparent outline-none text-white placeholder:text-slate-500"
            style={{ minHeight: '40px', maxHeight: '120px' }}
          />
          <button
            id="send-btn"
            type="submit"
            disabled={loading || !input.trim()}
            className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0 transition-all"
            style={{ opacity: (loading || !input.trim()) ? 0.3 : 1, background: '#10b981' }}>
            <svg width="18" height="18" fill="none" stroke="white" strokeWidth="2" viewBox="0 0 24 24">
              <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
            </svg>
          </button>
        </form>
      </div>
    </div>
  );
}
