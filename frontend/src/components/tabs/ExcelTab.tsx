"use client";

import { useState } from "react";
import { analyzeExcel, excelBatch, downloadBlob } from "@/lib/api";
import FileUpload from "@/components/ui/FileUpload";
import { Loader2, Download, FileSpreadsheet, ArrowRight } from "lucide-react";

export default function ExcelTab() {
  const [template, setTemplate] = useState<File | null>(null);
  const [templateId, setTemplateId] = useState<string | null>(null);
  const [analyzed, setAnalyzed] = useState(false);
  const [cellCount, setCellCount] = useState(0);
  const [dataFile, setDataFile] = useState<File | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");

  const doAnalyze = async () => {
    if (!template) return;
    setAnalyzing(true);
    setError("");
    try {
      const res = await analyzeExcel(template);
      setTemplateId(res.file_id);
      setCellCount(res.cell_count);
      setAnalyzed(true);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "분석 실패");
    } finally {
      setAnalyzing(false);
    }
  };

  const doGenerate = async () => {
    if (!templateId || !dataFile) return;
    setGenerating(true);
    setError("");
    try {
      const blob = await excelBatch(templateId, dataFile);
      downloadBlob(blob, "DocFlow_excel_batch.zip");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "생성 실패");
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="rounded-xl p-4 bg-[#f4f4f1]">
        <p className="text-base font-semibold text-[#1a1c1b]">
          엑셀 양식에 데이터를 채워 여러 개를 한번에 만듭니다.
        </p>
        <p className="text-sm mt-1 text-[#57423c]">
          예: 급여명세서 양식 + 직원명단 엑셀 = 급여명세서 100개. 한글 양식과 별개로 동작합니다.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-sm font-medium block mb-1.5 text-[#1a1c1b]">
            <FileSpreadsheet size={12} className="inline mr-1" />
            엑셀 양식 (서식이 있는 원본)
          </label>
          <FileUpload accept=".xlsx,.xls" label="양식 엑셀 (.xlsx)" onFiles={(f) => { setTemplate(f[0]); setAnalyzed(false); }} />
        </div>
        <div>
          <label className="text-sm font-medium block mb-1.5 text-[#1a1c1b]">
            <FileSpreadsheet size={12} className="inline mr-1" />
            데이터 엑셀 (채울 내용)
          </label>
          <FileUpload accept=".xlsx,.xls" label="데이터 엑셀 (.xlsx)" onFiles={(f) => setDataFile(f[0])} />
        </div>
      </div>

      {!analyzed ? (
        <button
          onClick={doAnalyze}
          disabled={analyzing || !template}
          className="w-full bg-gradient-to-r from-[#2563EB] to-[#1E40AF] text-white py-2.5 rounded-xl font-semibold text-sm hover:opacity-90 disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-all active:scale-[0.98]"
        >
          {analyzing ? <Loader2 size={14} className="animate-spin" /> : <ArrowRight size={14} />}
          {analyzing ? "분석 중..." : "양식 분석"}
        </button>
      ) : (
        <>
          <div className="bg-[#f0fdf4] border border-emerald-200/50 text-emerald-700 rounded-xl px-3 py-2 text-xs">
            양식에서 {cellCount}개 셀 발견. 데이터 엑셀을 올리고 생성하세요.
          </div>
          <button
            onClick={doGenerate}
            disabled={generating || !dataFile}
            className="w-full bg-[#1a1c1b] text-white py-2.5 rounded-xl font-semibold text-sm hover:bg-[#2f312f] disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-all active:scale-[0.98]"
          >
            {generating ? <Loader2 size={14} className="animate-spin" /> : <Download size={14} />}
            {generating ? "생성 중..." : "엑셀 대량 생성"}
          </button>
        </>
      )}

      {error && <div className="text-xs text-red-600 bg-red-50 p-2 rounded-xl">{error}</div>}
    </div>
  );
}
