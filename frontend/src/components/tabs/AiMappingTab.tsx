"use client";

import { useState, useEffect } from "react";
import { useForm } from "@/context/FormContext";
import { useAuth } from "@/context/AuthContext";
import { aiMap, generateDoc, downloadBlob, GaugeEmptyError, saveMapping, listMyMappings, loadMapping, deleteMapping, listPublicMappings, toggleLike, updateMappingPublic } from "@/lib/api";
import FileUpload from "@/components/ui/FileUpload";
import { Wand2, Download, Loader2, CheckCircle2, ChevronDown, ChevronUp, ImageOff, Sparkles, PenLine, Save, FolderOpen, Trash2, X, Heart, Globe, Lock } from "lucide-react";

interface AiMappingTabProps {
  onGaugeEmpty?: (data: { errorCode: string; plan: string; gaugePct: number }) => void;
}

export default function AiMappingTab({ onGaugeEmpty }: AiMappingTabProps = {}) {
  const { fileId, isAnalyzed, filename, fieldCount, docType, smartFields } = useForm();
  const { user } = useAuth();
  const [text, setText] = useState("");
  const [contentFiles, setContentFiles] = useState<File[]>([]);
  const [smartValues, setSmartValues] = useState<Record<string, string>>({});
  const [remember, setRemember] = useState(false);
  const [mode, setMode] = useState<"smart" | "free">("smart");

  // localStorage에서 기억된 값 불러오기
  useEffect(() => {
    try {
      const saved = localStorage.getItem("eazyhwpx_smart_remember");
      if (saved === "true") {
        setRemember(true);
        const vals = localStorage.getItem("eazyhwpx_smart_values");
        if (vals) setSmartValues(JSON.parse(vals));
      }
    } catch { /* localStorage 접근 불가 시 무시 */ }
  }, []);

  // 기억하기 ON일 때 값 변경 시 자동 저장
  useEffect(() => {
    if (!remember) return;
    try {
      localStorage.setItem("eazyhwpx_smart_values", JSON.stringify(smartValues));
    } catch { /* 무시 */ }
  }, [smartValues, remember]);

  const handleRememberToggle = (checked: boolean) => {
    setRemember(checked);
    try {
      if (checked) {
        localStorage.setItem("eazyhwpx_smart_remember", "true");
        localStorage.setItem("eazyhwpx_smart_values", JSON.stringify(smartValues));
      } else {
        localStorage.removeItem("eazyhwpx_smart_remember");
        localStorage.removeItem("eazyhwpx_smart_values");
      }
    } catch { /* 무시 */ }
  };
  const [mappings, setMappings] = useState<[string, string][]>([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");
  const [showDetail, setShowDetail] = useState(false);
  const [stripImages, setStripImages] = useState(false);
  const [outputFormat, setOutputFormat] = useState<"hwpx" | "hwp" | "docx">("hwpx");
  const [isGeneration, setIsGeneration] = useState(false);
  const [coverage, setCoverage] = useState<{ total_fields: number; mapped: number; coverage_pct: number } | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [showLoadModal, setShowLoadModal] = useState(false);
  const [loadTab, setLoadTab] = useState<"my" | "public">("my");
  const [savedList, setSavedList] = useState<{ id: number; form_name: string; form_field_count: number; created_at: string }[]>([]);
  const [publicList, setPublicList] = useState<{ id: number; form_name: string; form_field_count: number; likes: number; created_at: string; liked?: boolean }[]>([]);

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
    if (!prompt && contentFiles.length === 0) return;
    setLoading(true);
    setError("");
    try {
      const res = await aiMap(fileId, prompt, contentFiles.length > 0 ? contentFiles : undefined);
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

  const doSaveMapping = async (makePublic = false) => {
    if (!user || mappings.length === 0) return;
    setSaving(true);
    try {
      const obj: Record<string, string> = {};
      mappings.forEach(([k, v]) => { if (v.trim()) obj[k] = v; });
      const saved = await saveMapping(filename || "양식", obj, fieldCount || 0);
      if (makePublic && saved?.mapping?.id) {
        await updateMappingPublic(saved.mapping.id, true);
      }
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2000);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "매핑 저장 실패");
    } finally {
      setSaving(false);
    }
  };

  const doLoadMappings = async () => {
    try {
      const list = await listMyMappings();
      setSavedList(list);
      setLoadTab("my");
      setShowLoadModal(true);
    } catch {
      setError("저장된 매핑 목록을 불러올 수 없습니다.");
    }
  };

  const doLoadPublicMappings = async () => {
    try {
      const res = await listPublicMappings();
      setPublicList(res.mappings || []);
      setLoadTab("public");
      setShowLoadModal(true);
    } catch {
      setError("공개 매핑 목록을 불러올 수 없습니다.");
    }
  };

  const doToggleLike = async (id: number) => {
    if (!user) return;
    try {
      const res = await toggleLike(id);
      setPublicList((prev) =>
        prev.map((m) => m.id === id ? { ...m, likes: res.likes, liked: res.liked } : m)
      );
    } catch {
      // 무시
    }
  };

  const doApplyMapping = async (id: number) => {
    try {
      const res = await loadMapping(id);
      const m = res.mapping;
      if (m?.mappings) {
        setMappings(Object.entries(m.mappings));
        setShowLoadModal(false);
        setShowDetail(false);
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "매핑 불러오기 실패");
    }
  };

  const doDeleteMapping = async (id: number) => {
    try {
      await deleteMapping(id);
      setSavedList((prev) => prev.filter((m) => m.id !== id));
    } catch {
      setError("매핑 삭제 실패");
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
        <div className="text-base px-3 py-2 rounded-xl inline-flex items-center gap-1 bg-[#DBEAFE] text-[#1E40AF] font-medium">
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
              className="text-xs text-[#57423c]/50 hover:text-[#2563EB] flex items-center gap-1 transition-colors"
            >
              <PenLine size={10} /> 직접 입력
            </button>
          </div>
          <p className="text-sm text-[#57423c]/60">아래 정보를 입력하거나 파일을 올리면 AI가 양식에 맞춰 채워드립니다.</p>

          {/* 좌우 분리: 입력 필드 | 파일 업로드 */}
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
            {/* 왼쪽: 추천 입력 필드 (3/5) */}
            <div className="lg:col-span-3 space-y-2.5">
              {smartFields.map((f) => (
                <div key={f.key}>
                  <label className="text-xs text-[#57423c] font-medium mb-1 block">{f.label}</label>
                  <input
                    type="text"
                    name={`smart_${f.key}`}
                    autoComplete="on"
                    placeholder={f.placeholder}
                    value={smartValues[f.key] || ""}
                    onChange={(e) => setSmartValues((p) => ({ ...p, [f.key]: e.target.value }))}
                    className="w-full border border-[#93C5FD]/40 rounded-lg px-3 py-2.5 text-sm bg-white focus:outline-none focus:border-[#1E40AF]/40 transition-colors"
                  />
                </div>
              ))}
              <label className="flex items-center gap-2 cursor-pointer select-none group mt-1">
                <input
                  type="checkbox"
                  checked={remember}
                  onChange={(e) => handleRememberToggle(e.target.checked)}
                  className="rounded accent-[#2563EB] w-3.5 h-3.5"
                />
                <span className="text-xs text-[#57423c]/60 group-hover:text-[#57423c] transition-colors">
                  이 기기에서 내 정보 기억하기
                </span>
                {remember && (
                  <span className="text-xs text-[#57423c]/40">서버에 전송되지 않습니다</span>
                )}
              </label>
            </div>

            {/* 오른쪽: 파일 업로드 (2/5) */}
            <div className="lg:col-span-2">
              <p className="text-xs text-[#57423c] font-medium mb-1">또는 파일로 올리기</p>
              <div className="border-2 border-dashed border-[#93C5FD]/40 rounded-xl p-4 bg-[#FAFBFF] min-h-[120px] flex flex-col">
                <FileUpload
                  accept=".txt,.xlsx,.xls,.docx,.csv,.json,.md"
                  label="엑셀, 워드, 텍스트 등"
                  multiple
                  onFiles={(f) => setContentFiles((prev) => [...prev, ...f].slice(0, 5))}
                />
                {contentFiles.length > 0 && (
                  <div className="mt-2 space-y-1">
                    {contentFiles.map((f, i) => (
                      <div key={i} className="flex items-center justify-between bg-white rounded-lg px-2.5 py-1.5 border border-gray-100">
                        <span className="text-xs text-[#57423c] truncate">{f.name}</span>
                        <button
                          onClick={() => setContentFiles((prev) => prev.filter((_, j) => j !== i))}
                          className="text-[#57423c]/40 hover:text-red-500 ml-2"
                        >
                          <X size={12} />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              <p className="text-xs text-[#57423c]/40 mt-1.5">입력 + 파일을 함께 사용할 수 있어요</p>
            </div>
          </div>

          <button
            onClick={doMap}
            disabled={loading || !isAnalyzed || (!hasSmartInput && contentFiles.length === 0)}
            className="w-full bg-gradient-to-r from-[#2563EB] to-[#1E40AF] text-white py-3 rounded-xl font-semibold text-sm hover:opacity-90 disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-all active:scale-[0.98]"
          >
            {loading ? <Loader2 size={16} className="animate-spin" /> : <Wand2 size={16} />}
            {loading ? "채우는 중..." : "AI 자동 채우기"}
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="text-base text-[#57423c] space-y-1">
              <p className="font-semibold text-[#1a1c1b]">내 자료를 붙여넣거나 파일을 올리세요.</p>
              <p className="text-sm text-[#57423c]/60">양식에 맞춰 AI가 자동으로 채워드립니다. <span className="text-[#57423c]/40">Google AI 사용 · 학습에 미사용</span></p>
            </div>
            {docType && (
              <button
                onClick={() => setMode("smart")}
                className="text-xs text-[#57423c]/50 hover:text-[#2563EB] flex items-center gap-1 transition-colors shrink-0"
              >
                <Sparkles size={10} /> 추천 입력
              </button>
            )}
          </div>

          {/* 좌우 분리: 텍스트 입력 | 파일 업로드 */}
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
            {/* 왼쪽: 텍스트 입력 (3/5) */}
            <div className="lg:col-span-3">
              <textarea
                className="w-full border border-[#93C5FD]/40 rounded-xl p-3 text-sm resize-y focus:outline-none focus:border-[#1E40AF]/40 bg-white transition-colors"
                rows={5}
                placeholder={"여기에 내 자료를 붙여넣으세요.\n\n예: 회사명 주식회사 이지테크, 대표자 홍길동, 설립일 2024.01.15\n예: 엑셀이나 워드에서 복사해서 붙여넣기 해도 됩니다"}
                value={text}
                onChange={(e) => setText(e.target.value)}
              />
            </div>

            {/* 오른쪽: 파일 업로드 (2/5) */}
            <div className="lg:col-span-2">
              <div className="border-2 border-dashed border-[#93C5FD]/40 rounded-xl p-4 bg-[#FAFBFF] h-full flex flex-col">
                <FileUpload
                  accept=".txt,.xlsx,.xls,.docx,.csv,.json,.md"
                  label="엑셀, 워드, 텍스트 등"
                  multiple
                  onFiles={(f) => setContentFiles((prev) => [...prev, ...f].slice(0, 5))}
                />
                {contentFiles.length > 0 && (
                  <div className="mt-2 space-y-1">
                    {contentFiles.map((f, i) => (
                      <div key={i} className="flex items-center justify-between bg-white rounded-lg px-2.5 py-1.5 border border-gray-100">
                        <span className="text-xs text-[#57423c] truncate">{f.name}</span>
                        <button
                          onClick={() => setContentFiles((prev) => prev.filter((_, j) => j !== i))}
                          className="text-[#57423c]/40 hover:text-red-500 ml-2"
                        >
                          <X size={12} />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
                <p className="text-xs text-[#57423c]/40 mt-auto pt-2">텍스트 + 파일을 함께 사용 가능</p>
              </div>
            </div>
          </div>

          <button
            onClick={doMap}
            disabled={loading || !isAnalyzed || (!text && contentFiles.length === 0)}
            className="w-full bg-gradient-to-r from-[#2563EB] to-[#1E40AF] text-white py-3 rounded-xl font-semibold text-sm hover:opacity-90 disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-all active:scale-[0.98]"
          >
            {loading ? <Loader2 size={16} className="animate-spin" /> : <Wand2 size={16} />}
            {loading ? "채우는 중..." : "AI 자동 채우기"}
          </button>
        </div>
      )}

      {error && <div className="text-base text-red-600 bg-red-50 p-3 rounded-xl">{error}</div>}

      {mappings.length > 0 && (
        <div className="border border-[#93C5FD]/50 rounded-xl overflow-hidden">
          {/* AI 생성 모드 경고 */}
          {isGeneration && (
            <div className="bg-amber-50 border-b border-amber-200 px-4 py-3 text-base text-amber-800">
              <strong>AI 초안입니다.</strong> 이름, 날짜, 금액 등은 실제와 다를 수 있어요. 반드시 검토 후 사용하세요.
            </div>
          )}
          {/* 커버리지 정보 */}
          {coverage && (
            <div className="bg-[#f0fdf4] px-4 py-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle2 size={18} className="text-emerald-600" />
                <span className="text-base font-semibold text-[#1a1c1b]">{mappings.length}개 항목 매핑 완료</span>
              </div>
              <span className="text-sm text-[#57423c]">
                전체 {coverage.total_fields}개 필드 중 {coverage.mapped}개 매핑 ({coverage.coverage_pct}%)
              </span>
            </div>
          )}
          {!coverage && (
          <div className="bg-[#f0fdf4] px-4 py-3 flex items-center gap-2">
            <CheckCircle2 size={18} className="text-emerald-600" />
            <span className="text-base font-semibold text-[#1a1c1b]">{mappings.length}개 항목 매핑 완료</span>
          </div>
          )}

          <div className="p-3 space-y-2">
            <div className="flex items-center gap-4">
              <label className={`flex items-center gap-2 text-sm cursor-pointer select-none px-3 py-1.5 rounded-lg border transition-colors ${
                stripImages
                  ? "bg-red-50 border-red-200 text-red-700"
                  : "bg-[#f4f4f1] border-[#e2e3e0] text-[#57423c] hover:bg-[#e2e3e0]"
              }`}>
                <input
                  type="checkbox"
                  checked={stripImages}
                  onChange={(e) => setStripImages(e.target.checked)}
                  className="rounded accent-red-500 w-4 h-4"
                />
                <ImageOff size={16} />
                이미지 제거
                {stripImages && <span className="text-xs font-bold bg-red-100 px-1.5 py-0.5 rounded">ON</span>}
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

            {/* 매핑 저장/불러오기 */}
            <div className="flex gap-2">
              {user && (
                <button
                  onClick={() => doSaveMapping(false)}
                  disabled={saving || mappings.length === 0}
                  className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl text-xs font-semibold border border-[#93C5FD]/50 text-[#1E40AF] hover:bg-[#EFF6FF] disabled:opacity-40 transition-all"
                >
                  {saving ? <Loader2 size={12} className="animate-spin" /> : saveSuccess ? <CheckCircle2 size={12} className="text-emerald-600" /> : <Save size={12} />}
                  {saveSuccess ? "저장됨" : "매핑 저장"}
                </button>
              )}
              {user && (
                <button
                  onClick={doLoadMappings}
                  className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl text-xs font-semibold border border-[#93C5FD]/50 text-[#57423c] hover:bg-[#f4f4f1] transition-all"
                >
                  <FolderOpen size={12} /> 저장된 매핑
                </button>
              )}
            </div>

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

      {/* 매핑 불러오기 모달 */}
      {showLoadModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30" onClick={() => setShowLoadModal(false)}>
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md mx-4 max-h-[60vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
              <h3 className="font-bold text-[#1a1c1b]">저장된 매핑</h3>
              <button onClick={() => setShowLoadModal(false)} className="text-[#57423c]/50 hover:text-[#1a1c1b]"><X size={18} /></button>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-2">
              {savedList.length === 0 ? (
                <p className="text-base text-[#57423c]/60 text-center py-8">저장된 매핑이 없습니다.</p>
              ) : (
                savedList.map((m) => (
                  <div key={m.id} className="flex items-center justify-between p-3 rounded-xl border border-gray-100 hover:border-[#93C5FD]/50 transition-colors">
                    <button onClick={() => doApplyMapping(m.id)} className="flex-1 text-left">
                      <p className="text-base font-semibold text-[#1a1c1b] truncate">{m.form_name}</p>
                      <p className="text-xs text-[#57423c]/50">{m.form_field_count}개 필드 · {new Date(m.created_at).toLocaleDateString("ko-KR")}</p>
                    </button>
                    <button onClick={() => doDeleteMapping(m.id)} className="p-1.5 text-[#57423c]/30 hover:text-red-500 transition-colors"><Trash2 size={14} /></button>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
