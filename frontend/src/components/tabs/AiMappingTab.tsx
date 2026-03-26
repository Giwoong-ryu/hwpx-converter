"use client";

import { useState } from "react";
import { useForm } from "@/context/FormContext";
import { aiMap, generateDoc, downloadBlob } from "@/lib/api";
import FileUpload from "@/components/ui/FileUpload";
import { Wand2, Download, Loader2, CheckCircle2, ChevronDown, ChevronUp, ImageOff } from "lucide-react";

export default function AiMappingTab() {
  const { fileId, isAnalyzed } = useForm();
  const [text, setText] = useState("");
  const [contentFile, setContentFile] = useState<File | null>(null);
  const [mappings, setMappings] = useState<[string, string][]>([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");
  const [showDetail, setShowDetail] = useState(false);
  const [stripImages, setStripImages] = useState(true);
  const [outputFormat, setOutputFormat] = useState<"hwpx" | "hwp" | "docx">("hwpx");

  const doMap = async () => {
    if (!fileId) return;
    setLoading(true);
    setError("");
    try {
      const res = await aiMap(fileId, text, contentFile || undefined);
      setMappings(Object.entries(res.mappings));
      setShowDetail(false);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "매핑 실패");
    } finally {
      setLoading(false);
    }
  };

  const doGenerate = async () => {
    if (!fileId) return;
    setGenerating(true);
    try {
      const repl: Record<string, string> = {};
      mappings.forEach(([old, val]) => { if (val.trim()) repl[old] = val; });
      const blob = await generateDoc(fileId, repl, stripImages, outputFormat);
      downloadBlob(blob, `EazyHWPX_result.${outputFormat}`);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "생성 실패");
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-4">
      <p className="text-sm text-gray-800">
        채울 내용을 텍스트로 붙여넣거나, &quot;써줘&quot;라고 입력하면 AI가 대신 작성합니다.
        <span className="text-xs text-gray-400 ml-1">Google AI 사용 · 학습에 미사용</span>
      </p>
      {!isAnalyzed && (
        <div className="text-xs px-3 py-2 rounded-lg inline-flex items-center gap-1 bg-gray-100 text-gray-600">
          왼쪽에서 양식을 먼저 분석해주세요
        </div>
      )}

      <textarea
        className="w-full border border-gray-200 rounded-lg p-3 text-sm resize-y focus:outline-none focus:border-gray-400"
        rows={2}
        placeholder={"회사명: 주식회사 OO\n대표자: 홍길동\n설립일: 2025.01.01\n주소: 서울시 강남구 ..."}
        value={text}
        onChange={(e) => setText(e.target.value)}
      />

      <FileUpload
        accept=".txt,.xlsx,.xls,.docx,.csv,.json,.md"
        label="또는 내용이 담긴 파일 업로드 (txt, xlsx, docx, csv)"
        onFiles={(f) => setContentFile(f[0])}
      />

      <button
        onClick={doMap}
        disabled={loading || !isAnalyzed || (!text && !contentFile)}
        className="w-full bg-black text-white py-3 rounded-lg font-semibold text-sm hover:bg-gray-800 disabled:cursor-not-allowed flex items-center justify-center gap-2"
      >
        {loading ? <Loader2 size={16} className="animate-spin" /> : <Wand2 size={16} />}
        {loading ? "AI 작성 중..." : "AI 자동 채우기"}
      </button>

      {error && <div className="text-sm text-red-500 bg-red-50 p-3 rounded-lg">{error}</div>}

      {mappings.length > 0 && (
        <div className="border border-gray-200 rounded-xl overflow-hidden">
          <div className="bg-green-50 px-4 py-3 flex items-center gap-2">
            <CheckCircle2 size={18} className="text-green-600" />
            <span className="text-sm font-semibold text-gray-800">{mappings.length}개 항목 매핑 완료</span>
          </div>

          <div className="p-3 space-y-2">
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 text-xs text-gray-700 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={stripImages}
                  onChange={(e) => setStripImages(e.target.checked)}
                  className="rounded"
                />
                <ImageOff size={14} />
                원본 이미지 제거
              </label>
              <div className="flex items-center gap-1 text-xs text-gray-700">
                <span>저장 형식:</span>
                {(["hwpx", "hwp", "docx"] as const).map((fmt) => (
                  <button
                    key={fmt}
                    onClick={() => setOutputFormat(fmt)}
                    className={`px-2 py-0.5 rounded ${outputFormat === fmt ? "bg-black text-white" : "bg-gray-100"}`}
                  >{fmt.toUpperCase()}</button>
                ))}
              </div>
            </div>

            <button
              onClick={doGenerate}
              disabled={generating}
              className="w-full bg-black text-white py-3 rounded-lg font-semibold text-sm hover:bg-gray-800 disabled:bg-gray-300 flex items-center justify-center gap-2"
            >
              {generating ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
              {generating ? "생성 중..." : "문서 만들기"}
            </button>

            <button
              onClick={() => setShowDetail(!showDetail)}
              className="w-full text-xs text-gray-500 hover:text-gray-700 flex items-center justify-center gap-1 py-1"
            >
              {showDetail ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              {showDetail ? "상세 접기" : "매핑 상세 보기"}
            </button>
          </div>

          {showDetail && (
            <table className="w-full text-sm border-t border-gray-100">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="text-left px-4 py-2 text-gray-800 font-medium text-xs">원본</th>
                  <th className="text-left px-4 py-2 text-gray-800 font-medium text-xs">변경</th>
                </tr>
              </thead>
              <tbody>
                {mappings.map(([old, val], i) => (
                  <tr key={i} className="border-b border-gray-50 hover:bg-gray-50/50">
                    <td className="px-4 py-2 text-gray-700 text-xs">{old.length > 40 ? old.slice(0, 40) + "..." : old}</td>
                    <td className="px-4 py-1">
                      <input
                        className="w-full border border-gray-200 rounded px-2 py-1 text-xs focus:outline-none focus:border-gray-400"
                        value={val}
                        onChange={(e) => {
                          const copy = [...mappings];
                          copy[i] = [old, e.target.value];
                          setMappings(copy);
                        }}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}
