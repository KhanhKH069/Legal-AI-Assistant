'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { login } from '@/lib/api';

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const token = localStorage.getItem('access_token');
    if (token) router.replace('/dashboard');
  }, [router]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    const res = await login(username, password);
    if (res) {
      localStorage.setItem('access_token', res.access_token);
      localStorage.setItem('current_user', JSON.stringify(res.user));
      router.push('/dashboard');
    } else {
      setError('Sai mã nhân viên hoặc mật khẩu. Thử lại nhé!');
    }
    setLoading(false);
  };

  const handleGuestMode = () => {
    const sessionId = `guest_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
    localStorage.setItem('guest_session_id', sessionId);
    localStorage.removeItem('access_token');
    localStorage.removeItem('current_user');
    router.push('/guest');
  };

  if (!mounted) return null;

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden"
      style={{ background: 'radial-gradient(ellipse at 60% 40%, #0d2040 0%, #0a0f1e 70%)' }}>

      {/* Background orbs */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute w-96 h-96 rounded-full opacity-20 blur-3xl"
          style={{ background: 'radial-gradient(circle, #10b981, transparent)', top: '-10%', right: '10%' }} />
        <div className="absolute w-80 h-80 rounded-full opacity-10 blur-3xl"
          style={{ background: 'radial-gradient(circle, #3b82f6, transparent)', bottom: '5%', left: '5%' }} />
        <div className="absolute w-64 h-64 rounded-full opacity-15 blur-3xl"
          style={{ background: 'radial-gradient(circle, #8b5cf6, transparent)', top: '50%', left: '30%' }} />
      </div>

      {/* Grid pattern */}
      <div className="absolute inset-0 opacity-[0.03]"
        style={{ backgroundImage: 'linear-gradient(rgba(255,255,255,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.5) 1px, transparent 1px)', backgroundSize: '50px 50px' }} />

      <div className="relative z-10 w-full max-w-md px-6 fade-in-up">
        {/* Logo */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 mb-4">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center"
              style={{ background: 'linear-gradient(135deg, #10b981, #059669)', boxShadow: '0 0 20px rgba(16,185,129,0.4)' }}>
              <svg width="20" height="20" fill="white" viewBox="0 0 24 24">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
              </svg>
            </div>
            <span className="text-2xl font-bold text-white">Para<span className="text-emerald-400">line</span></span>
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">Chào mừng trở lại</h1>
          <p className="text-slate-400 text-sm">Đăng nhập để truy cập HR Portal</p>
        </div>

        {/* Card */}
        <div className="glass-card p-8 glow">
          <form onSubmit={handleLogin} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Mã nhân viên
              </label>
              <input
                id="username-input"
                type="text"
                value={username}
                onChange={e => setUsername(e.target.value)}
                placeholder="VD: EMP001"
                className="dark-input w-full px-4 py-3 rounded-xl text-sm"
                required
                autoFocus
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Mật khẩu
              </label>
              <input
                id="password-input"
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="••••••••"
                className="dark-input w-full px-4 py-3 rounded-xl text-sm"
                required
              />
            </div>

            {error && (
              <div className="flex items-center gap-2 p-3 rounded-xl text-sm"
                style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)', color: '#f87171' }}>
                <svg width="16" height="16" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
                </svg>
                {error}
              </div>
            )}

            <button
              id="login-btn"
              type="submit"
              disabled={loading}
              className="btn-primary w-full py-3 rounded-xl font-semibold text-sm"
              style={{ opacity: loading ? 0.7 : 1 }}>
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" className="opacity-25"/>
                    <path fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" className="opacity-75"/>
                  </svg>
                  Đang đăng nhập...
                </span>
              ) : 'Đăng Nhập'}
            </button>
          </form>

          {/* Divider */}
          <div className="flex items-center gap-3 my-5">
            <div className="flex-1 h-px" style={{ background: 'rgba(255,255,255,0.08)' }} />
            <span className="text-xs text-slate-500">hoặc</span>
            <div className="flex-1 h-px" style={{ background: 'rgba(255,255,255,0.08)' }} />
          </div>

          {/* Guest button */}
          <button
            id="guest-btn"
            type="button"
            onClick={handleGuestMode}
            className="w-full py-3 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 transition-all hover:scale-[1.02]"
            style={{
              background: 'rgba(139,92,246,0.1)',
              border: '1px solid rgba(139,92,246,0.3)',
              color: '#a78bfa',
            }}>
            <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
              <circle cx="12" cy="7" r="4"/>
            </svg>
            Tiếp tục với tư cách Khách / Ứng viên
          </button>

          {/* Demo hint */}
          <div className="mt-5 p-4 rounded-xl" style={{ background: 'rgba(16,185,129,0.06)', border: '1px dashed rgba(16,185,129,0.2)' }}>
            <p className="text-xs text-slate-400 font-medium mb-1">🔑 Tài khoản demo nhân viên:</p>
            <p className="text-xs text-emerald-400 font-mono">Admin: EMP001 / password123</p>
            <p className="text-xs text-blue-400 font-mono">Staff: EMP016 / password123</p>
          </div>
        </div>

        <p className="text-center text-xs text-slate-600 mt-6">
          © 2026 Paraline Software. Powered by AI.
        </p>
      </div>
    </div>
  );
}
