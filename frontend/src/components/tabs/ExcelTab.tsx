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
      <div className="rounded-xl p-4 bg-gray-50">
        <p className="text-sm font-medium text-gray-700">
          엑셀 양식에 데이터를 채워 여러 개를 한번에 만듭니다.
        </p>
        <p className="text-xs mt-1 text-gray-800">
          예: 급여명세서 양식 + 직원명단 엑셀 = 급여명세서 100개. 한글 양식과 별개로 동작합니다.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-xs font-medium block mb-1.5 text-gray-800">
            <FileSpreadsheet size={12} className="inline mr-1" />
            엑셀 양식 (서식이 있는 원본)
          </label>
          <FileUpload accept=".xlsx,.xls" label="양식 엑셀 (.xlsx)" onFiles={(f) => { setTemplate(f[0]); setAnalyzed(false); }} />
        </div>
        <div>
          <label className="text-xs font-medium block mb-1.5 text-gray-800">
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
          className="bg-black hover:bg-gray-800 w-full text-white py-2.5 rounded-xl font-semibold text-sm disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {analyzing ? <Loader2 size={14} className="animate-spin" /> : <ArrowRight size={14} />}
          {analyzing ? "분석 중..." : "양식 분석"}
        </button>
      ) : (
        <>
          <div className="bg-green-50 border border-green-100 text-green-700 rounded-lg px-3 py-2 text-xs">
            양식에서 {cellCount}개 셀 발견. 데이터 엑셀을 올리고 생성하세요.
          </div>
          <button
            onClick={doGenerate}
            disabled={generating || !dataFile}
            className="bg-black hover:bg-gray-800 w-full text-white py-2.5 rounded-xl font-semibold text-sm disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {generating ? <Loader2 size={14} className="animate-spin" /> : <Download size={14} />}
            {generating ? "생성 중..." : "엑셀 대량 생성"}
          </button>
        </>
      )}

      {error && <div className="text-xs text-red-500 bg-red-50 p-2 rounded-lg">{error}</div>}
    </div>
  );
}
