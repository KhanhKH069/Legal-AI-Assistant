'use client';

import { useEffect, useState } from 'react';
import { getApplicants, getScreeningResults, runScreening } from '@/lib/api';

export default function RecruitmentPage() {
  const [applicants, setApplicants] = useState<any[]>([]);
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [statusText, setStatusText] = useState('');
  const [error, setError] = useState('');

  const loadData = async () => {
    setLoading(true);
    const [apps, res] = await Promise.all([getApplicants(), getScreeningResults()]);
    if (apps) setApplicants(apps);
    if (res) setResults(res);
    setLoading(false);
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRunScreening = async () => {
    setRunning(true);
    setProgress(0);
    setStatusText('Đang khởi động AI engine...');
    setError('');

    // Connect to WebSocket for real-time progress
    const ws = new WebSocket('ws://127.0.0.1:8000/screening/ws/progress');

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.message) setStatusText(data.message);
        if (data.progress !== undefined) setProgress(data.progress);

        if (data.done) {
          ws.close();
          setProgress(100);
          loadData();
          setTimeout(() => {
            setRunning(false);
            setProgress(0);
            setStatusText('');
          }, 2000);
        }

        if (data.error) {
          ws.close();
          setError(data.message || 'Lỗi khi chạy đánh giá AI');
          setRunning(false);
        }
      } catch (e) {
        console.error(e);
      }
    };

    ws.onerror = () => {
      console.error("WebSocket connection error");
    };

    const res = await runScreening();
    if (!res) {
      ws.close();
      setError('Lỗi khi gửi yêu cầu đánh giá AI lên server');
      setRunning(false);
      setProgress(0);
    }
  };

  const getResultForApplicant = (appId: number) => {
    return results.find(r => r.applicant_id === appId);
  };

  const getRecommendationBadge = (rec: string) => {
    switch(rec) {
      case 'STRONG_PASS':
        return <span className="px-3 py-1 rounded-full text-xs font-bold" style={{background: 'rgba(16,185,129,0.1)', color: '#10b981', border: '1px solid #10b981'}}>Xuất Sắc</span>;
      case 'PASS':
        return <span className="px-3 py-1 rounded-full text-xs font-bold" style={{background: 'rgba(59,130,246,0.1)', color: '#3b82f6', border: '1px solid #3b82f6'}}>Đạt</span>;
      case 'MAYBE':
        return <span className="px-3 py-1 rounded-full text-xs font-bold" style={{background: 'rgba(245,158,11,0.1)', color: '#f59e0b', border: '1px solid #f59e0b'}}>Xem Xét</span>;
      case 'REJECT':
      default:
        return <span className="px-3 py-1 rounded-full text-xs font-bold" style={{background: 'rgba(239,68,68,0.1)', color: '#ef4444', border: '1px solid #ef4444'}}>Loại</span>;
    }
  };

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8 fade-in-up">
        <div>
          <h1 className="text-2xl font-bold text-white mb-2">Quản Lý Tuyển Dụng & Đánh Giá CV</h1>
          <p className="text-slate-400 text-sm">Xem danh sách ứng viên và kết quả chấm điểm RAG AI</p>
        </div>
        <div className="flex gap-4">
          <button
            onClick={async () => {
              try {
                const token = localStorage.getItem('token');
                const res = await fetch(`http://127.0.0.1:8000/screening/export`, {
                  headers: {
                    'Authorization': `Bearer ${token}`
                  }
                });
                if (!res.ok) throw new Error('Export failed');
                const blob = await res.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'screening_results.csv';
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(url);
              } catch (error) {
                console.error("Download failed:", error);
                alert("Không thể tải báo cáo. Vui lòng thử lại.");
              }
            }}
            className="flex items-center gap-2 bg-slate-700 hover:bg-slate-600 text-white px-5 py-2.5 rounded-lg font-medium transition-all shadow-[0_0_15px_rgba(255,255,255,0.05)]"
          >
            <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
            Xuất Báo Cáo (CSV)
          </button>

          <button
            onClick={handleRunScreening}
            disabled={running}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-lg font-medium transition-all shadow-lg ${
              running
                ? 'bg-blue-800 text-blue-200 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-500 text-white shadow-[0_0_15px_rgba(37,99,235,0.3)]'
            }`}
          >
            {running ? (
              <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" className="opacity-25"/><path fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" className="opacity-75"/></svg>
            ) : (
              <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
            )}
            {running ? 'Đang chạy AI Đánh giá...' : 'Chạy AI Đánh Giá Tất Cả'}
          </button>
        </div>
      </div>

      {running && (
        <div className="mb-6 fade-in-up">
          <div className="flex justify-between items-center mb-1">
            <span className="text-sm font-medium text-emerald-400">
              {statusText || 'Đang chạy AI Screening...'}
            </span>
            <span className="text-sm font-medium text-emerald-400">{Math.round(progress)}%</span>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-2.5 overflow-hidden">
            <div className="bg-emerald-500 h-2.5 rounded-full transition-all duration-300 ease-out" style={{ width: `${progress}%` }}></div>
          </div>
        </div>
      )}

      {error && (
        <div className="mb-4 p-4 rounded-xl text-red-400" style={{background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)'}}>
          {error}
        </div>
      )}

      {loading ? (
        <div className="space-y-4">
          {[1,2,3].map(i => <div key={i} className="skeleton h-24 w-full rounded-xl" />)}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6">
          {applicants.length === 0 ? (
             <div className="glass-card p-12 text-center fade-in-up">
               <p className="text-slate-400">Chưa có ứng viên nào ứng tuyển.</p>
             </div>
          ) : applicants.map((app, idx) => {
            const res = getResultForApplicant(app.id);
            return (
              <div key={app.id} className="glass-card p-6 fade-in-up" style={{ animationDelay: `${idx * 50}ms` }}>
                <div className="flex flex-col md:flex-row justify-between gap-6">
                  {/* Info */}
                  <div className="flex-1">
                    <div className="flex items-center gap-4 mb-3">
                      <div className="w-12 h-12 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center text-white font-bold text-lg">
                        {app.name.charAt(0)}
                      </div>
                      <div>
                        <h2 className="text-lg font-bold text-white">{app.name}</h2>
                        <p className="text-sm text-slate-400">{app.position} • {app.email}</p>
                      </div>
                    </div>
                    {app.skills && (
                      <div className="flex flex-wrap gap-2 mt-3">
                        {app.skills.split(',').slice(0, 5).map((skill: string, i: number) => (
                          <span key={i} className="px-2 py-1 bg-slate-800 text-slate-300 text-xs rounded-md">{skill.trim()}</span>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* AI Result */}
                  <div className="md:w-1/2 rounded-xl p-4" style={{background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)'}}>
                    {res ? (
                      <div>
                         <div className="flex justify-between items-center mb-4">
                           <span className="text-sm font-semibold text-slate-300">Điểm AI RAG</span>
                           <span className="text-xl font-bold gradient-text">{res.percentage}%</span>
                         </div>

                         <div className="h-2 w-full bg-slate-800 rounded-full mb-4 overflow-hidden">
                           <div className="h-full transition-all duration-1000"
                                style={{
                                  width: `${res.percentage}%`,
                                  background: res.percentage >= 80 ? '#10b981' : res.percentage >= 60 ? '#3b82f6' : '#ef4444'
                                }}
                           />
                         </div>

                         <div className="flex justify-between items-end mb-4">
                           <div>
                             <p className="text-xs text-slate-400 mb-1">Quyết định AI:</p>
                             {getRecommendationBadge(res.recommendation)}
                           </div>
                           <div className="text-right">
                             <p className="text-xs text-slate-400 mb-1">Trạng thái:</p>
                             <span className="text-sm text-slate-200 font-medium">{res.status}</span>
                           </div>
                         </div>

                         {/* Interview Questions Section */}
                         {res.interview_questions && res.interview_questions.length > 0 && (
                           <div className="mt-4 pt-4 border-t" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
                             <p className="text-xs font-semibold text-amber-400 mb-2 flex items-center gap-1">
                               <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/></svg>
                               Câu hỏi phỏng vấn đề xuất (AI sinh ra)
                             </p>
                             <ul className="text-xs text-slate-300 space-y-2 pl-4 list-disc marker:text-amber-500/50">
                               {res.interview_questions.slice(0, 3).map((q: string, i: number) => (
                                 <li key={i}>{q}</li>
                               ))}
                               {res.interview_questions.length > 3 && (
                                 <li className="text-slate-500 italic">Và {res.interview_questions.length - 3} câu hỏi khác...</li>
                               )}
                             </ul>
                           </div>
                         )}
                      </div>
                    ) : (
                      <div className="h-full flex flex-col items-center justify-center text-center">
                        <svg className="w-8 h-8 text-slate-600 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                        <p className="text-sm text-slate-500">Chưa có kết quả đánh giá AI</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
