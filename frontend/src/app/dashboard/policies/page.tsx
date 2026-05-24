'use client';

import React, { useState } from 'react';
import { uploadPolicy } from '@/lib/api';

export default function PoliciesPage() {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setIsUploading(true);
    setMessage(null);

    try {
      const res = await uploadPolicy(file);
      setMessage({ text: res.message || 'Tải lên thành công!', type: 'success' });
      setFile(null); // Reset
    } catch (err: any) {
      setMessage({ text: err.message || 'Có lỗi xảy ra khi tải lên.', type: 'error' });
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400 mb-2 drop-shadow-sm">
            Quản Lý Tài Liệu & Nội Quy
          </h1>
          <p className="text-slate-400">
            Tải lên các file PDF nội quy để huấn luyện AI Trợ lý Nhân sự.
          </p>
        </div>
      </div>

      <div className="bg-slate-800/40 backdrop-blur-md border border-slate-700/50 rounded-xl p-8 shadow-xl">
        <h2 className="text-xl font-semibold text-white mb-6">Huấn luyện RAG Knowledge Base</h2>

        <div className="border-2 border-dashed border-slate-600 rounded-xl p-10 flex flex-col items-center justify-center bg-slate-900/30 hover:bg-slate-900/50 transition-colors">
          <svg className="w-12 h-12 text-slate-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>
          </svg>

          <label className="cursor-pointer bg-blue-600 hover:bg-blue-500 text-white px-6 py-2 rounded-full font-medium transition-colors mb-4 shadow-[0_0_15px_rgba(37,99,235,0.3)]">
            Chọn file PDF
            <input
              type="file"
              className="hidden"
              accept=".pdf"
              onChange={handleFileChange}
            />
          </label>

          {file ? (
            <div className="text-emerald-400 flex items-center gap-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
              Đã chọn: {file.name}
            </div>
          ) : (
            <p className="text-slate-500 text-sm">Chỉ hỗ trợ file định dạng PDF</p>
          )}
        </div>

        <div className="mt-6 flex justify-end">
          <button
            onClick={handleUpload}
            disabled={!file || isUploading}
            className={`px-6 py-2.5 rounded-lg font-medium transition-all shadow-lg flex items-center gap-2 ${
              !file || isUploading
                ? 'bg-slate-700 text-slate-400 cursor-not-allowed'
                : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-[0_0_15px_rgba(16,185,129,0.3)]'
            }`}
          >
            {isUploading ? (
              <>
                <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Đang xử lý PDF...
              </>
            ) : (
              'Bắt đầu Huấn luyện AI'
            )}
          </button>
        </div>

        {message && (
          <div className={`mt-6 p-4 rounded-lg flex items-start gap-3 border ${
            message.type === 'success'
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
              : 'bg-rose-500/10 border-rose-500/30 text-rose-400'
          }`}>
            <svg className="w-5 h-5 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {message.type === 'success'
                ? <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                : <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              }
            </svg>
            <div>
              <h4 className="font-medium mb-1">{message.type === 'success' ? 'Hoàn tất!' : 'Lỗi'}</h4>
              <p className="text-sm opacity-90">{message.text}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
