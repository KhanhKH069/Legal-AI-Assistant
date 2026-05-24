'use client';

import { useState, useEffect, useCallback } from 'react';
import { getMetrics } from '@/lib/api';

interface AgentStat {
  count: number;
  percentage: number;
  avg_ms: number;
  min_ms: number;
  max_ms: number;
}

interface RecentRequest {
  timestamp: number;
  user_id: string;
  agent_name: string;
  response_time_ms: number;
  cached: boolean;
  message_preview: string;
  is_guest: boolean;
}

interface MetricsData {
  total_requests: number;
  employee_requests: number;
  guest_requests: number;
  cache_hits: number;
  cache_hit_rate: number;
  avg_response_time_ms: number;
  peak_agent: string;
  uptime_seconds: number;
  by_agent: Record<string, AgentStat>;
  recent_requests: RecentRequest[];
}

const AGENT_COLORS: Record<string, string> = {
  'Policy Agent':     '#10b981',
  'Onboard Agent':    '#3b82f6',
  'CV Agent':         '#8b5cf6',
  'Analytics Agent':  '#f59e0b',
  'Attendance Agent': '#ef4444',
  'Helpdesk Agent':   '#06b6d4',
  'Benefits Agent':   '#ec4899',
  'Appraisal Agent':  '#84cc16',
  'Recruitment Assistant': '#a78bfa',
  'Unknown Agent':    '#6b7280',
  'Offline Agent':    '#6b7280',
};

function StatCard({ title, value, subtitle, color, icon }: {
  title: string; value: string | number; subtitle?: string; color: string; icon: React.ReactNode;
}) {
  return (
    <div className="glass-card p-6 fade-in-up">
      <div className="flex items-start justify-between mb-3">
        <div className="w-11 h-11 rounded-xl flex items-center justify-center"
          style={{ background: `${color}18`, border: `1px solid ${color}30`, color }}>
          {icon}
        </div>
      </div>
      <p className="text-3xl font-bold text-white mb-1">{value}</p>
      <p className="text-sm font-medium text-slate-300">{title}</p>
      {subtitle && <p className="text-xs text-slate-500 mt-1">{subtitle}</p>}
    </div>
  );
}

function formatUptime(seconds: number) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) return `${h}h ${m}m`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}

