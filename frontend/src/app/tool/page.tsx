"use client";

import { useState, useEffect, Suspense, useRef } from "react";
import { createPortal } from "react-dom";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { FormProvider, useForm } from "@/context/FormContext";
import { useAuth } from "@/context/AuthContext";
import { analyzeForm, shareFormToGallery, useGalleryForm } from "@/lib/api";
import FileUpload from "@/components/ui/FileUpload";
import AiMappingTab from "@/components/tabs/AiMappingTab";
import BatchTab from "@/components/tabs/BatchTab";
import ExtractTab from "@/components/tabs/ExtractTab";
import PeriodicTab from "@/components/tabs/PeriodicTab";
import StampTab from "@/components/tabs/StampTab";
import MergeTab from "@/components/tabs/MergeTab";
import ExcelTab from "@/components/tabs/ExcelTab";
import LoginModal from "@/components/ui/LoginModal";
import GaugeEmptyModal from "@/components/ui/GaugeEmptyModal";
import RewardToast, { type RewardItem } from "@/components/ui/RewardToast";
import OnboardingGuide from "@/components/ui/OnboardingGuide";
import CouponBadge from "@/components/ui/CouponBadge";
import {
  FileText, Loader2, Shield, Wand2, Layers, TableProperties,
  Calendar, Stamp, Merge, CheckCircle2, FileSpreadsheet,
  Sparkles, ChevronLeft, Upload, ChevronDown, ChevronUp, Settings2,
  User, Zap, LogOut, Flame, Globe, Gift
} from "lucide-react";

const MAIN_TABS = [
  { id: "ai", group: ["ai"], label: "AI 자동 채우기", icon: Wand2 },
  { id: "excel_doc", group: ["batch", "extract"], label: "문서 ⇄ 엑셀 쌍방향", icon: Layers },
  { id: "excel", group: ["excel"], label: "엑셀 빈칸 채우기", icon: FileSpreadsheet },
  { id: "special", group: ["periodic", "stamp", "merge"], label: "특수 기능 더보기", icon: Settings2 },
];

const SUB_TABS: Record<string, { id: string; label: string; icon: any }[]> = {
  excel_doc: [
    { id: "batch", label: "엑셀 → 문서 만들기", icon: Layers },
    { id: "extract", label: "문서 → 엑셀표 추출", icon: TableProperties },
  ],
  special: [
    { id: "periodic", label: "매월 반복 문서", icon: Calendar },
    { id: "stamp", label: "자동 도장 날인", icon: Stamp },
    { id: "merge", label: "다량 문서 합치기", icon: Merge },
  ]
};

const TAB_GUIDE: Record<string, { what: string; examples: string[] }> = {
  ai: {
    what: "내 자료를 올리거나 붙여넣으면, AI가 양식에 맞춰 넣어드립니다. 자료가 없으면 AI 초안도 가능해요.",
    examples: [
      "엑셀이나 워드 파일을 올리면 → 양식의 항목에 맞춰 자동으로 넣어줌",
      "텍스트를 복사 붙여넣기 → 양식 칸에 알아서 매핑해줌",
      "\"사업계획서 써줘\" → AI가 핵심 질문 기반으로 초안을 만들어줌 (검토 필요)",
    ],
  },
  batch: {
    what: "엑셀에 여러 사람 정보가 있으면, 같은 양식으로 사람 수만큼 문서를 만들어 줍니다.",
    examples: [
      "급여명세서 — 엑셀에 직원 100명 이름/급여 넣고, 양식 하나 올리면 → 100개 문서가 한번에 나옴",
      "수료증 — 엑셀에 수료자 이름/날짜 넣고, 수료증 양식 올리면 → 50장이 한번에 나옴",
      "계약서 — 엑셀에 업체명/금액 넣고, 계약서 양식 올리면 → 업체별 계약서 30개가 나옴",
    ],
  },
  extract: {
    what: "문서 안에 있는 글자를 전부 뽑아서 엑셀 파일로 만들어 줍니다.",
    examples: [
      "사업계획서 안의 모든 텍스트 → 엑셀로 정리해서 한눈에 보기",
      "양식 안에 어떤 빈칸들이 있는지 목록으로 확인하고 싶을 때",
      "여러 문서의 내용을 엑셀로 뽑아서 서로 비교할 때",
    ],
  },
  periodic: {
    what: "매달/매주 날짜만 바뀌는 같은 문서를, 한번에 여러 달치 만들어 줍니다.",
    examples: [
      "월간 보고서 — 1월~12월까지 날짜만 다른 보고서 12개를 한번에",
      "주간 업무일지 — 52주치 날짜가 자동으로 바뀐 일지를 한번에",
      "분기 보고서 — 1분기~4분기 보고서 4개를 한번에",
    ],
  },
  stamp: {
    what: "문서에 (인)이라고 써있는 곳에 실제 도장/서명 이미지를 넣어줍니다.",
    examples: [
      "공문서의 (인) 자리에 회사 직인 이미지를 자동으로 넣기",
      "계약서 하단 서명란에 내 서명 이미지 넣기",
      "문서 여러 개에 같은 도장을 한번에 찍기",
    ],
  },
  merge: {
    what: "여러 개의 문서 파일을 하나의 파일로 합쳐줍니다.",
    examples: [
      "각 부서에서 따로 받은 보고서 5개 → 하나의 파일로 합치기",
      "제안서를 파트별로 나눠 작성한 뒤 → 최종 하나로 합치기",
      "여러 장의 공문을 하나의 문서로 묶기",
    ],
  },
  excel: {
    what: "엑셀 파일의 특정 칸에 데이터를 자동으로 넣어줍니다.",
    examples: [
      "견적서 엑셀의 품목명, 수량, 금액 칸에 데이터 자동 입력",
      "출석부 엑셀의 이름/날짜 칸을 한번에 채우기",
      "정산서 엑셀의 매달 금액 칸을 자동으로 채우기",
    ],
  },
};

