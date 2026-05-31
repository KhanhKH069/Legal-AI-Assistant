'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { sendGuestChatStream, uploadCV } from '@/lib/api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  isStreaming?: boolean;
  timestamp?: string;
}

const GUEST_SUGGESTIONS = [
  '💼 Công ty đang tuyển vị trí nào?',
  '📋 Yêu cầu cho vị trí Frontend Developer - Junior?',
  '🗓️ Quy trình phỏng vấn gồm mấy vòng?',
  '🏢 Văn hóa và môi trường làm việc ở Paraline như thế nào?',
  '🎁 Paraline có những phúc lợi gì?',
  '📄 Tôi muốn nộp CV ứng tuyển',
];

const BASE_ROLES = [
  'Software Engineer', 'Frontend Developer', 'Backend Developer',
  'QA Engineer', 'Project Manager', 'Business Analyst',
  'HR Specialist', 'AI Engineer', 'DevOps Engineer'
];
const LEVELS = ['Intern', 'Fresher', 'Junior', 'Middle', 'Senior', 'Expert'];
const ALL_POSITIONS = BASE_ROLES.flatMap(role => LEVELS.map(level => `${role} - ${level}`));

const WELCOME_MSG: Message = {
  role: 'assistant',
  content: `👋 Xin chào! Tôi là **AI Tuyển Dụng** của Paraline Vietnam.

Tôi có thể giúp bạn:
• 💼 Tìm hiểu các **vị trí đang tuyển dụng**
• 📋 Giải thích **yêu cầu công việc** (JD)
• 🗓️ Hướng dẫn **quy trình phỏng vấn**
• 🏢 Giới thiệu **văn hóa công ty**
• 🎁 Thông tin về **phúc lợi tổng quan**

Hãy đặt câu hỏi ngay, hoặc chọn một gợi ý bên dưới!`,
  timestamp: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
};

