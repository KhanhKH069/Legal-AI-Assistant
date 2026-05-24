'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children?: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export default class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="p-8 text-center mt-20">
          <div className="inline-block p-6 rounded-2xl glass-card text-left max-w-lg border-red-500/30 border">
            <h2 className="text-xl font-bold text-red-400 mb-2">Đã xảy ra lỗi hiển thị (Rendering Error)</h2>
            <p className="text-slate-300 text-sm mb-4">
              Giao diện trang này đã gặp sự cố không mong muốn. Vui lòng tải lại trang hoặc liên hệ quản trị viên.
            </p>
            <div className="bg-black/50 p-3 rounded text-xs text-red-300 font-mono overflow-auto max-h-32">
              {this.state.error?.message}
            </div>
            <button
              className="mt-6 w-full py-2 bg-red-500/20 hover:bg-red-500/30 text-red-300 rounded-lg transition-colors text-sm font-medium"
              onClick={() => window.location.reload()}
            >
              Tải lại trang
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
