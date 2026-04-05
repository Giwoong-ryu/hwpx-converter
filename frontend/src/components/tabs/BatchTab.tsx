"use client";

import { useState } from "react";
import { useForm } from "@/context/FormContext";
import { batchMapHeaders, batchGenerateMapped, downloadBlob } from "@/lib/api";
import FileUpload from "@/components/ui/FileUpload";
import { Loader2, Download, Sparkles, ArrowRight } from "lucide-react";

interface Mapping {
  header: string;
  form_text: string;
}

export default function BatchTab() {
  const { fileId, isAnalyzed } = useForm();
  const [excel, setExcel] = useState<File | null>(null);
  const [excelId, setExcelId] = useState<string | null>(null);
  const [mappings, setMappings] = useState<Mapping[]>([]);
  const [rowCount, setRowCount] = useState(0);
  const [sampleRow, setSampleRow] = useState<string[]>([]);
  const [mapping, setMapping] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");

  const doMap = async () => {
    if (!fileId || !excel) return;
    setMapping(true);
    setError("");
    try {
      const res = await batchMapHeaders(fileId, excel);
      setExcelId(res.excel_id);
      setMappings(res.mappings);
      setRowCount(res.row_count);
      setSampleRow(res.sample_row);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "매핑 실패");
    } finally {
      setMapping(false);
    }
  };

  const doGenerate = async () => {
    if (!fileId || !excelId) return;
    setGenerating(true);
    setError("");
    try {
      const validMappings = mappings.filter((m) => m.form_text);
      const blob = await batchGenerateMapped(fileId, excelId, validMappings);
      downloadBlob(blob, "DocFlow_batch.zip");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "생성 실패");
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-4">
      <p className="text-base text-[#57423c]">
        엑셀 파일을 올리면 AI가 양식과 자동 매칭하여 문서를 한번에 만들어줍니다.
        <span className="text-base block mt-1 text-[#57423c]">
          예: 직원명단.xlsx + 위촉장 양식 = 위촉장 100개
        </span>
      </p>
      {!isAnalyzed && (
        <div className="text-base px-3 py-2 rounded-xl inline-flex items-center gap-1 bg-[#DBEAFE] text-[#1E40AF] font-medium">
          왼쪽에서 양식을 먼저 분석해주세요
        </div>
      )}

      <div>
        <FileUpload accept=".xlsx,.xls" label="엑셀 파일 (.xlsx) — 직원명단, 데이터 등" onFiles={(f) => setExcel(f[0])} />
      </div>

      <button
        onClick={doMap}
        disabled={mapping || !excel || !isAnalyzed}
        className="w-full bg-gradient-to-r from-[#2563EB] to-[#1E40AF] text-white py-2.5 rounded-xl font-semibold text-sm hover:opacity-90 disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-all active:scale-[0.98]"
      >
        {mapping ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />}
        {mapping ? "AI 매칭 중..." : "AI 자동 매칭"}
      </button>

      {error && <div className="text-sm text-red-600 bg-red-50 p-2 rounded-xl">{error}</div>}

      {mappings.length > 0 && (
        <div className="space-y-3">
          <div className="rounded-xl overflow-hidden border border-[#93C5FD]/50">
            <div className="px-3 py-2 flex justify-between items-center bg-[#f4f4f1]">
              <span className="text-xs font-bold text-[#1a1c1b]">
                매칭 결과 — {rowCount}개 문서 생성 예정
              </span>
              <span className="text-xs text-[#57423c]/80">틀린 부분은 직접 수정 가능</span>
            </div>
            <table className="w-full text-xs">
              <thead>
                <tr className="bg-[#f9f9f6]">
                  <th className="text-left px-3 py-1.5 font-semibold text-[#1a1c1b]">엑셀 헤더</th>
                  <th className="px-2 py-1.5 text-[#57423c]/70"><ArrowRight size={12} /></th>
                  <th className="text-left px-3 py-1.5 font-semibold text-[#1a1c1b]">양식에서 바꿀 텍스트</th>
                  <th className="text-left px-3 py-1.5 font-semibold text-[#57423c]/80">샘플</th>
                </tr>
              </thead>
              <tbody>
                {mappings.map((m, i) => (
                  <tr key={i} className="border-t border-[#93C5FD]/50">
                    <td className="px-3 py-1.5 font-medium text-[#1a1c1b]">{m.header}</td>
                    <td className="px-2 text-center text-[#57423c]/70"><ArrowRight size={10} /></td>
                    <td className="px-3 py-1">
                      <input
                        className="w-full border border-[#93C5FD]/400 rounded-lg px-2 py-1 text-xs focus:outline-none focus:border-[#1E40AF]/40 bg-white"
                        value={m.form_text}
                        onChange={(e) => {
                          const copy = [...mappings];
                          copy[i] = { ...m, form_text: e.target.value };
                          setMappings(copy);
                        }}
                      />
                    </td>
                    <td className="px-3 py-1.5 text-xs text-[#57423c]/80">
                      {sampleRow[i] || ""}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <button
            onClick={doGenerate}
            disabled={generating}
            className="w-full bg-[#1a1c1b] text-white py-2.5 rounded-xl font-semibold text-sm hover:bg-[#2f312f] disabled:opacity-60 flex items-center justify-center gap-2 transition-all active:scale-[0.98]"
          >
            {generating ? <Loader2 size={14} className="animate-spin" /> : <Download size={14} />}
            {generating ? "생성 중..." : `${rowCount}개 문서 생성`}
          </button>
        </div>
      )}
    </div>
  );
}
