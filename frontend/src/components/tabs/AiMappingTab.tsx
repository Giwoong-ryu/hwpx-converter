"use client";

import { useState, useEffect } from "react";
import { useForm } from "@/context/FormContext";
import { useAuth } from "@/context/AuthContext";
import { aiMap, generateDoc, downloadBlob, GaugeEmptyError, saveMapping, listMyMappings, loadMapping, deleteMapping, listPublicMappings, toggleLike, updateMappingPublic } from "@/lib/api";
import FileUpload from "@/components/ui/FileUpload";
import { Wand2, Download, Loader2, CheckCircle2, ChevronDown, ChevronUp, ImageOff, Sparkles, Save, FolderOpen, Trash2, X, AlertTriangle } from "lucide-react";

interface AiMappingTabProps {
  onGaugeEmpty?: (data: { errorCode: string; plan: string; gaugePct: number }) => void;
}

export default function AiMappingTab({ onGaugeEmpty }: AiMappingTabProps = {}) {
  const { fileId, isAnalyzed, filename, fieldCount, docType, smartFields } = useForm();
  const { user } = useAuth();
  const [text, setText] = useState("");
  const [textInitialized, setTextInitialized] = useState(false);
  const [contentFiles, setContentFiles] = useState<File[]>([]);
  const [remember, setRemember] = useState(false);

  // localStorage에서 기억된 값 불러오기
  useEffect(() => {
    try {
      const saved = localStorage.getItem("eazyhwpx_smart_remember");
      if (saved === "true") {
        setRemember(true);
        const savedText = localStorage.getItem("eazyhwpx_smart_text");
        if (savedText) { setText(savedText); setTextInitialized(true); }
      }
    } catch { /* localStorage 접근 불가 시 무시 */ }
  }, []);

  const [showTemplate, setShowTemplate] = useState(false);

  // 예시 양식 채우기 토글
  const handleTemplateToggle = (checked: boolean) => {
    setShowTemplate(checked);
    if (checked && smartFields.length > 0) {
      const template = smartFields.map((f) => `${f.label}: `).join("\n");
      setText(template);
    } else if (!checked) {
      setText("");
    }
  };

  // 기억하기 ON일 때 텍스트 변경 시 자동 저장
  useEffect(() => {
    if (!remember) return;
    try {
      localStorage.setItem("eazyhwpx_smart_text", text);
    } catch { /* 무시 */ }
  }, [text, remember]);

  const handleRememberToggle = (checked: boolean) => {
    setRemember(checked);
    try {
      if (checked) {
        localStorage.setItem("eazyhwpx_smart_remember", "true");
        localStorage.setItem("eazyhwpx_smart_text", text);
      } else {
        localStorage.removeItem("eazyhwpx_smart_remember");
        localStorage.removeItem("eazyhwpx_smart_text");
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
  const [coverage, setCoverage] = useState<{ total_fields: number; mapped: number; coverage_pct: number; ai_filled?: number } | null>(null);
  const [sources, setSources] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [showLoadModal, setShowLoadModal] = useState(false);
  const [loadTab, setLoadTab] = useState<"my" | "public">("my");
  const [savedList, setSavedList] = useState<{ id: number; form_name: string; form_field_count: number; created_at: string }[]>([]);
  const [publicList, setPublicList] = useState<{ id: number; form_name: string; form_field_count: number; likes: number; created_at: string; liked?: boolean }[]>([]);

  const doMap = async (useAi: boolean) => {
    if (!fileId) return;
    const prompt = text.trim();
    if (!prompt && contentFiles.length === 0) return;
    setLoading(true);
    setError("");
    try {
      const apiMode = useAi ? "ai" : "direct";
      const res = await aiMap(fileId, prompt, contentFiles.length > 0 ? contentFiles : undefined, apiMode);
      setMappings(Object.entries(res.mappings));
      setIsGeneration(res.is_generation || false);
      setCoverage(res.coverage || null);
      setSources(res.sources || {});
      // AI 보완 항목이 있으면 상세 보기 자동 펼침
      const aiCount = res.coverage?.ai_filled || 0;
      setShowDetail(aiCount > 0);
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

      {/* 통합 입력 UI */}
      <div className="space-y-3">
        <div>
          {docType && (
            <div className="flex items-center gap-2 mb-1">
              <Sparkles size={16} className="text-[#2563EB]" />
              <span className="text-sm font-bold text-[#1a1c1b]">
                이 양식은 <span className="text-[#2563EB]">{docType}</span>로 보입니다
              </span>
            </div>
          )}

          <p className="text-sm text-[#57423c]/60">
            내 자료를 입력하거나 파일을 올려주세요.
            <span className="text-[#57423c]/60 ml-1">항목명: 값 형식이면 AI 없이도 채울 수 있습니다.</span>
          </p>
        </div>

        {/* 좌우 분리: 텍스트 입력 | 파일 업로드 */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
          {/* 왼쪽: 통합 텍스트 입력 (3/5) */}
          <div className="lg:col-span-3">
            <textarea
              className="w-full border border-[#93C5FD]/40 rounded-xl p-3 text-sm resize-y focus:outline-none focus:border-[#1E40AF]/40 bg-white transition-colors"
              rows={7}
              placeholder={smartFields.length > 0
                ? `여기에 내 자료를 입력하거나 붙여넣으세요.\n\n예:\n${smartFields.map((f) => `${f.label}: ${f.placeholder || ""}`).join("\n")}`
                : "여기에 내 자료를 입력하거나 붙여넣으세요.\n\n예: 회사명, 대표자, 주소, 연락처 등\n엑셀이나 워드에서 복사해서 붙여넣기 해도 됩니다."}
              value={text}
              onChange={(e) => setText(e.target.value)}
            />
            <div className="flex items-center gap-4 mt-1.5 flex-wrap">
              {smartFields.length > 0 && (
                <label className="flex items-center gap-2 cursor-pointer select-none group">
                  <input
                    type="checkbox"
                    checked={showTemplate}
                    onChange={(e) => handleTemplateToggle(e.target.checked)}
                    className="rounded accent-[#2563EB] w-3.5 h-3.5"
                  />
                  <span className="text-xs text-[#2563EB] group-hover:text-[#1E40AF] transition-colors font-medium">
                    입력 양식 채워보기
                  </span>
                </label>
              )}
              <label className="flex items-center gap-2 cursor-pointer select-none group">
                <input
                  type="checkbox"
                  checked={remember}
                  onChange={(e) => handleRememberToggle(e.target.checked)}
                  className="rounded accent-[#2563EB] w-3.5 h-3.5"
                />
              <span className="text-xs text-[#57423c]/60 group-hover:text-[#57423c] transition-colors">
                이 기기에서 입력 내용 기억하기
              </span>
              {remember && (
                <span className="text-xs text-[#57423c]/60">서버에 전송되지 않습니다</span>
              )}
            </label>
            </div>
          </div>

          {/* 오른쪽: 파일 업로드 (2/5) */}
          <div className="lg:col-span-2">
            <div className="border-2 border-dashed border-[#93C5FD]/40 rounded-xl p-4 bg-[#FAFBFF] h-full flex flex-col">
              <FileUpload
                accept=".txt,.xlsx,.xls,.docx,.csv,.json,.md,.html,.htm"
                label="엑셀, 워드, 텍스트, HTML 등"
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
                        className="text-[#57423c]/60 hover:text-red-500 ml-2"
                      >
                        <X size={12} />
                      </button>
                    </div>
                  ))}
                </div>
              )}
              <p className="text-xs text-[#57423c]/60 mt-auto pt-2">텍스트 + 파일을 함께 사용 가능</p>
            </div>
          </div>
        </div>

        <button
          onClick={() => doMap(true)}
          disabled={loading || !isAnalyzed || (!text.trim() && contentFiles.length === 0)}
          className="w-full bg-linear-to-r from-[#2563EB] to-[#1E40AF] text-white py-3 rounded-xl font-semibold text-sm hover:opacity-90 disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-all active:scale-[0.98]"
        >
          {loading ? <Loader2 size={16} className="animate-spin" /> : <Wand2 size={16} />}
          {loading ? "채우는 중..." : "AI로 채우기"}
        </button>
      </div>

      {error && <div className="text-base text-red-600 bg-red-50 p-3 rounded-xl">{error}</div>}

      {/* AI 초안 작성 경고 배너 */}
      {isGeneration && mappings.length > 0 && (
        <div className="flex items-start gap-2.5 bg-amber-50 border border-amber-200 rounded-xl px-4 py-3">
          <AlertTriangle size={15} className="text-amber-500 shrink-0 mt-0.5" />
          <div>
            <span className="text-sm font-bold text-amber-800">AI 초안 작성 결과입니다.</span>
            <span className="text-sm text-amber-700/80 ml-1">중요 문서는 반드시 내용을 검토한 후 사용하세요.</span>
          </div>
        </div>
      )}

      {mappings.length > 0 && (
        <div className="border border-[#93C5FD]/50 rounded-xl overflow-hidden">
          {/* 커버리지 + AI 보완 안내 */}
          {coverage ? (
            <div className="bg-[#f0fdf4] px-4 py-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle2 size={18} className="text-emerald-600" />
                  <span className="text-base font-semibold text-[#1a1c1b]">{mappings.length}개 항목 자동 채움 완료</span>
                </div>
                <span className="text-sm text-[#57423c]">
                  {coverage.total_fields}개 필드 중 {coverage.mapped}개 ({coverage.coverage_pct}%)
                </span>
              </div>
              {(coverage.ai_filled || 0) > 0 && (
                <p className="text-sm text-[#2563EB] mt-1.5">
                  {coverage.ai_filled}개 항목은 AI가 보완했어요. <span className="text-[#57423c]/50">아래에서 파란 배경 항목을 확인해보세요.</span>
                </p>
              )}
            </div>
          ) : (
            <div className="bg-[#f0fdf4] px-4 py-3 flex items-center gap-2">
              <CheckCircle2 size={18} className="text-emerald-600" />
              <span className="text-base font-semibold text-[#1a1c1b]">{mappings.length}개 항목 자동 채움 완료</span>
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
                  <th className="text-left px-4 py-2 text-[#1a1c1b] font-medium text-xs">채움 내용</th>
                  <th className="text-left px-4 py-2 text-[#1a1c1b] font-medium text-xs w-16">출처</th>
                </tr>
              </thead>
              <tbody>
                {mappings.map(([old, val], i) => {
                  const isAi = sources[old] === "ai";
                  return (
                  <tr key={i} className={`border-b border-[#93C5FD]/40 ${isAi ? "bg-blue-50/60" : "hover:bg-[#f4f4f1]/50"}`}>
                    <td className="px-4 py-2 text-[#57423c] text-xs">{old.length > 40 ? old.slice(0, 40) + "..." : old}</td>
                    <td className="px-4 py-1">
                      <input
                        className={`w-full border rounded-lg px-2 py-1 text-xs focus:outline-none focus:border-[#1E40AF]/40 ${isAi ? "border-blue-200 bg-blue-50/30" : "border-[#93C5FD]/40 bg-white"}`}
                        value={val}
                        onChange={(e) => {
                          const copy = [...mappings];
                          copy[i] = [old, e.target.value];
                          setMappings(copy);
                        }}
                      />
                    </td>
                    <td className="px-4 py-2 text-xs">
                      {isAi ? (
                        <span className="text-[#2563EB] font-medium">AI</span>
                      ) : (
                        <span className="text-[#57423c]/60">내 자료</span>
                      )}
                    </td>
                  </tr>
                );
              })}
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
                    <button onClick={() => doDeleteMapping(m.id)} className="p-1.5 text-[#57423c]/50 hover:text-red-500 transition-colors"><Trash2 size={14} /></button>
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
