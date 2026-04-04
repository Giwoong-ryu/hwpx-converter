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
      <p className="text-base text-[#57423c]">
        같은 양식에서 날짜만 바꿔서 월별/주별 문서를 한번에 만듭니다.
        <span className="text-sm block mt-1 text-[#57423c]">예: 1월~12월 월간보고서 12개를 한번에 생성</span>
      </p>
      {!isAnalyzed && (
        <div className="text-sm px-3 py-2 rounded-xl inline-flex items-center gap-1 bg-[#DBEAFE] text-[#1E40AF] font-medium">
          왼쪽에서 양식을 먼저 분석해주세요
        </div>
      )}

      <input className="w-full border border-[#93C5FD]/400 rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-[#1E40AF]/40 bg-white transition-colors" placeholder="문서에서 바꿀 날짜 (예: 2025.08.03)" value={dateText} onChange={(e) => setDateText(e.target.value)} />

      <div className="grid grid-cols-2 gap-3">
        <input className="border border-[#93C5FD]/400 rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-[#1E40AF]/40 bg-white transition-colors" placeholder="시작일 (2026-01-01)" value={start} onChange={(e) => setStart(e.target.value)} />
        <input className="border border-[#93C5FD]/400 rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-[#1E40AF]/40 bg-white transition-colors" placeholder="종료일 (2026-12-01)" value={end} onChange={(e) => setEnd(e.target.value)} />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-sm text-[#1a1c1b] font-medium mb-1 block">간격</label>
          <select className="w-full border border-[#93C5FD]/400 rounded-xl px-3 py-2 text-sm bg-white focus:outline-none focus:border-[#1E40AF]/40 transition-colors" value={interval} onChange={(e) => setInterval(e.target.value)}>
            <option value="monthly">매월</option>
            <option value="weekly">매주</option>
          </select>
        </div>
        <div>
          <label className="text-sm text-[#1a1c1b] font-medium mb-1 block">날짜 형식</label>
          <input className="w-full border border-[#93C5FD]/400 rounded-xl px-3 py-2 text-sm bg-white focus:outline-none focus:border-[#1E40AF]/40 transition-colors" value={fmt} onChange={(e) => setFmt(e.target.value)} />
        </div>
      </div>

      <button
        onClick={doGenerate}
        disabled={loading || !isAnalyzed || !dateText || !start || !end}
        className="w-full bg-gradient-to-r from-[#2563EB] to-[#1E40AF] text-white py-3 rounded-xl font-semibold text-sm hover:opacity-90 disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-all active:scale-[0.98]"
      >
        {loading ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
        {loading ? "생성 중..." : "정기 문서 생성"}
      </button>

      {error && <div className="text-sm text-red-600 bg-red-50 p-3 rounded-xl">{error}</div>}
    </div>
  );
}
