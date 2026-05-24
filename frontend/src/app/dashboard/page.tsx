'use client';

import { useEffect, useState } from 'react';
import { getHealth, getEmployees } from '@/lib/api';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  color: string;
  delay?: number;
}

function StatCard({ title, value, subtitle, icon, color, delay = 0 }: StatCardProps) {
  return (
    <div className="glass-card stat-card p-6 fade-in-up" style={{ animationDelay: `${delay}ms` }}>
      <div className="flex items-start justify-between mb-4">
        <div className="w-12 h-12 rounded-xl flex items-center justify-center"
          style={{ background: `${color}15`, border: `1px solid ${color}30`, color }}>
          {icon}
        </div>
      </div>
      <p className="text-3xl font-bold text-white mb-1">{value}</p>
      <p className="text-sm font-medium text-slate-300">{title}</p>
      {subtitle && <p className="text-xs text-slate-500 mt-1">{subtitle}</p>}
    </div>
  );
}

interface AgentBadgeProps {
  name: string;
  status?: boolean;
}
function AgentBadge({ name, status = true }: AgentBadgeProps) {
  return (
    <div className="flex items-center gap-2 px-3 py-2 rounded-lg" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
      <div className="w-2 h-2 rounded-full" style={{ background: status ? '#10b981' : '#6b7280', animation: status ? 'pulse-glow 2s infinite' : 'none' }} />
      <span className="text-xs text-slate-400">{name}</span>
    </div>
  );
}

export default function DashboardPage() {
  const [health, setHealth] = useState<any>(null);
  const [empData, setEmpData] = useState<any>(null);
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const u = localStorage.getItem('current_user');
    if (u) setUser(JSON.parse(u));

    Promise.all([getHealth(), getEmployees({ size: 200 })]).then(([h, e]) => {
      setHealth(h);
      setEmpData(e);
      setLoading(false);
    });
  }, []);

  const totalEmp = empData?.total ?? 0;
  const activeEmp = empData?.employees?.filter((e: any) => e.status === 'Active').length ?? 0;
  const depts = [...new Set((empData?.employees ?? []).map((e: any) => e.department))].length;

  const now = new Date();
  const greeting = now.getHours() < 12 ? 'Chào buổi sáng' : now.getHours() < 18 ? 'Chào buổi chiều' : 'Chào buổi tối';

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8 fade-in-up">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">
              {greeting}, <span className="gradient-text">{user?.username ?? '...'}</span> 👋
            </h1>
            <p className="text-slate-400 text-sm mt-1">
              {new Date().toLocaleDateString('vi-VN', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-2 rounded-full text-xs font-medium"
              style={{ background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.2)', color: '#10b981' }}>
              <div className="w-2 h-2 rounded-full bg-emerald-400" style={{ animation: 'pulse-glow 2s infinite' }} />
              {health ? `${health.agent_count} Agents Online` : 'Connecting...'}
            </div>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard
          title="Tổng nhân viên"
          value={loading ? '...' : totalEmp}
          subtitle="Trong hệ thống"
          delay={0}
          color="#10b981"
          icon={<svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/></svg>}
        />
        <StatCard
          title="Đang làm việc"
          value={loading ? '...' : activeEmp}
          subtitle={loading ? '' : `${totalEmp - activeEmp} đã nghỉ`}
          delay={80}
          color="#3b82f6"
          icon={<svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>}
        />
        <StatCard
          title="Phòng ban"
          value={loading ? '...' : depts}
          subtitle="Đơn vị hoạt động"
          delay={160}
          color="#8b5cf6"
          icon={<svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v16"/></svg>}
        />
        <StatCard
          title="AI Agents"
          value={loading ? '...' : (health?.agent_count ?? 0)}
          subtitle={health?.mode === 'online' ? 'Online mode' : 'Offline mode'}
          delay={240}
          color="#f59e0b"
          icon={<svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/></svg>}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Dept breakdown */}
        <div className="lg:col-span-2 glass-card p-6 fade-in-up" style={{ animationDelay: '200ms' }}>
          <h2 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
            <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v16"/></svg>
            Phân bổ theo phòng ban
          </h2>
          {loading ? (
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => <div key={i} className="skeleton h-8 w-full" />)}
            </div>
          ) : (
            <div className="space-y-3">
              {Object.entries(
                (empData?.employees ?? []).reduce((acc: any, e: any) => {
                  acc[e.department] = (acc[e.department] ?? 0) + 1;
                  return acc;
                }, {})
              )
                .sort(([, a]: any, [, b]: any) => b - a)
                .slice(0, 7)
                .map(([dept, count]: any) => {
                  const pct = Math.round((count / totalEmp) * 100);
                  const colors = ['#10b981','#3b82f6','#8b5cf6','#f59e0b','#ec4899','#06b6d4','#84cc16'];
                  const ci = Object.keys(empData?.employees?.reduce((a: any, e: any) => { a[e.department] = 1; return a; }, {}) ?? {}).indexOf(dept) % colors.length;
                  const color = colors[ci];
                  return (
                    <div key={dept}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs text-slate-300 font-medium">{dept}</span>
                        <span className="text-xs text-slate-500">{count} người ({pct}%)</span>
                      </div>
                      <div className="h-2 rounded-full" style={{ background: 'rgba(255,255,255,0.06)' }}>
                        <div className="h-2 rounded-full transition-all duration-700"
                          style={{ width: `${pct}%`, background: `linear-gradient(90deg, ${color}, ${color}99)` }} />
                      </div>
                    </div>
                  );
                })}
            </div>
          )}
        </div>

        {/* AI Agents status */}
        <div className="glass-card p-6 fade-in-up" style={{ animationDelay: '300ms' }}>
          <h2 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
            <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4"/></svg>
            AI Agents
          </h2>
          <div className="space-y-2">
            {['Policy Agent','Onboard Agent','CV Agent','Analytics Agent','Attendance Agent','Helpdesk Agent','Benefits Agent','Appraisal Agent'].map(a => (
              <AgentBadge key={a} name={a} status={health?.graph_loaded ?? false} />
            ))}
          </div>
          <div className="mt-4 pt-4 border-t" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
            <div className="text-xs text-slate-500 space-y-1">
              <div className="flex justify-between">
                <span>Model</span>
                <span className="text-slate-400">{health?.model ?? '—'}</span>
              </div>
              <div className="flex justify-between">
                <span>Mode</span>
                <span className={health?.mode === 'online' ? 'text-emerald-400' : 'text-amber-400'}>
                  {health?.mode ?? '—'}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Uptime</span>
                <span className="text-slate-400">
                  {health?.uptime_seconds ? `${Math.floor(health.uptime_seconds / 60)}m ${Math.floor(health.uptime_seconds % 60)}s` : '—'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