export default function GuestChatPage() {
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([WELCOME_MSG]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState('guest_anonymous');
  const [selectedPosition, setSelectedPosition] = useState('Chưa xác định');
  const [mounted, setMounted] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setMounted(true);
    const sid = localStorage.getItem('guest_session_id') || `guest_${Date.now()}`;
    setSessionId(sid);
    localStorage.setItem('guest_session_id', sid);
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const send = async (text: string) => {
    if (!text.trim() || loading) return;
    const now = new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });

    setMessages(prev => [...prev, { role: 'user', content: text.trim(), timestamp: now }]);
    setInput('');
    setLoading(true);

    // Placeholder streaming message
    setMessages(prev => [...prev, {
      role: 'assistant',
      content: '',
      isStreaming: true,
      timestamp: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
    }]);

    try {
      await sendGuestChatStream(text.trim(), sessionId, (token) => {
        setMessages(prev => {
          const msgs = [...prev];
          const last = msgs[msgs.length - 1];
          if (last.role === 'assistant') {
            msgs[msgs.length - 1] = { ...last, content: last.content + token };
          }
          return msgs;
        });
      });
    } catch {
      setMessages(prev => {
        const msgs = [...prev];
        const last = msgs[msgs.length - 1];
        if (last.role === 'assistant') {
          last.content = '❌ Không thể kết nối. Vui lòng thử lại hoặc liên hệ hr@paraline.vn';
        }
        return msgs;
      });
    } finally {
      setMessages(prev => {
        const msgs = [...prev];
        const last = msgs[msgs.length - 1];
        if (last.role === 'assistant') last.isStreaming = false;
        return msgs;
      });
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send(input);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const isImage = file.type.startsWith('image/');

    setLoading(true);
    setMessages(prev => [...prev, {
      role: 'user',
      content: `📎 Tải lên: ${file.name}\nĐang tải...`,
      timestamp: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
    }]);

    try {
      const res = await uploadCV(file);
      // Xóa message "Đang tải..." và thay bằng message thật
      setMessages(prev => {
        const msgs = [...prev];
        msgs.pop();
        return msgs;
      });

      if (isImage) {
        // Gửi message yêu cầu OCR thẻ cư trú / CCCD
        send(`Tôi vừa tải lên ảnh thẻ cư trú / CCCD tại đường dẫn: ${res.cv_path}. Vui lòng trích xuất thông tin từ thẻ này giúp tôi.`);
      } else {
        // Gửi message yêu cầu phân tích CV vào chat
        const positionText = selectedPosition === "Chưa xác định" ? "" : ` cho vị trí ${selectedPosition}`;
        send(`Tôi vừa tải lên file CV: ${res.cv_path}. Vui lòng đánh giá mức độ phù hợp của tôi${positionText}.`);
      }
    } catch (error) {
      setMessages(prev => {
        const msgs = [...prev];
        const last = msgs[msgs.length - 1];
        last.content = `❌ Tải lên thất bại: ${file.name}`;
        return msgs;
      });
      setLoading(false);
    }

    // Reset input
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  if (!mounted) return null;

  return (
    <div className="min-h-screen flex flex-col" style={{ background: 'radial-gradient(ellipse at 50% 0%, #130a2a 0%, #0a0f1e 60%)' }}>
      {/* Background orbs */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
        <div className="absolute w-96 h-96 rounded-full opacity-10 blur-3xl animate-blob"
          style={{ background: 'radial-gradient(circle, #8b5cf6, transparent)', top: '-5%', right: '5%' }} />
        <div className="absolute w-80 h-80 rounded-full opacity-10 blur-3xl animate-blob"
          style={{ background: 'radial-gradient(circle, #a78bfa, transparent)', bottom: '10%', left: '5%', animationDelay: '-10s' }} />
      </div>

      {/* Header */}
      <header className="sticky top-0 z-20 flex items-center justify-between px-6 py-4"
        style={{ background: 'rgba(10,15,30,0.8)', backdropFilter: 'blur(12px)', borderBottom: '1px solid rgba(139,92,246,0.15)' }}>
        <div className="flex items-center gap-3">
          {/* Logo */}
          <div className="w-9 h-9 rounded-xl flex items-center justify-center"
            style={{ background: 'linear-gradient(135deg, #8b5cf6, #7c3aed)', boxShadow: '0 0 16px rgba(139,92,246,0.4)' }}>
            <svg width="16" height="16" fill="white" viewBox="0 0 24 24">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
            </svg>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-white text-sm">Para<span className="text-purple-400">line</span></span>
              <span className="text-xs px-2 py-0.5 rounded-full font-medium"
                style={{ background: 'rgba(139,92,246,0.15)', color: '#a78bfa', border: '1px solid rgba(139,92,246,0.3)' }}>
                Cổng Ứng Viên
              </span>
            </div>
            <p className="text-xs text-slate-500">AI Tuyển Dụng · Hỗ trợ 24/7</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs text-purple-400">
            <span className="w-2 h-2 rounded-full bg-purple-400 animate-pulse" />
            Online
          </div>
          <button
            onClick={() => router.push('/')}
            className="text-xs px-3 py-1.5 rounded-lg transition-colors text-slate-400 hover:text-white"
            style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}>
            Đăng nhập Nhân viên →
          </button>
        </div>
      </header>

      {/* Info banner */}
      <div className="px-6 py-3 text-center text-xs"
        style={{ background: 'rgba(139,92,246,0.06)', borderBottom: '1px solid rgba(139,92,246,0.1)', color: '#c4b5fd' }}>
        👤 Bạn đang dùng với tư cách <strong>Khách / Ứng viên</strong> — Chỉ hỗ trợ câu hỏi về tuyển dụng & công ty.
        Nhân viên nội bộ vui lòng{' '}
        <button onClick={() => router.push('/')} className="underline font-medium hover:text-purple-300">
          đăng nhập tại đây
        </button>.
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-5 max-w-3xl mx-auto w-full">
        {messages.map((msg, i) => (
          <div key={i} className={`flex items-end gap-3 fade-in-up ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
            {msg.role === 'assistant' && (
              <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0"
                style={{ background: 'linear-gradient(135deg, #8b5cf6, #7c3aed)' }}>
                <svg width="14" height="14" fill="white" viewBox="0 0 24 24">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
                </svg>
              </div>
            )}
            <div className={`max-w-[75%] flex flex-col gap-1 ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
              <div className={`px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap rounded-2xl ${
                msg.role === 'user'
                  ? 'text-white rounded-br-sm'
                  : 'text-slate-200 rounded-bl-sm'
              }`}
                style={msg.role === 'user'
                  ? { background: 'linear-gradient(135deg, #7c3aed, #6d28d9)', boxShadow: '0 2px 12px rgba(124,58,237,0.3)' }
                  : { background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(139,92,246,0.15)' }
                }>
                {msg.content}
                {msg.isStreaming && <span className="inline-block w-1.5 h-3.5 bg-purple-400 ml-1 animate-pulse" />}
              </div>
              {msg.timestamp && (
                <span className="text-xs text-slate-600 px-1">{msg.timestamp}</span>
              )}
            </div>
          </div>
        ))}

        {/* Suggestions */}
        {messages.length <= 2 && !loading && (
          <div className="mt-4">
            <p className="text-xs text-slate-500 mb-3 text-center">💡 Gợi ý câu hỏi:</p>
            <div className="flex flex-wrap gap-2 justify-center">
              {GUEST_SUGGESTIONS.map((s, i) => (
                <button key={i} onClick={() => send(s.replace(/^[^\s]+\s/, ''))}
                  className="text-xs px-3 py-2 rounded-xl transition-all hover:scale-105"
                  style={{ background: 'rgba(139,92,246,0.1)', border: '1px solid rgba(139,92,246,0.25)', color: '#c4b5fd' }}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div className="sticky bottom-0 px-4 pb-6 pt-3 max-w-3xl mx-auto w-full flex flex-col gap-2">

        {/* Vị trí ứng tuyển dropdown */}
        <div className="flex items-center gap-2 px-1">
          <span className="text-xs font-medium" style={{ color: '#a78bfa' }}>Ứng tuyển vị trí:</span>
          <select
            value={selectedPosition}
            onChange={(e) => setSelectedPosition(e.target.value)}
            className="text-xs outline-none cursor-pointer rounded px-2 py-1 transition-colors"
            style={{
              background: 'rgba(139,92,246,0.1)',
              color: '#e2e8f0',
              border: '1px solid rgba(139,92,246,0.3)'
            }}
          >
            <option value="Chưa xác định" className="bg-slate-900">Chưa rõ / Nhờ tư vấn</option>
            {ALL_POSITIONS.map(pos => (
              <option key={pos} value={pos} className="bg-slate-900">{pos}</option>
            ))}
          </select>
        </div>

        <div className="flex items-end gap-3 p-3 rounded-2xl"
          style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(139,92,246,0.2)', backdropFilter: 'blur(12px)' }}>

          {/* File Upload Button */}
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            className="hidden"
            accept=".pdf,.doc,.docx,.png,.jpg,.jpeg"
          />
          <div className="flex flex-col items-center gap-0.5">
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={loading}
              className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0 transition-all text-purple-300 hover:bg-purple-900/30"
              style={{ border: '1px solid rgba(139,92,246,0.2)' }}
              title="Tải lên CV (PDF) hoặc Thẻ cư trú (Ảnh)"
            >
              <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path d="M12 5v14M5 12h14"/>
              </svg>
            </button>
            <span className="text-slate-500" style={{ fontSize: '9px', lineHeight: '1.2', textAlign: 'center', whiteSpace: 'nowrap' }}>CV / Thẻ</span>
          </div>

          <textarea
            ref={textareaRef}
            rows={1}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Hỏi về vị trí tuyển dụng, quy trình phỏng vấn, văn hóa công ty..."
            disabled={loading}
            className="flex-1 bg-transparent text-sm text-white placeholder-slate-500 resize-none outline-none leading-relaxed"
            style={{ maxHeight: '120px' }}
          />
          <button
            id="guest-send-btn"
            onClick={() => send(input)}
            disabled={loading || !input.trim()}
            className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0 transition-all"
            style={{
              background: loading || !input.trim() ? 'rgba(139,92,246,0.2)' : 'linear-gradient(135deg, #8b5cf6, #7c3aed)',
              opacity: loading || !input.trim() ? 0.5 : 1,
            }}>
            {loading
              ? <svg className="animate-spin w-4 h-4 text-purple-300" fill="none" viewBox="0 0 24 24">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" className="opacity-25"/>
                  <path fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" className="opacity-75"/>
                </svg>
              : <svg width="16" height="16" fill="none" stroke="white" strokeWidth="2" viewBox="0 0 24 24">
                  <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
                </svg>
            }
          </button>
        </div>
        <p className="text-center text-xs text-slate-600 mt-2">
          Enter để gửi · Shift+Enter để xuống dòng · Liên hệ: hr@paraline.vn
        </p>
      </div>
    </div>
  );
}
