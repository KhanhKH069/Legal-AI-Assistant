'use client';

import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import mermaid from 'mermaid';

mermaid.initialize({
  startOnLoad: false,
  theme: 'dark',
  securityLevel: 'loose',
  fontFamily: 'Inter, sans-serif'
});

const MermaidRenderer = ({ chart }: { chart: string }) => {
  const [svg, setSvg] = useState<string>('');
  const id = useRef(`mermaid-${Math.random().toString(36).substr(2, 9)}`);

  useEffect(() => {
    if (chart) {
      mermaid.render(id.current, chart).then((result) => {
        setSvg(result.svg);
      }).catch((e) => {
        console.error("Mermaid syntax error", e);
      });
    }
  }, [chart]);

  return <div className="mermaid-graph my-4 p-4 rounded-xl bg-slate-900/80 border border-emerald-500/20 overflow-x-auto flex justify-center shadow-lg shadow-emerald-900/10" dangerouslySetInnerHTML={{ __html: svg }} />;
};

// --- Helper: Strip Markdown & Code blocks for TTS ---
const stripMarkdown = (text: string) => {
  if (!text) return '';
  let stripped = text.replace(/```[\s\S]*?```/g, ''); // Remove code blocks completely
  stripped = stripped.replace(/(\*\*|\*|_|#|>|\[|\]|\(|\))/g, ''); // Remove basic md symbols
  return stripped.trim();
};

const speakText = (text: string) => {
  if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
    window.speechSynthesis.cancel(); 
    const cleanText = stripMarkdown(text);
    if (!cleanText) return;
    
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = 'vi-VN';
    
    // Try to find a Vietnamese female voice
    const voices = window.speechSynthesis.getVoices();
    const viVoice = voices.find(v => v.lang.includes('vi') || v.name.includes('Vietnamese'));
    if (viVoice) {
      utterance.voice = viVoice;
    }
    
    utterance.rate = 1.1;
    window.speechSynthesis.speak(utterance);
  }
};

type Message = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  intent?: string;
};

type ReviewResult = {
  clause: string;
  analysis: string;
};