function formatTime(ts: number) {
  return new Date(ts * 1000).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

export default function MetricsPage() {
  const [data, setData] = useState<MetricsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchMetrics = useCallback(async () => {
    const result = await getMetrics();
    if (result) {
      setData(result);
      setLastRefresh(new Date());
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchMetrics();
  }, [fetchMetrics]);

  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(fetchMetrics, 15000);
    return () => clearInterval(interval);
  }, [autoRefresh, fetchMetrics]);

  const agentEntries = data ? Object.entries(data.by_agent) : [];
  const maxCount = agentEntries.length > 0 ? Math.max(...agentEntries.map(([, s]) => s.count)) : 1;

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8 fade-in-up">
        <div>
          <h1 className="text-2xl font-bold text-white">
            AI <span className="gradient-text">Performance Metrics</span>
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Theo dõi hiệu suất thời gian thực của 8 AI Agents
            {lastRefresh && (
              <span className="text-slate-600 ml-2">
                · Cập nhật: {lastRefresh.toLocaleTimeString('vi-VN')}
              </span>
            )}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setAutoRefresh(a => !a)}
            className="flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-medium transition-all"
            style={{
              background: autoRefresh ? 'rgba(16,185,129,0.1)' : 'rgba(255,255,255,0.04)',
              border: `1px solid ${autoRefresh ? 'rgba(16,185,129,0.3)' : 'rgba(255,255,255,0.08)'}`,
              color: autoRefresh ? '#10b981' : '#64748b',
            }}>
            <span className={`w-2 h-2 rounded-full ${autoRefresh ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'}`} />
            Auto-refresh {autoRefresh ? 'ON' : 'OFF'}
          </button>
          <button
            onClick={fetchMetrics}
            className="flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-medium text-slate-400 transition-all hover:text-white"
            style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)' }}>
            <svg width="13" height="13" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path d="M23 4v6h-6M1 20v-6h6"/><path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/>
            </svg>
            Làm mới
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-48">
          <div className="flex items-center gap-3 text-slate-400">
            <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" className="opacity-25"/>
              <path fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" className="opacity-75"/>
            </svg>
            Đang tải metrics...
          </div>
        </div>
      ) : !data || data.total_requests === 0 ? (
        <div className="glass-card p-12 text-center fade-in-up">
          <div className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4"
            style={{ background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.15)' }}>
            <svg width="28" height="28" fill="none" stroke="#10b981" strokeWidth="1.5" viewBox="0 0 24 24">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
            </svg>
          </div>
          <p className="text-white font-semibold mb-2">Chưa có dữ liệu</p>
          <p className="text-slate-400 text-sm">Bắt đầu chat với HR Assistant để xem metrics hiện tại.</p>
        </div>
      ) : (
        <>
          {/* Stat Cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <StatCard
              title="Tổng yêu cầu"
              value={data.total_requests}
              subtitle={`${data.employee_requests} nhân viên · ${data.guest_requests} khách`}
              color="#10b981"
              icon={<svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
              </svg>}
            />
            <StatCard
              title="Cache Hit Rate"
              value={`${data.cache_hit_rate}%`}
              subtitle={`${data.cache_hits} câu hỏi trùng được cache`}
              color="#3b82f6"
              icon={<svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
              </svg>}
            />
            <StatCard
              title="Thời gian phản hồi TB"
              value={data.avg_response_time_ms > 0 ? `${(data.avg_response_time_ms / 1000).toFixed(1)}s` : '—'}
              subtitle="Thời gian graph.invoke() trả về"
              color="#8b5cf6"
              icon={<svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
              </svg>}
            />
            <StatCard
              title="Agent phổ biến nhất"
              value={data.peak_agent}
              subtitle={`Uptime: ${formatUptime(data.uptime_seconds)}`}
              color="#f59e0b"
              icon={<svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
              </svg>}
            />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 mb-6">
            {/* Agent Usage Chart */}
            <div className="lg:col-span-3 glass-card p-6 fade-in-up">
              <h2 className="text-base font-semibold text-white mb-5 flex items-center gap-2">
                <span className="w-1.5 h-5 rounded-full bg-emerald-400 inline-block" />
                Phân bổ Agent Usage
              </h2>
              <div className="space-y-4">
                {agentEntries.length === 0 ? (
                  <p className="text-slate-500 text-sm">Chưa có dữ liệu.</p>
                ) : (
                  agentEntries.map(([agent, stat]) => {
                    const color = AGENT_COLORS[agent] || '#6b7280';
                    const barWidth = maxCount > 0 ? Math.round((stat.count / maxCount) * 100) : 0;
                    return (
                      <div key={agent}>
                        <div className="flex items-center justify-between mb-1.5">
                          <div className="flex items-center gap-2">
                            <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: color }} />
                            <span className="text-sm text-slate-300">{agent}</span>
                          </div>
                          <div className="flex items-center gap-4 text-xs text-slate-500">
                            <span className="font-mono">{stat.count} req ({stat.percentage}%)</span>
                            <span className="font-mono text-slate-400">{(stat.avg_ms / 1000).toFixed(1)}s avg</span>
                          </div>
                        </div>
                        <div className="h-2.5 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.05)' }}>
                          <div className="h-2.5 rounded-full transition-all duration-500"
                            style={{ width: `${barWidth}%`, background: `linear-gradient(90deg, ${color}, ${color}99)` }} />
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>

            {/* Response Time per Agent */}
            <div className="lg:col-span-2 glass-card p-6 fade-in-up">
              <h2 className="text-base font-semibold text-white mb-5 flex items-center gap-2">
                <span className="w-1.5 h-5 rounded-full bg-purple-400 inline-block" />
                Thời gian phản hồi
              </h2>
              <div className="space-y-3">
                {agentEntries.length === 0 ? (
                  <p className="text-slate-500 text-sm">Chưa có dữ liệu.</p>
                ) : (
                  agentEntries.slice(0, 8).map(([agent, stat]) => {
                    const color = AGENT_COLORS[agent] || '#6b7280';
                    const isLong = stat.avg_ms > 5000;
                    return (
                      <div key={agent} className="flex items-center justify-between p-3 rounded-xl"
                        style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)' }}>
                        <div className="flex items-center gap-2">
                          <span className="w-2 h-2 rounded-full" style={{ background: color }} />
                          <span className="text-xs text-slate-400">{agent.replace(' Agent', '')}</span>
                        </div>
                        <span className={`text-xs font-mono font-semibold ${isLong ? 'text-amber-400' : 'text-emerald-400'}`}>
                          {(stat.avg_ms / 1000).toFixed(1)}s
                        </span>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </div>

          {/* Recent Requests Timeline */}
          <div className="glass-card p-6 fade-in-up">
            <h2 className="text-base font-semibold text-white mb-5 flex items-center gap-2">
              <span className="w-1.5 h-5 rounded-full bg-blue-400 inline-block" />
              20 Yêu cầu gần nhất
            </h2>
            {data.recent_requests.length === 0 ? (
              <p className="text-slate-500 text-sm">Chưa có yêu cầu nào.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="text-slate-500 border-b" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
                      <th className="text-left pb-3 font-medium">Thời gian</th>
                      <th className="text-left pb-3 font-medium">User</th>
                      <th className="text-left pb-3 font-medium">Agent</th>
                      <th className="text-left pb-3 font-medium">Câu hỏi</th>
                      <th className="text-right pb-3 font-medium">Response time</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y" style={{ borderColor: 'rgba(255,255,255,0.04)' }}>
                    {data.recent_requests.map((req, i) => {
                      const color = AGENT_COLORS[req.agent_name] || '#6b7280';
                      const isSlow = req.response_time_ms > 5000;
                      return (
                        <tr key={i} className="group">
                          <td className="py-2.5 text-slate-500 font-mono whitespace-nowrap pr-4">
                            {formatTime(req.timestamp)}
                          </td>
                          <td className="py-2.5 pr-4">
                            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${req.is_guest
                              ? 'text-purple-300'
                              : 'text-emerald-300'
                            }`} style={{
                              background: req.is_guest ? 'rgba(139,92,246,0.12)' : 'rgba(16,185,129,0.1)',
                            }}>
                              {req.is_guest ? '👤 Guest' : req.user_id}
                            </span>
                          </td>
                          <td className="py-2.5 pr-4">
                            <span className="flex items-center gap-1.5">
                              <span className="w-1.5 h-1.5 rounded-full" style={{ background: color }} />
                              <span className="text-slate-300">{req.agent_name}</span>
                            </span>
                          </td>
                          <td className="py-2.5 pr-4 text-slate-500 max-w-xs truncate">
                            {req.message_preview || '—'}
                          </td>
                          <td className={`py-2.5 text-right font-mono font-semibold ${isSlow ? 'text-amber-400' : 'text-emerald-400'}`}>
                            {(req.response_time_ms / 1000).toFixed(2)}s
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