function GaugeBadge() {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (!user) return (
    <Link href="/pricing" className="flex items-center gap-1.5 text-xs text-[#57423c]/50 bg-[#f4f4f1] px-2.5 py-1 rounded-lg hover:bg-[#e2e3e0] transition-colors">
      <Zap size={10} /> 무료 사용 중 · <span className="text-[#2563EB] font-bold">업그레이드</span>
    </Link>
  );

  const plan = user.plan || "free";
  const gauge = user.gauge_pct || 0;
  const streak = user.streak_days || 0;
  const level = user.level || 1;
  const levelTitle = user.level_title || "복붙 탈출";

  // 게이지 바 색상: 100%+ 초록, 30%+ 파랑, 10%+ 노랑, 그 아래 빨강
  const barColor = gauge > 100 ? "bg-emerald-500" : gauge > 30 ? "bg-[#2563EB]" : gauge > 10 ? "bg-amber-500" : "bg-red-500";
  const barWidth = Math.min(gauge, 100);

  if (plan === "free") return (
    <Link href="/pricing" className="flex items-center gap-1.5 text-xs text-[#57423c]/50 bg-[#f4f4f1] px-2.5 py-1 rounded-lg hover:bg-[#e2e3e0] transition-colors">
      <Zap size={10} /> 무료 · <span className="text-[#2563EB] font-bold">업그레이드</span>
      {streak > 0 && <span className="text-[#57423c]/30">· {streak}일</span>}
    </Link>
  );

  return (
    <Link href="/mypage" className="flex items-center gap-2 text-xs bg-white border border-gray-200/80 px-3 py-1.5 rounded-lg hover:border-[#93C5FD] transition-colors">
      {/* 플랜 뱃지 */}
      {plan === "pro" ? (
        <span className="font-bold text-white bg-[#1E40AF] px-1.5 py-0.5 rounded text-xs">PRO</span>
      ) : (
        <span className="font-bold text-[#2563EB] bg-[#DBEAFE] px-1.5 py-0.5 rounded text-xs">PLUS</span>
      )}

      {/* 게이지 바 */}
      <div className="flex items-center gap-1.5">
        <span className="w-16 h-1.5 bg-gray-100 rounded-full overflow-hidden">
          <span className={`block h-full rounded-full transition-all duration-500 ${barColor}`} style={{ width: `${barWidth}%` }} />
        </span>
        <span className="font-bold text-[#1a1c1b] tabular-nums">{Math.round(gauge)}%</span>
      </div>

      {/* 스트릭 (3일 이상만 표시) */}
      {streak >= 3 && (
        <span className="text-orange-500 font-bold flex items-center gap-0.5">
          {streak}일
        </span>
      )}

      {/* 단계 (2 이상만 표시) */}
      {level >= 2 && (
        <span className="text-[#57423c]/30">{level}단계</span>
      )}
    </Link>
  );
}

