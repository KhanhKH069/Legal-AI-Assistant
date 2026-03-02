"use client";

import React, { useState } from "react";
import "../globals.css";
import { createApplicant, uploadCv, runScreening } from "../../lib/api";


export default function ApplyPage() {
  const [form, setForm] = useState({ name: "", email: "", phone: "", position: "" });
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function handleChange(e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) {
    const { name, value } = e.target as HTMLInputElement;
    setForm((prev) => ({ ...prev, [name]: value }));
  }
  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0] ?? null;
    setFile(f);
  }
  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setStatus(null);
    setLoading(true);
    try {
      let cvPath: string | null = null;
      if (file) {
        const uploaded = await uploadCv(file);
        cvPath = uploaded.cv_path;
      }
      const applicant = await createApplicant({
        name: form.name,
        email: form.email,
        phone: form.phone,
        position: form.position,
        cv_path: cvPath,
        cv_url: null
      });

      // trigger screening for the returned applicant id
      try {
        const resp = await runScreening(applicant.id);
        let recText = "";
        if (resp.results && resp.results[0]) {
          recText = ` (${resp.results[0].recommendation})`;
        }
        setStatus(` Nộp hồ sơ thành công!${recText}`);
      } catch (_err) {
        // ignore screening failure in UI, backend logged it
        setStatus(" Nộp hồ sơ thành công!");
      }

      setForm({ name: "", email: "", phone: "", position: "" });
      setFile(null);
    } catch (e: any) {
      const msg = e.message || String(e);
      if (msg.includes("Failed to fetch")) {
        setStatus(" Lỗi: Không thể kết nối tới API. Hãy kiểm tra xem backend (mặc định http://localhost:8000) có đang chạy và có cho phép CORS không.");
      } else {
        setStatus(` Lỗi: ${msg}`);
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ minHeight: '100vh', background: '#f5f7fa', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: 32 }}>
        <div style={{
          width: 90,
          height: 90,
          background: 'linear-gradient(135deg, #27ae60 60%, #1e8449 100%)',
          borderRadius: '50%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 4px 32px 0 rgba(39,174,96,0.18)',
          marginBottom: 18,
          border: '4px solid #fff',
        }}>
          <svg width="54" height="54" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <rect x="2" y="7" width="20" height="10" rx="5" fill="#27ae60" stroke="#fff" strokeWidth="2.5"/>
            <path d="M7 17v2a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2v-2" stroke="#fff" strokeWidth="2.5"/>
            <circle cx="12" cy="12" r="3" fill="#fff"/>
          </svg>
        </div>
        <h1 style={{ fontSize: 32, fontWeight: 700, color: '#222', marginBottom: 6, letterSpacing: 1 }}>Ứng Tuyển Việc Làm</h1>
        <div style={{ color: '#666', fontSize: 16, marginBottom: 8, textAlign: 'center', maxWidth: 420 }}>
          Điền thông tin bên dưới và upload CV (PDF/DOCX). HR sẽ liên hệ lại trong 3–5 ngày làm việc.
        </div>
      </div>
      <div style={{ width: '100%', maxWidth: 520, background: '#fff', borderRadius: 18, boxShadow: '0 2px 16px 0 rgba(44,62,80,0.08)', padding: 0, border: '1px solid #e0e0e0' }}>
        <form onSubmit={handleSubmit} style={{ padding: 32, display: 'flex', flexDirection: 'column', gap: 18 }}>
          <div>
            <label style={{ fontWeight: 600, fontSize: 14, color: '#222', marginBottom: 4, display: 'block' }}>Họ và tên *</label>
            <input name="name" style={{ width: '100%', borderRadius: 8, border: '1px solid #e0e0e0', padding: '12px 16px', fontSize: 15, outline: 'none', marginTop: 2 }} value={form.name} onChange={handleChange} required />
          </div>
          <div>
            <label style={{ fontWeight: 600, fontSize: 14, color: '#222', marginBottom: 4, display: 'block' }}>Email *</label>
            <input type="email" name="email" style={{ width: '100%', borderRadius: 8, border: '1px solid #e0e0e0', padding: '12px 16px', fontSize: 15, outline: 'none', marginTop: 2 }} value={form.email} onChange={handleChange} required />
          </div>
          <div>
            <label style={{ fontWeight: 600, fontSize: 14, color: '#222', marginBottom: 4, display: 'block' }}>Số điện thoại *</label>
            <input name="phone" style={{ width: '100%', borderRadius: 8, border: '1px solid #e0e0e0', padding: '12px 16px', fontSize: 15, outline: 'none', marginTop: 2 }} value={form.phone} onChange={handleChange} required />
          </div>
          <div>
            <label style={{ fontWeight: 600, fontSize: 14, color: '#222', marginBottom: 4, display: 'block' }}>Vị trí ứng tuyển *</label>
            <select name="position" style={{ width: '100%', borderRadius: 8, border: '1px solid #e0e0e0', padding: '12px 16px', fontSize: 15, outline: 'none', marginTop: 2 }} value={form.position} onChange={handleChange} required>
                <option value="">-- Chọn vị trí --</option>
                <option value="Software Engineer">Software Engineer</option>
                <option value="Frontend Developer">Frontend Developer</option>
                <option value="Backend Developer">Backend Developer</option>
                <option value="QA Engineer">QA Engineer</option>
                <option value="Project Manager">Project Manager</option>
                <option value="Business Analyst">Business Analyst</option>
                <option value="HR Specialist">HR Specialist</option>
                <option value="AI Engineer">AI Engineer</option>
                <option value="AI Intern">AI Intern</option>
                <option value="DevOps Engineer">DevOps Engineer</option>
                <option value="Devops Intern">Devops Intern</option>
            </select>
          </div>
          <div>
            <label style={{ fontWeight: 600, fontSize: 14, color: '#222', marginBottom: 4, display: 'block' }}>Upload CV (PDF, DOCX)</label>
            <input type="file" accept=".pdf,.doc,.docx" onChange={handleFileChange} style={{ width: '100%', fontSize: 14, marginTop: 2 }} />
            <div style={{ color: '#888', fontSize: 12, marginTop: 2 }}>Kích thước tối đa 10MB. Hỗ trợ PDF, DOC, DOCX.</div>
          </div>
          <button type="submit" disabled={loading} style={{ marginTop: 8, width: '100%', borderRadius: 8, background: '#27ae60', color: '#fff', fontWeight: 700, fontSize: 16, padding: '12px 0', border: 'none', boxShadow: '0 2px 8px 0 rgba(39,174,96,0.08)', cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.7 : 1 }}>
            {loading ? 'Đang gửi...' : ' Nộp hồ sơ'}
          </button>
          {status && <div style={{ color: status.startsWith('') ? '#27ae60' : '#e74c3c', fontSize: 14, marginTop: 8 }}>{status}</div>}
        </form>
      </div>
    </div>
  );
}

