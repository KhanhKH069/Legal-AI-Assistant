'use client';

import { useEffect, useState } from 'react';
import { getEmployeeProfile, getMonthlyInfo } from '@/lib/api';

function InfoRow({ label, value }: { label: string; value?: string | number | null }) {
  return (
    <div className="flex items-start justify-between py-3 border-b" style={{ borderColor: 'rgba(255,255,255,0.05)' }}>
      <span className="text-xs text-slate-500 font-medium uppercase tracking-wide">{label}</span>
      <span className="text-sm text-slate-200 text-right max-w-[60%]">{value ?? '—'}</span>
    </div>
  );
}

export default function ProfilePage() {
  const [profile, setProfile] = useState<any>(null);
  const [monthly, setMonthly] = useState<any>(null);
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const u = localStorage.getItem('current_user');
    if (!u) return;
    const parsed = JSON.parse(u);
    setUser(parsed);
    Promise.all([
      getEmployeeProfile(parsed.employee_id),
      getMonthlyInfo(parsed.employee_id),
    ]).then(([p, m]) => {
      setProfile(p);
      setMonthly(m);
      setLoading(false);
    });
  }, []);

  const contractEnd = profile?.contract?.end;
  const daysToExpiry = contractEnd
    ? Math.ceil((new Date(contractEnd).getTime() - Date.now()) / 86400000)
    : null;

  const initials = profile?.name?.split(' ').slice(-2).map((w: string) => w[0]).join('') ?? '??';

  return (
    <div className="p-8">
      <div className="mb-6 fade-in-up">
        <h1 className="text-2xl font-bold text-white mb-1">Hồ sơ cá nhân</h1>
        <p className="text-slate-400 text-sm">Thông tin chi tiết của bạn</p>
      </div>

      {loading ? (
        <div className="space-y-4">
          {[...Array(4)].map((_, i) => <div key={i} className="skeleton h-32 w-full rounded-2xl" />)}
        </div>
      ) : !profile ? (
        <div className="glass-card p-12 text-center text-slate-500">
          <p>Không tải được thông tin. Hãy đảm bảo backend đang chạy.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Profile card */}
          <div className="fade-in-up">
            <div className="glass-card p-6 text-center">
              <div className="w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl font-bold"
                style={{ background: 'linear-gradient(135deg, rgba(16,185,129,0.3), rgba(59,130,246,0.3))', border: '2px solid rgba(16,185,129,0.4)', color: '#10b981' }}>
                {initials}
              </div>
              <h2 className="text-lg font-bold text-white mb-1">{profile.name}</h2>
              <p className="text-sm text-slate-400 mb-2">{profile.position}</p>
              <span className="text-xs px-3 py-1 rounded-full font-medium"
                style={{ background: 'rgba(16,185,129,0.1)', color: '#10b981', border: '1px solid rgba(16,185,129,0.3)' }}>
                {profile.department}
              </span>

              {/* Performance ring */}
              <div className="mt-6 flex justify-center">
                <div className="relative w-24 h-24">
                  <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
                    <circle cx="50" cy="50" r="40" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="8"/>
                    <circle cx="50" cy="50" r="40" fill="none" stroke="#10b981" strokeWidth="8"
                      strokeDasharray={`${(profile.performance_rating / 5) * 251} 251`}
                      strokeLinecap="round"/>
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-xl font-bold text-white">{profile.performance_rating}</span>
                    <span className="text-xs text-slate-500">/5.0</span>
                  </div>
                </div>
              </div>
              <p className="text-xs text-slate-500 mt-2">Đánh giá hiệu suất</p>
            </div>

            {/* Leave balance card */}
            <div className="glass-card p-5 mt-4 fade-in-up" style={{ animationDelay: '100ms' }}>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-3">Ngày phép còn lại</p>
              <div className="flex items-end gap-2">
                <span className="text-4xl font-bold gradient-text">{profile.leave_balance}</span>
                <span className="text-slate-500 text-sm mb-1">ngày</span>
              </div>
              <div className="mt-3 h-2 rounded-full" style={{ background: 'rgba(255,255,255,0.06)' }}>
                <div className="h-2 rounded-full" style={{ width: `${Math.min((profile.leave_balance / 20) * 100, 100)}%`, background: 'linear-gradient(90deg, #10b981, #3b82f6)' }} />
              </div>
              <p className="text-xs text-slate-600 mt-1">Tối đa 20 ngày/năm</p>
            </div>
          </div>

          {/* Details */}
          <div className="lg:col-span-2 space-y-4">
            {/* Personal info */}
            <div className="glass-card p-6 fade-in-up" style={{ animationDelay: '80ms' }}>
              <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
                <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/>
                </svg>
                Thông tin cá nhân
              </h3>
              <InfoRow label="Mã nhân viên" value={profile.employee_id} />
              <InfoRow label="Họ và tên" value={profile.name} />
              <InfoRow label="Email" value={profile.email} />
              <InfoRow label="Số điện thoại" value={profile.phone} />
              <InfoRow label="Địa chỉ" value={profile.address} />
              <InfoRow label="Học vấn" value={profile.education} />
              <InfoRow label="Ngày vào làm" value={profile.hire_date} />
            </div>

            {/* Work info */}
            <div className="glass-card p-6 fade-in-up" style={{ animationDelay: '160ms' }}>
              <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
                <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v16"/>
                </svg>
                Thông tin công việc
              </h3>
              <InfoRow label="Phòng ban" value={profile.department} />
              <InfoRow label="Vị trí" value={profile.position} />
              <InfoRow label="Cấp bậc" value={profile.level} />
              <InfoRow label="Quản lý trực tiếp" value={profile.manager_name ?? profile.manager_id} />
              <InfoRow label="Trạng thái" value={profile.status === 'Active' ? '✅ Đang làm việc' : '❌ Đã nghỉ'} />
            </div>

            {/* Contract */}
            <div className="glass-card p-6 fade-in-up" style={{ animationDelay: '240ms' }}>
              <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
                <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>
                </svg>
                Hợp đồng lao động
              </h3>
              <InfoRow label="Bắt đầu" value={profile.contract?.start} />
              <InfoRow label="Kết thúc" value={profile.contract?.end} />
              {daysToExpiry !== null && (
                <div className={`mt-3 p-3 rounded-xl text-sm ${daysToExpiry <= 30 ? 'text-red-400' : daysToExpiry <= 90 ? 'text-amber-400' : 'text-emerald-400'}`}
                  style={{ background: daysToExpiry <= 30 ? 'rgba(239,68,68,0.1)' : daysToExpiry <= 90 ? 'rgba(245,158,11,0.1)' : 'rgba(16,185,129,0.1)', border: `1px solid ${daysToExpiry <= 30 ? 'rgba(239,68,68,0.2)' : daysToExpiry <= 90 ? 'rgba(245,158,11,0.2)' : 'rgba(16,185,129,0.2)'}` }}>
                  {daysToExpiry > 0 ? `⏳ Hợp đồng còn ${daysToExpiry} ngày` : '❗ Hợp đồng đã hết hạn'}
                </div>
              )}
            </div>

            {/* Skills */}
            {profile.skills?.length > 0 && (
              <div className="glass-card p-6 fade-in-up" style={{ animationDelay: '320ms' }}>
                <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
                  <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
                  </svg>
                  Kỹ năng
                </h3>
                <div className="flex flex-wrap gap-2">
                  {profile.skills.map((s: string) => (
                    <span key={s} className="text-xs px-3 py-1.5 rounded-full font-medium"
                      style={{ background: 'rgba(59,130,246,0.1)', color: '#93c5fd', border: '1px solid rgba(59,130,246,0.2)' }}>
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
