'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

interface User {
  username: string;
  role: string;
  employee_id: string;
}

const navItems = [
  {
    href: '/dashboard',
    label: 'Dashboard',
    icon: (
      <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
        <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>
        <rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>
      </svg>
    ),
  },
  {
    href: '/dashboard/chat',
    label: 'HR Assistant',
    icon: (
      <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
        <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>
      </svg>
    ),
    badge: 'AI',
  },
  {
    href: '/dashboard/policies',
    label: 'Nội Quy & RAG',
    icon: (
      <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
        <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6z"/>
        <path d="M14 3v5h5M16 13H8M16 17H8M10 9H8"/>
      </svg>
    ),
  },
  {
    href: '/dashboard/employees',
    label: 'Nhân viên',
    icon: (
      <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
        <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/>
        <path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/>
      </svg>
    ),
  },
  {
    href: '/dashboard/profile',
    label: 'Hồ sơ của tôi',
    icon: (
      <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
        <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/>
      </svg>
    ),
  },
  {
    href: '/dashboard/recruitment',
    label: 'Tuyển dụng & RAG',
    icon: (
      <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
        <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6z"/>
        <path d="M14 3v5h5M16 13H8M16 17H8M10 9H8"/>
      </svg>
    ),
    badge: 'Mới',
  },
  {
    href: '/dashboard/my-metrics',
    label: 'Chỉ số của tôi',
    icon: (
      <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
        <path d="M12 20V10M18 20V4M6 20v-4"/>
      </svg>
    ),
  },
  {
    href: '/dashboard/metrics',
    label: 'AI Metrics',
    icon: (
      <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
      </svg>
    ),
    badge: 'Live',
  },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    const u = localStorage.getItem('current_user');
    if (u) setUser(JSON.parse(u));
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('current_user');
    router.push('/');
  };

  const roleColor = user?.role === 'admin' ? 'text-purple-400' :
    user?.role === 'manager' ? 'text-blue-400' : 'text-emerald-400';
  const roleLabel = user?.role === 'admin' ? 'Quản trị viên' :
    user?.role === 'manager' ? 'Quản lý' : 'Nhân viên';

  return (
    <aside className="flex flex-col w-64 min-h-screen shrink-0"
      style={{ background: 'var(--bg-sidebar)', borderRight: '1px solid rgba(255,255,255,0.05)' }}>

      {/* Logo */}
      <div className="px-6 py-6 border-b" style={{ borderColor: 'rgba(255,255,255,0.05)' }}>
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0"
            style={{ background: 'linear-gradient(135deg, #10b981, #059669)', boxShadow: '0 0 20px rgba(16,185,129,0.3)' }}>
            <svg width="16" height="16" fill="white" viewBox="0 0 24 24">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
            </svg>
          </div>
          <div>
            <span className="text-lg font-bold text-white">Para<span className="text-emerald-400">line</span></span>
            <p className="text-xs text-slate-500">HR Portal</p>
          </div>
        </div>
      </div>

      {/* User info */}
      {user && (
        <div className="px-4 py-4 mx-3 mt-4 rounded-xl" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)' }}>
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full flex items-center justify-center shrink-0 font-bold text-sm"
              style={{ background: 'linear-gradient(135deg, rgba(16,185,129,0.3), rgba(59,130,246,0.3))', border: '1px solid rgba(16,185,129,0.3)', color: '#10b981' }}>
              {user.username.slice(0, 2).toUpperCase()}
            </div>
            <div className="min-w-0">
              <p className="text-sm font-semibold text-white truncate">{user.username}</p>
              <p className={`text-xs font-medium ${roleColor}`}>{roleLabel}</p>
            </div>
          </div>
        </div>
      )}

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        <p className="px-3 py-2 text-xs font-semibold text-slate-600 uppercase tracking-wider">Menu</p>
        {navItems.map((item) => {
          const isActive = pathname === item.href || (item.href !== '/dashboard' && pathname.startsWith(item.href));
          return (
            <Link key={item.href} href={item.href}
              className={`nav-item flex items-center gap-3 px-3 py-2.5 text-sm font-medium ${isActive ? 'active' : 'text-slate-400'}`}>
              <span className={isActive ? 'text-emerald-400' : 'text-slate-500'}>{item.icon}</span>
              <span className="flex-1">{item.label}</span>
              {item.badge && (
                <span className="text-xs px-2 py-0.5 rounded-full font-bold"
                  style={{ background: 'rgba(16,185,129,0.15)', color: '#10b981', border: '1px solid rgba(16,185,129,0.3)' }}>
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Bottom */}
      <div className="px-3 py-4 border-t" style={{ borderColor: 'rgba(255,255,255,0.05)' }}>
        <button onClick={handleLogout}
          className="nav-item flex items-center gap-3 px-3 py-2.5 text-sm font-medium text-slate-400 w-full text-left hover:text-red-400">
          <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24" className="text-slate-500">
            <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9"/>
          </svg>
          Đăng xuất
        </button>
      </div>
    </aside>
  );
}
