"use client";

import { useState } from "react";
import { useForm } from "@/context/FormContext";
import { periodicGenerate, downloadBlob } from "@/lib/api";
import { Loader2, Download } from "lucide-react";

export default function PeriodicTab() {
  const { fileId, isAnalyzed } = useForm();
  const [dateText, setDateText] = useState("");
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [interval, setInterval] = useState("monthly");
  const [fmt, setFmt] = useState("%Y.%m.%d");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const doGenerate = async () => {
    if (!fileId) return;
    setLoading(true);
    setError("");
    try {
      const blob = await periodicGenerate(fileId, dateText, start, end, interval, fmt);
      downloadBlob(blob, "DocFlow_periodic.zip");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "생성 실패");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <p className="text-sm text-gray-800">
        같은 양식에서 날짜만 바꿔서 월별/주별 문서를 한번에 만듭니다.
        <span className="text-xs block mt-1 text-gray-600">예: 1월~12월 월간보고서 12개를 한번에 생성</span>
      </p>
      {!isAnalyzed && (
        <div className="text-xs px-3 py-2 rounded-lg inline-flex items-center gap-1 bg-gray-100 text-gray-600">
          왼쪽에서 양식을 먼저 분석해주세요
        </div>
      )}

      <input className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-gray-400" placeholder="문서에서 바꿀 날짜 (예: 2025.08.03)" value={dateText} onChange={(e) => setDateText(e.target.value)} />

      <div className="grid grid-cols-2 gap-3">
        <input className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-gray-400" placeholder="시작일 (2026-01-01)" value={start} onChange={(e) => setStart(e.target.value)} />
        <input className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-gray-400" placeholder="종료일 (2026-12-01)" value={end} onChange={(e) => setEnd(e.target.value)} />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-xs text-gray-800 mb-1 block">간격</label>
          <select className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm" value={interval} onChange={(e) => setInterval(e.target.value)}>
            <option value="monthly">매월</option>
            <option value="weekly">매주</option>
          </select>
        </div>
        <div>
          <label className="text-xs text-gray-800 mb-1 block">날짜 형식</label>
          <input className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm" value={fmt} onChange={(e) => setFmt(e.target.value)} />
        </div>
      </div>

      <button
        onClick={doGenerate}
        disabled={loading || !isAnalyzed || !dateText || !start || !end}
        className="w-full bg-black text-white py-3 rounded-lg font-semibold text-sm hover:bg-gray-800 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center gap-2"
      >
        {loading ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
        {loading ? "생성 중..." : "정기 문서 생성"}
      </button>

      {error && <div className="text-sm text-red-500 bg-red-50 p-3 rounded-lg">{error}</div>}
    </div>
  );
}
