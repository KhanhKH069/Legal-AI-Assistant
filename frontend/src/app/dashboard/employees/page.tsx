'use client';

import { useEffect, useState } from 'react';
import { getEmployees } from '@/lib/api';

const DEPT_COLORS: Record<string, string> = {
  Engineering: '#3b82f6', HR: '#ec4899', Sales: '#f59e0b',
  Marketing: '#8b5cf6', Finance: '#06b6d4', Product: '#10b981',
  QA: '#84cc16', DevOps: '#f97316', Legal: '#6366f1', 'Customer Success': '#14b8a6',
};

const DEPTS = ['Tất cả', 'Engineering', 'HR', 'Sales', 'Marketing', 'Finance', 'Product', 'QA', 'DevOps', 'Legal'];

export default function EmployeesPage() {
  const [employees, setEmployees] = useState<any[]>([]);
  const [filtered, setFiltered] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [dept, setDept] = useState('Tất cả');
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    const u = localStorage.getItem('current_user');
    if (u) setUser(JSON.parse(u));
    getEmployees({ size: 200 }).then(data => {
      setEmployees(data?.employees ?? []);
      setFiltered(data?.employees ?? []);
      setLoading(false);
    });
  }, []);

  useEffect(() => {
    let result = employees;
    if (dept !== 'Tất cả') result = result.filter(e => e.department === dept);
    if (search) result = result.filter(e =>
      e.name?.toLowerCase().includes(search.toLowerCase()) ||
      e.employee_id?.toLowerCase().includes(search.toLowerCase()) ||
      e.position?.toLowerCase().includes(search.toLowerCase())
    );
    setFiltered(result);
  }, [search, dept, employees]);

  const isPrivileged = user?.role === 'admin' || user?.role === 'manager';

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-6 fade-in-up">
        <h1 className="text-2xl font-bold text-white mb-1">Danh sách nhân viên</h1>
        <p className="text-slate-400 text-sm">{filtered.length} nhân viên được hiển thị</p>
      </div>

      {/* Filters */}
      <div className="glass-card p-4 mb-6 fade-in-up" style={{ animationDelay: '80ms' }}>
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>
            </svg>
            <input
              id="emp-search"
              type="text"
              placeholder="Tìm theo tên, mã NV, vị trí..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="dark-input w-full pl-10 pr-4 py-2.5 rounded-xl text-sm"
            />
          </div>
          <div className="flex gap-2 flex-wrap">
            {DEPTS.slice(0, 6).map(d => (
              <button key={d} onClick={() => setDept(d)}
                className="px-3 py-2 rounded-xl text-xs font-medium transition-all"
                style={{
                  background: dept === d ? 'rgba(16,185,129,0.15)' : 'rgba(255,255,255,0.04)',
                  border: `1px solid ${dept === d ? 'rgba(16,185,129,0.4)' : 'rgba(255,255,255,0.07)'}`,
                  color: dept === d ? '#10b981' : '#94a3b8',
                }}>
                {d}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="glass-card overflow-hidden fade-in-up" style={{ animationDelay: '160ms' }}>
        {loading ? (
          <div className="p-8 space-y-4">
            {[...Array(8)].map((_, i) => <div key={i} className="skeleton h-12 w-full" />)}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full dark-table">
              <thead>
                <tr>
                  <th className="text-left px-6 py-4">Nhân viên</th>
                  <th className="text-left px-6 py-4">Phòng ban</th>
                  <th className="text-left px-6 py-4">Vị trí</th>
                  <th className="text-left px-6 py-4">Trạng thái</th>
                  {isPrivileged && <th className="text-left px-6 py-4">Lương (VNĐ)</th>}
                  <th className="text-left px-6 py-4">Đánh giá</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((emp, i) => {
                  const color = DEPT_COLORS[emp.department] ?? '#6b7280';
                  const initials = emp.name?.split(' ').slice(-2).map((w: string) => w[0]).join('') ?? '??';
                  return (
                    <tr key={emp.employee_id} className="fade-in-up" style={{ animationDelay: `${i * 20}ms` }}>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-9 h-9 rounded-full flex items-center justify-center shrink-0 text-xs font-bold"
                            style={{ background: `${color}20`, border: `1px solid ${color}40`, color }}>
                            {initials}
                          </div>
                          <div>
                            <p className="text-sm font-medium text-white">{emp.name}</p>
                            <p className="text-xs text-slate-500">{emp.employee_id}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-xs px-2.5 py-1 rounded-full font-medium"
                          style={{ background: `${color}15`, color, border: `1px solid ${color}30` }}>
                          {emp.department}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-slate-300">{emp.position}</td>
                      <td className="px-6 py-4">
                        <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${emp.status === 'Active' ? 'badge-active' : 'badge-resigned'}`}>
                          {emp.status === 'Active' ? 'Đang làm' : 'Đã nghỉ'}
                        </span>
                      </td>
                      {isPrivileged && (
                        <td className="px-6 py-4 text-sm text-slate-300 font-mono">
                          {emp.salary_vnd ? emp.salary_vnd.toLocaleString('vi-VN') : '—'}
                        </td>
                      )}
                      <td className="px-6 py-4">
                        {emp.performance_rating ? (
                          <div className="flex items-center gap-2">
                            <div className="flex gap-0.5">
                              {[1,2,3,4,5].map(s => (
                                <div key={s} className="w-1.5 h-4 rounded-sm"
                                  style={{ background: s <= Math.round(emp.performance_rating) ? '#10b981' : 'rgba(255,255,255,0.1)' }} />
                              ))}
                            </div>
                            <span className="text-xs text-slate-400">{emp.performance_rating}</span>
                          </div>
                        ) : '—'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            {filtered.length === 0 && (
              <div className="text-center py-16 text-slate-500">
                <svg className="mx-auto mb-3 opacity-30" width="40" height="40" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
                  <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/>
                </svg>
                Không tìm thấy nhân viên phù hợp
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
