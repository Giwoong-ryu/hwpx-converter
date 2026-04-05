"use client";

import { useState } from "react";
import { useForm } from "@/context/FormContext";
import { aiMap, generateDoc, downloadBlob, GaugeEmptyError } from "@/lib/api";
import FileUpload from "@/components/ui/FileUpload";
import { Wand2, Download, Loader2, CheckCircle2, ChevronDown, ChevronUp, ImageOff, Sparkles, PenLine } from "lucide-react";

interface AiMappingTabProps {
  onGaugeEmpty?: (data: { errorCode: string; plan: string; gaugePct: number }) => void;
}

export default function AiMappingTab({ onGaugeEmpty }: AiMappingTabProps = {}) {
  const { fileId, isAnalyzed, docType, smartFields } = useForm();
  const [text, setText] = useState("");
  const [contentFile, setContentFile] = useState<File | null>(null);
  const [smartValues, setSmartValues] = useState<Record<string, string>>({});
  const [mode, setMode] = useState<"smart" | "free">("smart");
  const [mappings, setMappings] = useState<[string, string][]>([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");
  const [showDetail, setShowDetail] = useState(false);
  const [stripImages, setStripImages] = useState(true);
  const [outputFormat, setOutputFormat] = useState<"hwpx" | "hwp" | "docx">("hwpx");
  const [isGeneration, setIsGeneration] = useState(false);
  const [coverage, setCoverage] = useState<{ total_fields: number; mapped: number; coverage_pct: number } | null>(null);

  const buildSmartPrompt = (): string => {
    const parts = smartFields
      .filter((f) => smartValues[f.key]?.trim())
      .map((f) => `${f.label}: ${smartValues[f.key].trim()}`);
    return `${docType} 써줘. ${parts.join(", ")}`;
  };

  const hasSmartInput = smartFields.some((f) => smartValues[f.key]?.trim());
  const useSmartMode = mode === "smart" && docType && smartFields.length > 0;

  const doMap = async () => {
    if (!fileId) return;
    const prompt = useSmartMode ? buildSmartPrompt() : text;
    if (!prompt && !contentFile) return;
    setLoading(true);
    setError("");
    try {
      const res = await aiMap(fileId, prompt, contentFile || undefined);
      setMappings(Object.entries(res.mappings));
      setIsGeneration(res.is_generation || false);
      setCoverage(res.coverage || null);
      setShowDetail(false);
    } catch (e: unknown) {
      if (e instanceof GaugeEmptyError) {
        onGaugeEmpty?.({ errorCode: e.error_code, plan: e.plan, gaugePct: e.gauge_pct });
        return;
      }
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
      {!isAnalyzed && (
        <div className="text-sm px-3 py-2 rounded-xl inline-flex items-center gap-1 bg-[#DBEAFE] text-[#1E40AF] font-medium">
          왼쪽에서 양식을 먼저 분석해주세요
        </div>
      )}

      {/* 스마트 모드: 문서 종류가 추론되었을 때 */}
      {useSmartMode ? (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles size={16} className="text-[#2563EB]" />
              <span className="text-sm font-bold text-[#1a1c1b]">
                이 양식은 <span className="text-[#2563EB]">{docType}</span>로 보입니다
              </span>
            </div>
            <button
              onClick={() => setMode("free")}
              className="text-[11px] text-[#57423c]/50 hover:text-[#2563EB] flex items-center gap-1 transition-colors"
            >
              <PenLine size={10} /> 직접 입력
            </button>
          </div>
          <p className="text-xs text-[#57423c]/60">아래 정보만 입력하면 AI가 나머지를 채워드립니다.</p>
          <div className="space-y-2">
            {smartFields.map((f) => (
              <div key={f.key} className="flex items-center gap-2">
                <label className="text-xs text-[#57423c] w-24 shrink-0 text-right font-medium">{f.label}</label>
                <input
                  type="text"
                  placeholder={f.placeholder}
                  value={smartValues[f.key] || ""}
                  onChange={(e) => setSmartValues((p) => ({ ...p, [f.key]: e.target.value }))}
                  className="flex-1 border border-[#93C5FD]/40 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:border-[#1E40AF]/40 transition-colors"
                />
              </div>
            ))}
          </div>
          <button
            onClick={doMap}
            disabled={loading || !isAnalyzed || !hasSmartInput}
            className="w-full bg-gradient-to-r from-[#2563EB] to-[#1E40AF] text-white py-3 rounded-xl font-semibold text-sm hover:opacity-90 disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-all active:scale-[0.98]"
          >
            {loading ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
            {loading ? "AI 작성 중..." : "스마트 작성하기"}
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="text-base text-[#57423c] space-y-1">
              <p className="font-semibold text-[#1a1c1b]">&quot;써줘&quot;라고 입력하면 AI가 대신 작성합니다.</p>
              <p className="text-sm">또는 채울 내용을 직접 붙여넣을 수도 있습니다. <span className="text-[#57423c]/70">Google AI 사용 · 학습에 미사용</span></p>
            </div>
            {docType && (
              <button
                onClick={() => setMode("smart")}
                className="text-[11px] text-[#57423c]/50 hover:text-[#2563EB] flex items-center gap-1 transition-colors shrink-0"
              >
                <Sparkles size={10} /> 스마트 입력
              </button>
            )}
          </div>
          <textarea
            className="w-full border border-[#93C5FD]/40 rounded-xl p-3 text-sm resize-y focus:outline-none focus:border-[#1E40AF]/40 bg-white transition-colors"
            rows={2}
            placeholder={"예: 온라인 교육 플랫폼 사업계획서 써줘\n예: 회사명: 주식회사 OO, 대표자: 홍길동, 설립일: 2025.01.01"}
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
          <div>
            <FileUpload
              accept=".txt,.xlsx,.xls,.docx,.csv,.json,.md"
              label="또는 내용이 담긴 파일 업로드 (txt, xlsx, docx, csv)"
              onFiles={(f) => setContentFile(f[0])}
            />
          </div>
          <button
            onClick={doMap}
            disabled={loading || !isAnalyzed || (!text && !contentFile)}
            className="w-full bg-gradient-to-r from-[#2563EB] to-[#1E40AF] text-white py-3 rounded-xl font-semibold text-sm hover:opacity-90 disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-all active:scale-[0.98]"
          >
            {loading ? <Loader2 size={16} className="animate-spin" /> : <Wand2 size={16} />}
            {loading ? "AI 작성 중..." : "AI 자동 채우기"}
          </button>
        </div>
      )}

      {error && <div className="text-sm text-red-600 bg-red-50 p-3 rounded-xl">{error}</div>}

      {mappings.length > 0 && (
        <div className="border border-[#93C5FD]/50 rounded-xl overflow-hidden">
          {/* AI 생성 모드 경고 */}
          {isGeneration && (
            <div className="bg-amber-50 border-b border-amber-200 px-4 py-3 text-sm text-amber-800">
              <strong>AI가 작성한 내용입니다.</strong> 이름, 날짜, 금액, 수치 등은 실제와 다를 수 있습니다. 반드시 확인 후 사용하세요.
            </div>
          )}
          {/* 커버리지 정보 */}
          {coverage && (
            <div className="bg-[#f0fdf4] px-4 py-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle2 size={18} className="text-emerald-600" />
                <span className="text-sm font-semibold text-[#1a1c1b]">{mappings.length}개 항목 매핑 완료</span>
              </div>
              <span className="text-xs text-[#57423c]">
                전체 {coverage.total_fields}개 필드 중 {coverage.mapped}개 매핑 ({coverage.coverage_pct}%)
              </span>
            </div>
          )}
          {!coverage && (
          <div className="bg-[#f0fdf4] px-4 py-3 flex items-center gap-2">
            <CheckCircle2 size={18} className="text-emerald-600" />
            <span className="text-sm font-semibold text-[#1a1c1b]">{mappings.length}개 항목 매핑 완료</span>
          </div>
          )}

          <div className="p-3 space-y-2">
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 text-xs text-[#57423c] cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={stripImages}
                  onChange={(e) => setStripImages(e.target.checked)}
                  className="rounded accent-[#1E40AF]"
                />
                <ImageOff size={14} />
                원본 이미지 제거
              </label>
              <div className="flex items-center gap-1 text-xs text-[#57423c]">
                <span>저장 형식:</span>
                {(["hwpx", "hwp", "docx"] as const).map((fmt) => (
                  <button
                    key={fmt}
                    onClick={() => setOutputFormat(fmt)}
                    className={`px-2 py-0.5 rounded-lg text-xs font-semibold transition-colors ${
                      outputFormat === fmt
                        ? "bg-[#1a1c1b] text-white"
                        : "bg-[#f4f4f1] text-[#57423c] hover:bg-[#e2e3e0]"
                    }`}
                  >{fmt.toUpperCase()}</button>
                ))}
              </div>
            </div>

            <button
              onClick={doGenerate}
              disabled={generating}
              className="w-full bg-[#1a1c1b] text-white py-3 rounded-xl font-semibold text-sm hover:bg-[#2f312f] disabled:opacity-60 flex items-center justify-center gap-2 transition-all active:scale-[0.98]"
            >
              {generating ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
              {generating ? "생성 중..." : "문서 만들기"}
            </button>

            <button
              onClick={() => setShowDetail(!showDetail)}
              className="w-full text-xs text-[#57423c]/80 hover:text-[#1E40AF] flex items-center justify-center gap-1 py-1 transition-colors"
            >
              {showDetail ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              {showDetail ? "상세 접기" : "매핑 상세 보기"}
            </button>
          </div>

          {showDetail && (
            <table className="w-full text-sm border-t border-[#93C5FD]/50">
              <thead>
                <tr className="border-b border-[#93C5FD]/50">
                  <th className="text-left px-4 py-2 text-[#1a1c1b] font-medium text-xs">원본</th>
                  <th className="text-left px-4 py-2 text-[#1a1c1b] font-medium text-xs">변경</th>
                </tr>
              </thead>
              <tbody>
                {mappings.map(([old, val], i) => (
                  <tr key={i} className="border-b border-[#93C5FD]/40 hover:bg-[#f4f4f1]/50">
                    <td className="px-4 py-2 text-[#57423c] text-xs">{old.length > 40 ? old.slice(0, 40) + "..." : old}</td>
                    <td className="px-4 py-1">
                      <input
                        className="w-full border border-[#93C5FD]/400 rounded-lg px-2 py-1 text-xs focus:outline-none focus:border-[#1E40AF]/40 bg-white"
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
