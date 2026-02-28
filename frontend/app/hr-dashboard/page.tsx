"use client";

import React, { useEffect, useState } from "react";
import "../globals.css";
import { listScreeningResults, runScreening } from "../../lib/api";
import type { ScreeningResult } from "../../lib/types";

export default function HrDashboardPage() {
  const [results, setResults] = useState<ScreeningResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);
  const [filterPosition, setFilterPosition] = useState("");
  const [filterRecommendation, setFilterRecommendation] = useState<string>("ALL");

  async function load() {
    setLoading(true);
    try {
      const data = await listScreeningResults({
        position: filterPosition || undefined,
        recommendation:
          filterRecommendation === "ALL" ? undefined : filterRecommendation
      });
      setResults(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [filterPosition, filterRecommendation]);

  async function handleRunAll() {
    setRunning(true);
    try {
      await runScreening();
      await load();
    } catch (e) {
      console.error(e);
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="max-w-5xl mx-auto py-10">
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="mb-4 flex items-center justify-between">
          <h1 className="text-lg font-semibold">📊 HR Dashboard - Screening</h1>
          <button
            onClick={handleRunAll}
            disabled={running}
            className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
          >
            {running ? "Đang chạy..." : "Chạy screening tất cả NEW"}
          </button>
        </div>

        <div className="mb-4 flex flex-wrap items-end gap-3 text-sm">
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-700">
              Vị trí
            </label>
            <input
              className="rounded-md border border-slate-300 px-3 py-1 text-sm"
              value={filterPosition}
              onChange={(e) => setFilterPosition(e.target.value)}
              placeholder="VD: Software Engineer"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-700">
              Recommendation
            </label>
            <select
              className="rounded-md border border-slate-300 px-3 py-1 text-sm"
              value={filterRecommendation}
              onChange={(e) => setFilterRecommendation(e.target.value)}
            >
              <option value="ALL">Tất cả</option>
              <option value="STRONG_PASS">STRONG_PASS</option>
              <option value="PASS">PASS</option>
              <option value="MAYBE">MAYBE</option>
              <option value="REJECT">REJECT</option>
            </select>
          </div>
        </div>

        {loading && (
          <div className="mb-2 text-sm text-slate-500">
            Đang tải kết quả screening...
          </div>
        )}

        <div className="space-y-2">
          {results.map((r) => (
            <div
              key={r.id}
              className="rounded-lg border border-slate-200 bg-slate-50 p-3"
            >
              <div className="font-semibold">
                Applicant #{r.applicant_id} – {r.position}
              </div>
              <div className="text-sm text-slate-700">
                Score: {r.total_score}/{r.max_score} ({r.percentage}%)
              </div>
              <div className="text-sm">
                Recommendation: <span className="font-medium">{r.recommendation}</span>
              </div>
              <div className="text-sm">Action: {r.action}</div>
            </div>
          ))}

          {!loading && results.length === 0 && (
            <div className="text-sm text-slate-500">
              Chưa có kết quả screening. Hãy chạy screening hoặc thêm ứng viên.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