function UserMenu({ onLoginClick }: { onLoginClick: () => void }) {
  const { user, accessToken, signOut, loading } = useAuth();
  const [open, setOpen] = useState(false);
  if (loading) return null;
  if (!user) return (
    <button onClick={onLoginClick} className="text-sm text-white bg-gradient-to-r from-[#2563EB] to-[#1E40AF] px-4 py-1.5 rounded-lg font-semibold hover:opacity-90 transition-all active:scale-95">
      로그인 / 가입
    </button>
  );

  return (
    <div className="relative">
      <button onClick={() => setOpen(!open)} className="flex items-center gap-1.5 text-sm text-[#57423c]/60 hover:text-[#1a1c1b] transition-colors">
        <User size={14} /> {user.email?.split("@")[0]}
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute right-0 top-8 bg-white border border-gray-200 rounded-xl shadow-lg p-2 min-w-[160px] z-50">
            <div className="px-3 py-2 border-b border-gray-100 mb-1">
              <p className="text-xs font-bold text-[#1a1c1b]">{user.level || 1}단계 {user.level_title || "복붙 탈출"}</p>
              <p className="text-xs text-[#57423c]/40">문서 {user.total_docs || 0}건 완성</p>
            </div>
            <Link href="/mypage" className="flex items-center gap-2 px-3 py-2 text-sm text-[#57423c] hover:bg-[#f4f4f1] rounded-lg" onClick={() => setOpen(false)}>
              <User size={12} /> 마이페이지
            </Link>
            <Link href="/pricing" className="block px-3 py-2 text-sm text-[#57423c] hover:bg-[#f4f4f1] rounded-lg" onClick={() => setOpen(false)}>
              요금제
            </Link>
            {user.email && ["ryugw10@gmail.com"].includes(user.email) && (
              <div className="border-t border-gray-100 mt-1 pt-1">
                <p className="px-3 py-1 text-[10px] text-[#57423c]/30 font-bold">OWNER</p>
                {(["free", "plus", "pro"] as const).map((p) => (
                  <button key={p} onClick={async () => {
                    const API = process.env.NEXT_PUBLIC_API_URL || "/api";
                    const token = accessToken || "";
                    await fetch(`${API}/admin/switch-plan`, {
                      method: "POST",
                      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
                      body: JSON.stringify({ plan: p }),
                    });
                    setOpen(false);
                    window.location.reload();
                  }} className="w-full text-left px-3 py-1.5 text-xs text-[#57423c] hover:bg-[#f4f4f1] rounded-lg">
                    {p.toUpperCase()}로 전환
                  </button>
                ))}
              </div>
            )}
            <button onClick={() => { signOut(); setOpen(false); }} className="w-full text-left px-3 py-2 text-sm text-red-500 hover:bg-red-50 rounded-lg flex items-center gap-2">
              <LogOut size={12} /> 로그아웃
            </button>
          </div>
        </>
      )}
    </div>
  );
}

const SHARE_CATEGORIES = ["사업계획서", "이력서", "견적서", "보고서", "계약서", "공문", "회의록", "수료증", "기타"];

