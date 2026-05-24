'use client';

import { useEffect, useState } from 'react';
import { getMyMetrics } from '@/lib/api';

interface MetricData {
  employee: {
    name: string;
    department: string;
    position: string;
    level: string;
    base_salary: number;
    leave_balance: number;
    performance_rating: number;
  };
  latest_payroll: any;
  latest_appraisal: any;
  pending_leaves: number;
  open_tickets: number;
}

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

export default function MyMetricsPage() {
  const [data, setData] = useState<MetricData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMyMetrics().then(res => {
      setData(res);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const formatVND = (val: number) => {
    if (!val) return '0 ₫';
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(val);
  };

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8 fade-in-up">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">
              Chỉ số cá nhân của <span className="gradient-text">{data?.employee.name ?? '...'}</span> 📊
            </h1>
            <p className="text-slate-400 text-sm mt-1">
              {data?.employee.position} · {data?.employee.department} · Level: {data?.employee.level}
            </p>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard
          title="Lương Net Tháng Cuối"
          value={loading ? '...' : formatVND(data?.latest_payroll?.net_salary || 0)}
          subtitle={data?.latest_payroll ? `Tháng ${data.latest_payroll.month}` : 'Chưa có dữ liệu'}
          delay={0}
          color="#10b981"
          icon={<svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M12 1v22M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>}
        />
        <StatCard
          title="Đánh Giá Năng Lực"
          value={loading ? '...' : (data?.latest_appraisal?.final_score || data?.employee.performance_rating || 'N/A')}
          subtitle={data?.latest_appraisal ? `Kỳ: ${data.latest_appraisal.period}` : 'Tổng quan'}
          delay={80}
          color="#f59e0b"
          icon={<svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>}
        />
        <StatCard
          title="Phép Năm Còn Lại"
          value={loading ? '...' : `${data?.employee.leave_balance || 0} ngày`}
          subtitle={data?.pending_leaves ? `Đang chờ duyệt: ${data.pending_leaves} ngày` : 'Sẵn sàng sử dụng'}
          delay={160}
          color="#3b82f6"
          icon={<svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>}
        />
        <StatCard
          title="Yêu Cầu / Ticket"
          value={loading ? '...' : (data?.open_tickets || 0)}
          subtitle="Đang chờ xử lý"
          delay={240}
          color="#8b5cf6"
          icon={<svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></svg>}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Payroll Details */}
        <div className="glass-card p-6 fade-in-up" style={{ animationDelay: '300ms' }}>
          <h2 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
            <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M12 1v22M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
            Chi tiết Phiếu Lương (Tháng {data?.latest_payroll?.month ?? 'N/A'})
          </h2>

          {loading ? (
             <div className="space-y-3">
               {[...Array(5)].map((_, i) => <div key={i} className="skeleton h-8 w-full" />)}
             </div>
          ) : data?.latest_payroll ? (
            <div className="space-y-4">
              <div className="flex justify-between items-center py-2 border-b border-white/5">
                <span className="text-slate-400 text-sm">Lương cơ bản</span>
                <span className="text-white font-medium">{formatVND(data.latest_payroll.base_salary)}</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-white/5">
                <span className="text-slate-400 text-sm">Lương OT ({data.latest_payroll.ot_hours} giờ)</span>
                <span className="text-emerald-400 font-medium">+{formatVND(data.latest_payroll.ot_pay)}</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-white/5">
                <span className="text-slate-400 text-sm">Thưởng KPI</span>
                <span className="text-emerald-400 font-medium">+{formatVND(data.latest_payroll.kpi_bonus)}</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-white/5">
                <span className="text-slate-400 text-sm">Thưởng khác</span>
                <span className="text-emerald-400 font-medium">+{formatVND(data.latest_payroll.other_bonus)}</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-white/5">
                <span className="text-slate-400 text-sm">Tổng khấu trừ (Thuế, BH)</span>
                <span className="text-red-400 font-medium">-{formatVND(data.latest_payroll.total_deductions)}</span>
              </div>
              <div className="flex justify-between items-center py-3 bg-white/5 px-4 rounded-xl mt-4">
                <span className="text-slate-300 font-semibold">Thực Lãnh (Net Salary)</span>
                <span className="text-emerald-400 font-bold text-lg">{formatVND(data.latest_payroll.net_salary)}</span>
              </div>
            </div>
          ) : (
            <p className="text-slate-500 text-sm text-center py-8">Chưa có dữ liệu phiếu lương</p>
          )}
        </div>

        {/* Appraisal Details */}
        <div className="glass-card p-6 fade-in-up" style={{ animationDelay: '400ms' }}>
          <h2 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
            <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
            Kỳ Đánh Giá Năng Lực ({data?.latest_appraisal?.period ?? 'N/A'})
          </h2>

          {loading ? (
             <div className="space-y-3">
               {[...Array(3)].map((_, i) => <div key={i} className="skeleton h-12 w-full" />)}
             </div>
          ) : data?.latest_appraisal ? (
            <div className="space-y-4">
              <div className="flex items-center gap-4 bg-white/5 p-4 rounded-xl">
                <div className="text-4xl font-bold text-amber-400">{data.latest_appraisal.final_score}</div>
                <div>
                  <div className="text-sm text-slate-400">Xếp loại</div>
                  <div className="text-lg font-semibold text-white">{data.latest_appraisal.rating_label}</div>
                </div>
              </div>

              {data.latest_appraisal.manager_feedback_json && data.latest_appraisal.manager_feedback_json !== 'null' && (
                <div className="mt-6">
                  <h3 className="text-xs text-slate-500 uppercase tracking-wider mb-3">Feedback từ Quản lý</h3>
                  <div className="space-y-3">
                    {Object.entries(JSON.parse(data.latest_appraisal.manager_feedback_json)).map(([k, v]: any) => (
                      <div key={k} className="bg-white/5 p-3 rounded-lg border border-white/5">
                        <p className="text-xs font-semibold text-slate-400 capitalize mb-1">{k}</p>
                        <p className="text-sm text-slate-200">{v}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <p className="text-slate-500 text-sm text-center py-8">Chưa có dữ liệu đánh giá</p>
          )}
        </div>
      </div>
    </div>
  );
}