export default function LegalAssistant() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [isReviewing, setIsReviewing] = useState(false);
  const [reviewReport, setReviewReport] = useState<string>('');

  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<BlobPart[]>([]);

  const toggleRecording = async () => {
    if (isRecording) {
      if (mediaRecorderRef.current) {
        mediaRecorderRef.current.stop();
      }
      return;
    }
    
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const formData = new FormData();
        formData.append('file', audioBlob, 'recording.webm');
        
        setIsRecording(false);
        setIsTranscribing(true);
        try {
          const res = await fetch('http://localhost:8000/api/stt', {
            method: 'POST',
            body: formData,
          });
          if (res.ok) {
            const data = await res.json();
            setInput(prev => prev + (prev ? " " : "") + data.text);
          }
        } catch (e) {
          console.error("STT Error", e);
        } finally {
          setIsTranscribing(false);
        }
        
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error("Error accessing microphone", err);
      alert("Không thể truy cập Microphone. Vui lòng kiểm tra quyền.");
    }
  };
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, reviewReport]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const res = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: 'guest_legal', message: userMsg.content }),
      });
      const data = await res.json();
      const botMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.response || "Lỗi phản hồi",
        intent: data.agent_name
      };
      setMessages(prev => [...prev, botMsg]);
    } catch (error) {
      console.error(error);
      setMessages(prev => [...prev, { id: Date.now().toString(), role: 'assistant', content: '❌ Không thể kết nối tới server.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async () => {
    if (!file) return;
    setIsReviewing(true);
    setReviewReport('');
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const res = await fetch('http://localhost:8000/contract/review', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      if (data.status === 'success') {
         setReviewReport(data.result);
      } else {
         setReviewReport('❌ Lỗi: ' + (data.detail || 'Không thể thẩm định'));
      }
    } catch (error) {
       setReviewReport('❌ Không thể kết nối tới server thẩm định.');
    } finally {
      setIsReviewing(false);
    }
  };

  return (
    <div className="flex h-screen bg-[#0a0f1e] text-slate-200 font-sans overflow-hidden">
      
      {/* Sidebar: Thẩm định Hợp đồng */}
      <div className="w-1/3 max-w-sm border-r border-slate-800 bg-[#0d1424] flex flex-col">
        <div className="p-6 border-b border-slate-800">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-700 flex items-center justify-center glow">
               <svg width="20" height="20" fill="white" viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 2l5 5h-5V4zM6 20V4h5v7h7v9H6z"/></svg>
            </div>
            <h1 className="text-xl font-bold text-white">Thẩm định Hợp đồng</h1>
          </div>
          <p className="text-sm text-slate-400">Tải lên file hợp đồng (PDF) để AI phân tích rủi ro dựa trên Pháp điển.</p>
        </div>
        
        <div className="p-6 flex-1 overflow-y-auto">
          <div className="glass-card p-5 mb-6 border border-emerald-900/30">
            <label className="block text-sm font-medium text-slate-300 mb-3">
              Tệp tài liệu (.pdf)
            </label>
            <input 
              type="file" 
              accept=".pdf"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="block w-full text-sm text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-emerald-500/10 file:text-emerald-400 hover:file:bg-emerald-500/20 cursor-pointer"
            />
            <button 
              onClick={handleFileUpload}
              disabled={!file || isReviewing}
              className="mt-4 w-full py-2.5 rounded-xl text-sm font-semibold text-white transition-all bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed glow"
            >
              {isReviewing ? 'Đang phân tích...' : 'Bắt đầu Thẩm định'}
            </button>
          </div>
          
          {reviewReport && (
            <div className="fade-in-up">
              <h3 className="text-emerald-400 font-semibold mb-3 flex items-center gap-2">
                <svg width="18" height="18" fill="currentColor" viewBox="0 0 24 24"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
                Kết quả Phân tích
              </h3>
              <div className="prose prose-invert prose-sm max-w-none text-slate-300 bg-slate-900/50 p-4 rounded-xl border border-slate-800">
                {reviewReport.split('\n').map((line, i) => (
                  <p key={i} className="mb-2">{line.replace(/\*\*/g, '').replace(/_/g, '')}</p>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col relative"
        style={{ backgroundImage: 'radial-gradient(ellipse at center, rgba(16,185,129,0.03) 0%, transparent 70%)' }}>
        
        {/* Header */}
        <header className="h-16 border-b border-slate-800 bg-[#0a0f1e]/80 backdrop-blur-md flex items-center px-6 z-10">
           <h2 className="text-lg font-semibold text-white">Legal AI Assistant</h2>
           <span className="ml-3 px-2.5 py-1 rounded-full text-xs font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20">
             Pháp điển & Án lệ VN
           </span>
        </header>

        {/* Chat History */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 scroll-smooth">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center fade-in-up">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-slate-800 to-slate-700 flex items-center justify-center mb-4 shadow-xl">
                 <svg width="32" height="32" fill="white" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/></svg>
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">Trợ lý Pháp lý Thông minh</h2>
              <p className="text-slate-400 max-w-md">Hãy hỏi tôi bất kỳ câu hỏi nào về Luật dân sự, Luật doanh nghiệp, hoặc tình huống Án lệ thực tế tại Việt Nam.</p>
              
              <div className="mt-8 grid grid-cols-2 gap-4 max-w-xl">
                {["Thủ tục thành lập công ty TNHH", "Án lệ về tranh chấp đất đai", "Quy định về thời gian thử việc", "Phân chia tài sản khi ly hôn"].map(hint => (
                  <button key={hint} onClick={() => setInput(hint)} className="p-3 rounded-xl border border-slate-800 bg-slate-900/50 text-sm text-slate-300 hover:border-emerald-500/50 hover:bg-emerald-500/5 transition-all text-left">
                    "{hint}"
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map(msg => (
              <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} fade-in-up`}>
                <div className={`max-w-[80%] rounded-2xl p-5 ${msg.role === 'user' ? 'chat-user glow shadow-emerald-900/20' : 'chat-assistant'}`}>
                  {msg.intent && (
                    <div className="flex items-center gap-2 mb-2 text-xs font-semibold text-emerald-400 uppercase tracking-wider">
                      <svg width="14" height="14" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
                      {msg.intent}
                    </div>
                  )}
                  <div className="prose prose-invert max-w-none text-sm leading-relaxed whitespace-pre-wrap">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        a: ({ node, ...props }) => (
                          <a
                            {...props}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 px-2 py-0.5 mx-1 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/20 hover:border-emerald-500/60 transition-all font-medium no-underline glow"
                          >
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
                            {props.children}
                          </a>
                        ),
                        code: ({ className, children, ...props }: any) => {
                          const match = /language-(\w+)/.exec(className || '');
                          if (match && match[1] === 'mermaid') {
                            return <MermaidRenderer chart={String(children).replace(/\n$/, '')} />;
                          }
                          return (
                            <code className={className} {...props}>
                              {children}
                            </code>
                          );
                        }
                      }}
                    >
                      {msg.content}
                    </ReactMarkdown>
                    
                    {msg.role === 'assistant' && (
                      <div className="flex justify-start mt-3">
                        <button
                          type="button"
                          onClick={() => speakText(msg.content)}
                          className="flex items-center gap-1.5 text-xs font-medium text-slate-400 hover:text-emerald-400 transition-colors bg-slate-800/50 hover:bg-slate-700 px-2 py-1 rounded-md border border-slate-700/50"
                          title="Đọc văn bản"
                        >
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path></svg>
                          Nghe AI đọc
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
          {isLoading && (
            <div className="flex justify-start fade-in-up">
              <div className="chat-assistant rounded-2xl p-5 flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full bg-emerald-500 typing-dot"></div>
                <div className="w-2 h-2 rounded-full bg-emerald-500 typing-dot"></div>
                <div className="w-2 h-2 rounded-full bg-emerald-500 typing-dot"></div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 bg-[#0a0f1e]/80 backdrop-blur-md border-t border-slate-800 z-10">
          <form onSubmit={handleSendMessage} className="max-w-4xl mx-auto relative">
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder={isTranscribing ? "Đang nhận diện giọng nói..." : isRecording ? "Đang ghi âm... (Bấm Mic để dừng)" : "Nhập câu hỏi pháp lý của bạn..."}
              disabled={isLoading || isTranscribing}
              className="w-full bg-[#1e293b]/50 border border-slate-700 text-slate-100 rounded-full pl-6 pr-28 py-4 text-sm focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all shadow-inner"
            />
            
            <button
              type="button"
              onClick={toggleRecording}
              disabled={isLoading || isTranscribing}
              className={`absolute right-14 top-2 bottom-2 w-10 h-10 rounded-full flex items-center justify-center transition-colors ${
                isRecording 
                  ? "bg-red-500/20 text-red-500 hover:bg-red-500/30 animate-pulse" 
                  : "bg-slate-700/50 text-slate-300 hover:bg-slate-600 hover:text-emerald-400"
              }`}
            >
              <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 1v11m0 0a3 3 0 01-3-3V4a3 3 0 116 0v5a3 3 0 01-3 3z" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 10v2a7 7 0 01-14 0v-2m7 9v3m-3 0h6" />
              </svg>
            </button>
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="absolute right-2 top-2 bottom-2 w-10 h-10 rounded-full bg-emerald-600 hover:bg-emerald-500 flex items-center justify-center text-white disabled:opacity-50 disabled:bg-slate-600 transition-colors shadow-lg shadow-emerald-900/50"
            >
              <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/></svg>
            </button>
          </form>
          <div className="text-center mt-2 text-[10px] text-slate-500">
            AI có thể mắc lỗi. Vui lòng kiểm tra lại thông tin với luật sư thực tế trước khi đưa ra quyết định.
          </div>
        </div>

      </div>
    </div>
  );
}