function ShareFormButton({ file, filename, fieldCount }: { file: File | null; filename: string; fieldCount: number }) {
  const { user } = useAuth();
  const [showModal, setShowModal] = useState(false);
  const [title, setTitle] = useState("");
  const [category, setCategory] = useState("기타");
  const [sharing, setSharing] = useState(false);
  const [shared, setShared] = useState(false);

  useEffect(() => {
    if (filename) setTitle(filename.replace(/\.(hwpx?|docx)$/i, ""));
  }, [filename]);

  if (!user || !file || shared) {
    if (shared) return (
      <div className="flex items-center gap-1.5 text-xs text-emerald-600 bg-emerald-50 px-3 py-2 rounded-xl">
        <CheckCircle2 size={12} /> 갤러리에 공유됨
      </div>
    );
    return null;
  }

  const doShare = async () => {
    setSharing(true);
    try {
      await shareFormToGallery(file, title || filename, category);
      setShared(true);
      setShowModal(false);
    } catch { /* ignore */ }
    finally { setSharing(false); }
  };

  return (
    <>
      <button
        onClick={() => setShowModal(true)}
        className="w-full flex items-center justify-center gap-2 py-2 rounded-xl text-xs font-semibold border border-dashed border-[#93C5FD]/60 text-[#2563EB] hover:bg-[#EFF6FF] transition-all"
      >
        <Globe size={12} /> 빈 양식 갤러리에 올리기 <span className="text-xs bg-[#DBEAFE] px-1.5 py-0.5 rounded font-bold">+25%</span>
      </button>

      {showModal && createPortal(
        <div className="fixed inset-0 z-[100] bg-black/40 flex items-center justify-center p-4" onClick={() => setShowModal(false)}>
          <div className="bg-white rounded-2xl shadow-2xl p-6 max-w-sm w-full" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-base font-bold text-[#1a1c1b] mb-2">빈 양식을 갤러리에 올리기</h3>

            {/* 개인정보 안전 안내 */}
            <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-3 mb-4 space-y-1.5">
              <p className="text-xs font-bold text-emerald-700">공유되는 것 / 공유되지 않는 것</p>
              <div className="flex items-start gap-2 text-xs text-emerald-700">
                <span className="mt-0.5 font-bold shrink-0">공유 O</span>
                <span>업로드한 <strong>빈 양식 파일 자체</strong> (서식·구조만)</span>
              </div>
              <div className="flex items-start gap-2 text-xs text-red-600">
                <span className="mt-0.5 font-bold shrink-0">공유 X</span>
                <span>AI가 채운 내용, 내가 입력한 데이터, 이름·연락처 등 <strong>개인정보 일절 없음</strong></span>
              </div>
              <div className="flex items-start gap-2 text-xs text-red-600">
                <span className="mt-0.5 font-bold shrink-0">공유 X</span>
                <span>업로드한 사람의 이름이나 계정 정보</span>
              </div>
            </div>

            <div className="space-y-3 mb-4">
              <div>
                <label className="text-xs font-medium text-[#57423c] mb-1 block">양식 제목</label>
                <input
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full border border-[#93C5FD]/40 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#2563EB]/50"
                  placeholder="예: 초기창업패키지 사업계획서"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-[#57423c] mb-1 block">카테고리</label>
                <div className="flex flex-wrap gap-1.5">
                  {SHARE_CATEGORIES.map((c) => (
                    <button
                      key={c}
                      onClick={() => setCategory(c)}
                      className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-colors ${
                        category === c ? "bg-[#2563EB] text-white" : "bg-[#f4f4f1] text-[#57423c] hover:bg-[#e2e3e0]"
                      }`}
                    >{c}</button>
                  ))}
                </div>
              </div>
            </div>

            <p className="text-xs text-[#57423c]/40 mb-4">
              업로드한 콘텐츠의 저작권 책임은 사용자에게 있습니다.
            </p>

            <div className="flex gap-2">
              <button onClick={() => setShowModal(false)} className="flex-1 py-2.5 rounded-xl text-sm font-semibold bg-[#f4f4f1] text-[#57423c] hover:bg-[#e2e3e0]">
                취소
              </button>
              <button
                onClick={doShare}
                disabled={sharing || !title.trim()}
                className="flex-1 py-2.5 rounded-xl text-sm font-bold bg-gradient-to-r from-[#2563EB] to-[#1E40AF] text-white hover:opacity-90 disabled:opacity-50 flex items-center justify-center gap-1.5"
              >
                {sharing ? <Loader2 size={14} className="animate-spin" /> : <Gift size={14} />}
                {sharing ? "올리는 중..." : "올리기 (+25%)"}
              </button>
            </div>
          </div>
        </div>,
        document.body
      )}
    </>
  );
}

function Main() {
  const { isAnalyzed, filename, fieldCount, setForm } = useForm();
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [warning, setWarning] = useState("");
  const searchParams = useSearchParams();
  const [activeTab, setActiveTab] = useState("ai");
  const [showInfo, setShowInfo] = useState(false);
  const [showExamples, setShowExamples] = useState(false);
  const [showSteps, setShowSteps] = useState(true);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [gaugeEmptyData, setGaugeEmptyData] = useState<{ errorCode: string; plan: string; gaugePct: number } | null>(null);
  const [rewards, setRewards] = useState<RewardItem[]>([]);

  useEffect(() => {
    setShowExamples(false);
  }, [activeTab]);

  useEffect(() => {
    const tab = searchParams.get("tab");
    if (tab) {
      const isMain = MAIN_TABS.some((t) => t.id === tab);
      const isSub = Object.values(SUB_TABS).flat().some((t) => t.id === tab);
      if (isMain || isSub) {
        setActiveTab(tab);
      }
    }
  }, [searchParams]);

  // 갤러리에서 "바로 사용" 클릭 시 자동 분석
  useEffect(() => {
    const galleryId = searchParams.get("gallery_id");
    if (!galleryId || isAnalyzed) return;
    setLoading(true);
    setError("");
    useGalleryForm(Number(galleryId))
      .then((res) => {
        setForm({
          fileId: res.file_id,
          filename: res.filename,
          fields: res.fields,
          fieldCount: res.field_count,
          isAnalyzed: true,
          docType: res.doc_type || null,
          smartFields: res.smart_fields || [],
        });
      })
      .catch((e) => {
        setError(e instanceof Error ? e.message : "갤러리 양식 불러오기 실패");
      })
      .finally(() => setLoading(false));
  }, [searchParams]);

  const doAnalyze = async () => {
    if (!file) return;
    setLoading(true);
    setError("");
    try {
      const res = await analyzeForm(file);
      setForm({
        fileId: res.file_id,
        filename: res.filename,
        fields: res.fields,
        fieldCount: res.field_count,
        isAnalyzed: true,
        docType: res.doc_type || null,
        smartFields: res.smart_fields || [],
      });
      setWarning(res.warning || "");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "분석 실패");
    } finally {
      setLoading(false);
    }
  };

  const guide = TAB_GUIDE[activeTab] || TAB_GUIDE.ai;

  return (
    <div className="min-h-screen bg-[#f9f9f6]">
      {/* 헤더 — 랜딩과 톤 통일 */}
      <header className="sticky top-0 z-50 bg-[#f9f9f6]/80 backdrop-blur-xl border-b border-[#93C5FD]/50">
        <div className="max-w-screen-xl mx-auto px-6 lg:px-10 py-3.5 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/" className="flex items-center gap-1 text-[#57423c] hover:text-[#1E40AF] transition-colors">
              <ChevronLeft size={16} />
            </Link>
            <Link href="/" className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-[#1a1c1b] flex items-center justify-center">
                <FileText size={14} className="text-white" strokeWidth={2.2} />
              </div>
              <span className="text-lg font-extrabold tracking-tighter text-[#1a1c1b]">Eazy HWPX</span>
            </Link>
            <span className="hidden sm:block text-base text-[#57423c]">양식 + 내 자료를 올리면 AI가 넣어드립니다</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-2">
              <span className="text-xs font-bold text-[#1E40AF] bg-[#DBEAFE]/40 px-2.5 py-1 rounded-md">HWP</span>
              <span className="text-xs font-bold text-[#1E40AF] bg-[#DBEAFE]/40 px-2.5 py-1 rounded-md">HWPX</span>
              <span className="text-xs font-bold text-[#57423c]/70 bg-[#e2e3e0]/50 px-2.5 py-1 rounded-md">DOCX</span>
            </div>
            <div className="w-px h-5 bg-gray-200 hidden sm:block" />
            <CouponBadge />
            <GaugeBadge />
            <UserMenu onLoginClick={() => setShowLoginModal(true)} />
          </div>
        </div>
      </header>

      {/* 도구 영역 */}
      <div className="max-w-screen-xl mx-auto px-6 lg:px-10 py-6 flex flex-col lg:flex-row gap-10">

        {/* 왼쪽: 양식 넣기 */}
        <div className="w-full lg:w-[380px] shrink-0">
          <div className="lg:sticky lg:top-20">
            {/* 업로드 카드 */}
            <div className="bg-white rounded-2xl border border-[#93C5FD]/40 p-5 shadow-[0_4px_20px_rgba(26,28,27,0.03)]">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-7 h-7 rounded-lg bg-[#DBEAFE] flex items-center justify-center">
                  <Upload size={14} className="text-[#1E40AF]" />
                </div>
                <h2 className="font-bold text-sm text-[#1a1c1b]">양식 넣기</h2>
              </div>
              <p className="text-base text-[#57423c] mb-5">양식 문서를 올리고 분석하세요.</p>

              <div id="onboard-upload" className="min-h-[100px]">
                <FileUpload accept=".hwp,.hwpx,.docx" label="HWP / HWPX / DOCX 파일" onFiles={(f) => setFile(f[0])} />
              </div>

              <button
                id="onboard-analyze"
                onClick={doAnalyze}
                disabled={loading || !file}
                className="w-full mt-3 bg-gradient-to-r from-[#2563EB] to-[#1E40AF] text-white py-2.5 rounded-xl font-semibold text-sm hover:opacity-90 disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-all active:scale-[0.98]"
              >
                {loading ? <Loader2 size={14} className="animate-spin" /> : null}
                {loading ? "분석 중..." : "양식 분석"}
              </button>

              {error && <div className="text-base text-red-600 mt-2 bg-red-50 rounded-lg p-2">{error}</div>}
              {warning && <div className="text-base text-amber-700 mt-2 bg-amber-50 rounded-lg p-2">{warning}</div>}

              {isAnalyzed && (
                <div className="mt-3 space-y-2">
                  <div className="bg-[#f0fdf4] border border-emerald-200/50 rounded-xl px-3 py-2.5 flex items-start gap-2">
                    <CheckCircle2 size={15} className="text-emerald-600 mt-0.5 shrink-0" />
                    <div>
                      <div className="text-base font-bold text-[#1a1c1b]">{filename}</div>
                      <div className="text-base text-[#57423c]">{fieldCount}개 항목 발견</div>
                    </div>
                  </div>
                  <ShareFormButton file={file} filename={filename || ""} fieldCount={fieldCount || 0} />
                </div>
              )}
            </div>

            {/* 갤러리 링크 */}
            <div className="mt-4 pt-4 border-t border-[#93C5FD]/20">
              <Link href="/gallery" className="flex items-center justify-center gap-1.5 text-xs text-[#2563EB] hover:text-[#1E40AF] transition-colors">
                <Globe size={12} /> 양식 갤러리에서 양식 찾기
              </Link>
            </div>

          </div>
        </div>

        {/* 오른쪽 */}
        <div className="flex-1 min-w-0 space-y-4">

          {/* 탭 헤더 */}
          <div>
            {/* 메인 탭 */}
            <div id="onboard-tabs" className="flex bg-white border border-[#93C5FD]/50 rounded-2xl shadow-[0_4px_20px_rgba(26,28,27,0.03)] overflow-hidden p-1.5 gap-1">
              {MAIN_TABS.map((mainTab) => {
                const isActive = mainTab.group.includes(activeTab);
                const Icon = mainTab.icon;
                return (
                  <button
                    key={mainTab.id}
                    onClick={() => {
                      if (!isActive) setActiveTab(mainTab.group[0]);
                    }}
                    className={`flex-1 flex items-center justify-center gap-2 py-3.5 px-3 rounded-xl text-[14px] font-bold transition-all ${
                      isActive
                        ? "bg-gradient-to-r from-[#2563EB] to-[#1E40AF] text-white shadow-md"
                        : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                    }`}
                  >
                    <Icon size={18} />
                    <span>{mainTab.label}</span>
                  </button>
                );
              })}
            </div>

            {/* 서브 탭 (해당 메인 탭에 속할 때만 노출) */}
            {(() => {
              const activeMain = MAIN_TABS.find(m => m.group.includes(activeTab));
              if (activeMain && SUB_TABS[activeMain.id]) {
                return (
                  <div className="flex gap-2 mt-3 bg-white p-2 rounded-xl border border-gray-200">
                    {SUB_TABS[activeMain.id].map(sub => {
                      const isSubActive = sub.id === activeTab;
                      const SubIcon = sub.icon;
                      return (
                        <button
                          key={sub.id}
                          onClick={() => setActiveTab(sub.id)}
                          className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-[13px] font-bold transition-all ${
                            isSubActive
                              ? "bg-[#EFF6FF] text-[#1E40AF] shadow-sm border border-blue-200"
                              : "text-gray-500 hover:bg-gray-50 border border-transparent"
                          }`}
                        >
                          <SubIcon size={16} />
                          {sub.label}
                        </button>
                      );
                    })}
                  </div>
                );
              }
              return null;
            })()}
          </div>

          {/* 탭 콘텐츠 + 예시 + 보안 */}
          <div>

            {/* 탭 콘텐츠 */}
            <div className="bg-white border border-[#93C5FD]/40 rounded-2xl p-5 shadow-[0_4px_20px_rgba(26,28,27,0.03)]">
              {activeTab === "ai" && <AiMappingTab onGaugeEmpty={(data) => setGaugeEmptyData(data)} />}
              {activeTab === "batch" && <BatchTab />}
              {activeTab === "extract" && <ExtractTab />}
              {activeTab === "periodic" && <PeriodicTab />}
              {activeTab === "stamp" && <StampTab />}
              {activeTab === "merge" && <MergeTab />}
              {activeTab === "excel" && <ExcelTab />}
            </div>

            {/* 예시 */}
            <div className="pt-5 border-t border-[#93C5FD]/20">
              <p className="text-base text-[#57423c]/70 font-bold tracking-wider uppercase mb-3">이런 식으로 사용합니다</p>
              <div className="space-y-2.5">
                {guide.examples.map((ex, i) => (
                  <div key={`${activeTab}-${i}`} className="flex gap-3 items-start">
                    <span className="bg-gradient-to-br from-[#2563EB] to-[#1E40AF] text-white text-sm font-bold w-6 h-6 rounded-md flex items-center justify-center shrink-0 mt-0.5">{i + 1}</span>
                    <span className="text-[15px] text-[#57423c] leading-relaxed">{ex}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* 보안 — 하단 */}
            <div className="mt-5 pt-4 border-t border-[#93C5FD]/20">
              <button
                onClick={() => setShowInfo(!showInfo)}
                className="w-full py-2 flex items-center gap-2 hover:opacity-70 transition-opacity text-left"
              >
                <Shield size={15} className="text-[#1E40AF] shrink-0" />
                <span className="text-base font-semibold text-[#1a1c1b]">내 데이터는 어떻게 처리되나요?</span>
                {showInfo
                  ? <ChevronUp size={14} className="text-[#57423c] ml-auto" />
                  : <ChevronDown size={14} className="text-[#57423c] ml-auto" />
                }
              </button>
              {showInfo && (
                <div className="pt-3 pb-2 text-base text-[#57423c] leading-relaxed space-y-3">
                  <div>
                    <p className="font-semibold text-[#1a1c1b] mb-0.5">양식 분석 / 문서 생성 / 추출 / 병합</p>
                    <p>외부 서비스를 거치지 않고, 이 서버 안에서만 처리됩니다. 문서 내용이 외부로 전송되지 않습니다.</p>
                  </div>
                  <div>
                    <p className="font-semibold text-[#1a1c1b] mb-0.5">AI 자동 채우기</p>
                    <p>이 기능만 Google AI(Gemini)를 사용합니다. Google의 데이터 처리 정책에 따라 사용자 데이터는 AI 학습에 사용되지 않으며, 55일 후 완전 삭제됩니다.</p>
                  </div>
                  <div>
                    <p className="font-semibold text-[#1a1c1b] mb-0.5">파일 보관</p>
                    <p>업로드된 파일은 3시간 후 서버에서 자동 삭제됩니다. 서버가 종료되면 즉시 삭제됩니다. 별도의 백업이나 보관을 하지 않습니다.</p>
                  </div>
                  <div>
                    <p className="font-semibold text-[#1a1c1b] mb-0.5">통신 보안</p>
                    <p>모든 데이터는 HTTPS(TLS 1.3) 암호화 통신으로 전송됩니다.</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 푸터 */}
      <footer className="max-w-screen-xl mx-auto px-6 lg:px-10 py-4 flex items-center justify-center gap-4 text-base text-[#57423c]/50">
        <span>Eazy HWPX</span>
        <span>·</span>
        <Link href="/pricing" className="hover:text-[#1E40AF] transition-colors">요금제</Link>
        <span>·</span>
        <span>HTTPS 암호화 통신</span>
      </footer>

      {/* 로그인 모달 */}
      {showLoginModal && <LoginModal onClose={() => setShowLoginModal(false)} />}
      {/* 게이지 소진 모달 */}
      {gaugeEmptyData && (
        <GaugeEmptyModal
          errorCode={gaugeEmptyData.errorCode}
          plan={gaugeEmptyData.plan}
          gaugePct={gaugeEmptyData.gaugePct}
          onClose={() => setGaugeEmptyData(null)}
        />
      )}
      {/* 보상 토스트 */}
      {rewards.length > 0 && <RewardToast rewards={rewards} onDone={() => setRewards([])} />}
      {/* 첫 방문 가이드 */}
      <OnboardingGuide />
    </div>
  );
}

export default function ToolPage() {
  return (
    <Suspense>
      <FormProvider>
        <Main />
      </FormProvider>
    </Suspense>
  );
}
