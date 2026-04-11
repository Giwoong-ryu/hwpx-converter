"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  Wand2, Layers, TableProperties, Calendar,
  Stamp, Merge, FileSpreadsheet, ArrowRight,
  FileText, Shield, ChevronRight,
  Lock, Server, Trash2, Clock, CheckCircle2, ChevronDown,
  UploadCloud, RefreshCw
} from "lucide-react";
import CouponBadge from "@/components/ui/CouponBadge";

/* ═══ 데이터 ═══ */

const FEATURES = [
  { icon: Wand2, label: "AI 자동 채우기", benefit: "내 자료를 양식에 맞춰 넣어드립니다", tab: "ai", highlight: true },
  { icon: Layers, label: "엑셀 → 문서", benefit: "100행이면 문서 100개", tab: "batch" },
  { icon: TableProperties, label: "문서 → 엑셀", benefit: "글자를 엑셀로 추출", tab: "extract" },
  { icon: Calendar, label: "정기문서", benefit: "12개월치 한번에", tab: "periodic" },
  { icon: Stamp, label: "도장", benefit: "(인) 자리에 자동", tab: "stamp" },
  { icon: Merge, label: "합치기", benefit: "여러 파일을 하나로", tab: "merge" },
  { icon: FileSpreadsheet, label: "엑셀 채우기", benefit: "빈칸 자동 채움", tab: "excel" },
];

/* ═══ 스크롤 애니메이션 ═══ */

function useScrollReveal() {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const targets = el.querySelectorAll(".scroll-fade");
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const delay = Number(entry.target.getAttribute("data-delay") || 0);
            setTimeout(() => entry.target.classList.add("visible"), delay);
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.06 }
    );
    targets.forEach((t) => observer.observe(t));
    return () => observer.disconnect();
  }, []);
  return ref;
}

/* ═══ 인기 양식 (랜딩용) ═══ */

function PopularForms() {
  const [forms, setForms] = useState<{ id: number; title: string; category: string; likes: number; downloads: number; field_count: number }[]>([]);

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL || "/api"}/gallery/list?sort=popular&size=6`)
      .then((r) => r.json())
      .then((d) => setForms(d.forms || []))
      .catch(() => { });
  }, []);

  const COLORS: Record<string, string> = {
    "사업계획서": "bg-blue-100 text-blue-700",
    "이력서": "bg-emerald-100 text-emerald-700",
    "견적서": "bg-amber-100 text-amber-700",
    "보고서": "bg-purple-100 text-purple-700",
    "계약서": "bg-red-100 text-red-700",
    "공문": "bg-gray-100 text-gray-700",
  };

  if (forms.length === 0) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {["사업계획서", "이력서", "견적서", "보고서", "계약서", "공문"].map((name) => (
          <div key={name} className="bg-[#f9f9f6] rounded-2xl border border-dashed border-[#93C5FD]/40 p-5 text-center">
            <span className={`text-xs font-bold px-2 py-0.5 rounded-md ${COLORS[name] || "bg-gray-100 text-gray-600"}`}>{name}</span>
            <p className="text-sm text-[#57423c]/60 mt-3">아직 공유된 양식이 없습니다</p>
            <Link href="/tool" className="text-xs text-[#2563EB] mt-1 inline-block">첫 번째 양식 공유하기</Link>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {forms.map((f, i) => (
        <div key={f.id} className="scroll-fade bg-[#f9f9f6] rounded-2xl border border-[#93C5FD]/30 p-5 hover:border-[#2563EB]/40 hover:shadow-md transition-all group" data-delay={i * 80}>
          <span className={`text-xs font-bold px-2 py-0.5 rounded-md ${COLORS[f.category] || "bg-gray-100 text-gray-600"}`}>{f.category}</span>
          <h3 className="text-sm font-bold text-[#1a1c1b] mt-2 mb-1 line-clamp-1 group-hover:text-[#2563EB] transition-colors">{f.title}</h3>
          <p className="text-sm text-[#57423c]/65 mb-3">{f.field_count}개 필드</p>
          <div className="flex items-center justify-between">
            <span className="text-sm text-[#57423c]/60">{f.likes} 좋아요 · {f.downloads}명 사용</span>
            <Link
              href={`/tool?gallery_id=${f.id}`}
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-linear-to-r from-[#2563EB] to-[#1E40AF] text-white text-xs font-bold hover:opacity-90 transition-opacity"
            >
              바로 사용
            </Link>
          </div>
        </div>
      ))}
    </div>
  );
}

/* ═══ FAQ 데이터 ═══ */

const FAQS = [
  {
    q: "한글 프로그램(한컴오피스)이 없어도 되나요?",
    a: "네, 없어도 됩니다. Eazy HWPX는 서버에서 HWP·HWPX 파일을 직접 처리하므로, 사용자 PC에 한글 프로그램이 설치되어 있지 않아도 됩니다.",
  },
  {
    q: "내 자료가 서버에 저장되나요?",
    a: "양식 파일과 내 자료는 처리 후 3시간 이내에 자동 삭제됩니다. AI 채우기에 사용되는 데이터는 Google AI로 전송되지만 학습에는 사용되지 않습니다.",
  },
  {
    q: "어떤 파일 형식을 지원하나요?",
    a: "양식: HWP, HWPX, DOCX. 내 자료: 엑셀(.xlsx, .xls), 워드(.docx), 텍스트, CSV, JSON, HTML 등 대부분의 문서 형식을 지원합니다.",
  },
  {
    q: "무료로 사용할 수 있나요?",
    a: "HWP·HWPX·DOCX 변환, 합치기, 도장, 추출 기능은 완전 무료입니다. AI 자동 채우기는 하루 10회 무료 제공되며, 매일 자정에 자동 충전됩니다.",
  },
  {
    q: "AI 초안 작성은 얼마나 정확한가요?",
    a: "자료가 없을 때 \"사업계획서 써줘\" 같이 요청하면 AI가 핵심 질문 기반으로 초안을 만들어드립니다. 참고용으로 활용하고, 중요 문서는 반드시 본인이 검토하세요.",
  },
];

/* ═══ 페이지 ═══ */

export default function LandingPage() {
  const scrollRef = useScrollReveal();
  const [showMoreFeatures, setShowMoreFeatures] = useState(false);
  const [openFaq, setOpenFaq] = useState<number | null>(null);
  const [isAiScanning, setIsAiScanning] = useState(false);
  const [isAiDone, setIsAiDone] = useState(false);

  const startScan = () => {
    if (isAiScanning) return;
    setIsAiScanning(true);
    setTimeout(() => setIsAiDone(true), 2500);
  };

  return (
    <div ref={scrollRef} className="min-h-screen bg-[#f9f9f6] text-[#1a1c1b] overflow-hidden">

      {/* ── 네비게이션 ── */}
      <nav className="fixed top-0 w-full z-50 bg-[#f9f9f6]/80 backdrop-blur-xl border-b border-[#BFDBFE]/40">
        <div className="flex justify-between items-center px-4 sm:px-8 lg:px-12 py-4 max-w-screen-2xl mx-auto">
          <Link href="/" className="flex items-center gap-2.5 shrink-0">
            <div className="w-7 h-7 rounded-lg bg-[#1a1c1b] flex items-center justify-center">
              <FileText size={14} className="text-white" strokeWidth={2.2} />
            </div>
            <span className="text-lg font-extrabold tracking-tighter whitespace-nowrap">Eazy HWPX</span>
          </Link>
          <div className="flex items-center gap-2 sm:gap-4 shrink-0">
            <CouponBadge />
            <Link href="/pricing" className="text-sm text-[#57423c]/70 hover:text-[#1a1c1b] transition-colors whitespace-nowrap">
              요금제
            </Link>
            <Link
              href="/tool"
              className="bg-linear-to-r from-[#2563EB] to-[#1E40AF] text-white px-3 sm:px-5 py-2 rounded-lg font-semibold text-sm hover:opacity-90 transition-all active:scale-95 whitespace-nowrap"
            >
              <span className="hidden sm:inline">무료로 시작하기</span>
              <span className="sm:hidden">시작하기</span>
            </Link>
          </div>
        </div>
      </nav>

      {/* ══════════════════════════════════════════
          섹션 1: 히어로 — 좌우 스플릿
          왼쪽: 핵심 가치 (매핑) + CTA
          오른쪽: AI 매핑 플로우 시각화
      ══════════════════════════════════════════ */}
      <section className="relative pt-28 pb-16 lg:pb-12 lg:min-h-[90vh] flex items-center">
        <div className="absolute inset-0 warm-hero-bg" />
        <div className="relative w-full max-w-screen-2xl mx-auto px-8 lg:px-16 grid grid-cols-1 lg:grid-cols-12 gap-16 items-center">

          {/* 왼쪽: 카피 */}
          <div className="lg:col-span-6">
            {/* HWP/HWPX 호환 배지 */}
            <div className="hero-stagger hero-s1 mb-8">
              <div className="flex items-center gap-4 flex-wrap">
                <div className="flex items-baseline gap-2">
                  <span className="text-[3rem] lg:text-[4rem] font-black text-[#1E40AF] leading-none tracking-tighter">HWP</span>
                  <span className="text-[2rem] text-[#BFDBFE] font-light">/</span>
                  <span className="text-[3rem] lg:text-[4rem] font-black text-[#1E40AF] leading-none tracking-tighter">HWPX</span>
                </div>
                <div className="flex flex-col gap-0.5">
                  <span className="text-sm font-bold text-[#1a1c1b]">+ DOCX 완벽 지원</span>
                  <span className="text-sm text-[#57423c]/60">표, 수식, 개조식까지 깨짐 없이</span>
                </div>
              </div>
            </div>

            <h1 className="hero-stagger hero-s2 text-[2.4rem] lg:text-[3rem] font-extrabold leading-[1.15] tracking-tight mb-5">
              또 양식에 하나하나<br />
              <span className="text-[#1E40AF]">복사 붙여넣기</span> 하실 건가요?
            </h1>

            <p className="hero-stagger hero-s3 text-lg text-[#57423c] leading-relaxed max-w-lg mb-8">
              내 자료만 올리면 <strong className="text-[#1a1c1b]">양식에 맞춰 AI가 넣어드립니다.</strong><br />
              엑셀, 워드, 텍스트 — 어떤 자료든.
            </p>

            <div className="hero-stagger hero-s4 flex flex-wrap items-center gap-4 mb-3">
              <Link
                href="/tool"
                className="cta-warm bg-linear-to-r from-[#2563EB] to-[#1E40AF] text-white px-8 py-3.5 rounded-xl text-base font-bold shadow-lg shadow-[#1E40AF]/20 hover:shadow-xl transition-all active:scale-95 flex items-center gap-2"
              >
                무료로 시작하기 <ArrowRight size={17} />
              </Link>
              <span className="text-sm text-[#57423c]/65">회원가입 없이 바로 사용</span>
            </div>
            <div className="hero-stagger hero-s4 mb-6">
              <Link
                href="/gallery"
                className="inline-flex items-center gap-1.5 text-sm text-[#2563EB] hover:text-[#1E40AF] transition-colors"
              >
                <FileText size={14} />
                양식이 없다면? 사업계획서, 이력서, 견적서 등 공공 양식 바로 사용
                <ArrowRight size={13} />
              </Link>
            </div>

            {/* 핵심 수치 */}
            <div className="hero-stagger hero-s4 flex items-center gap-6 text-base text-[#57423c]/60">
              <span><strong className="text-[#1a1c1b]">7가지</strong> 자동화 도구</span>
              <span className="text-[#BFDBFE]">|</span>
              <span>평균 <strong className="text-[#1a1c1b]">3분</strong> 완성</span>
              <span className="text-[#BFDBFE]">|</span>
              <span><strong className="text-[#1a1c1b]">무료</strong> 사용</span>
            </div>
          </div>

          {/* 오른쪽: 버블 프레임 + Before/After 스캔 애니메이션 */}
          <div className="lg:col-span-6 relative hidden lg:flex items-center justify-center h-[460px] scale-[0.85] origin-center translate-x-44">

            {/* ── 입체 버블들 (배경) ── */}
            <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
              <div className="absolute top-[15%] right-[-10%] w-[360px] h-[360px] rounded-full bg-white shadow-[inset_-25px_-25px_40px_rgba(0,0,0,0.03),_0_20px_40px_rgba(0,0,0,0.06)] border border-[#F9FAFB]" />
              <div className="absolute top-[5%] left-[5%] w-[260px] h-[260px] rounded-full bg-white shadow-[inset_-20px_-20px_35px_rgba(0,0,0,0.02),_10px_15px_30px_rgba(0,0,0,0.05)] border border-[#F9FAFB]" />
              <div className="absolute top-[-5%] left-[25%] w-[200px] h-[200px] rounded-full bg-white shadow-[inset_-15px_-15px_30px_rgba(0,0,0,0.02),_5px_10px_20px_rgba(0,0,0,0.03)] border border-[#F9FAFB]" />
              <div className="absolute top-[0%] right-[10%] w-[120px] h-[120px] rounded-full bg-white shadow-[inset_-10px_-10px_20px_rgba(0,0,0,0.02),_5px_5px_15px_rgba(0,0,0,0.04)]" />
              <div className="absolute bottom-[-10%] left-[15%] w-[220px] h-[220px] rounded-full bg-[#FAFAFA] shadow-[inset_-15px_-15px_30px_rgba(0,0,0,0.02),_10px_10px_25px_rgba(37,99,235,0.06)] border border-[#F3F4F6]" />
              <div className="absolute top-[40%] right-[2%] w-[80px] h-[80px] rounded-full bg-blue-50 shadow-[inset_-8px_-8px_15px_rgba(37,99,235,0.1),_0_5px_10px_rgba(0,0,0,0.03)] border border-blue-100" />
              <div className="absolute top-[60%] left-[-2%] w-[90px] h-[90px] rounded-full bg-blue-100 shadow-[inset_-10px_-10px_20px_rgba(37,99,235,0.15),_0_5px_15px_rgba(37,99,235,0.1)] opacity-80 border border-blue-200" />
            </div>

            {/* ── 3D 투시 래퍼 ── */}
            <div style={{ perspective: '1600px' }} className="z-10 ml-16 relative flex items-center">

              {/* ── 1. 양식 파일 카드 (Top Left) ── */}
              <div className="absolute top-[10%] left-[-360px] z-30 w-[220px] hidden xl:flex flex-col items-center">
                <div className="w-full bg-white rounded-2xl shadow-[0_20px_40px_rgba(0,0,0,0.08),_0_0_0_1px_rgba(0,0,0,0.02)] p-4 transform -rotate-6 transition-transform duration-500 hover:rotate-0 relative">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-6 h-6 rounded-md bg-[#EEF2FF] flex items-center justify-center text-blue-600">
                      <UploadCloud size={14} />
                    </div>
                    <span className="font-bold text-[16px] text-gray-800 tracking-tight">양식 파일</span>
                  </div>
                  <p className="text-[12px] text-gray-500 mb-3 leading-tight">HWP, HWPX, DOCX 양식을 올리세요.</p>
                  <div className="relative border-[2px] border-dashed border-[#BFDBFE] rounded-xl py-4 px-4 flex flex-col items-center justify-center bg-[#EFF6FF]/50 mb-3">
                    <div className="absolute -top-2 z-20 w-16 h-20 bg-white rounded-lg flex flex-col items-center justify-center border border-[#00A1E9]/40 shadow-lg transform rotate-3 animate-[bounce_3s_infinite]">
                      <div className="absolute top-0 right-0 w-4 h-4 bg-[#00A1E9]/10 border-b border-l border-[#00A1E9]/30 rounded-bl-sm z-10" />
                      <div className="w-8 h-8 bg-[#00A1E9] rounded flex items-center justify-center text-white font-black text-[14px] shadow-sm mb-1 z-0 relative">H</div>
                      <span className="text-[8px] font-black text-[#00A1E9] tracking-tighter">.hwpx</span>
                    </div>
                    <div className="mt-8 w-8 h-8 rounded-full bg-white shadow-sm flex items-center justify-center">
                      <UploadCloud size={16} className="text-[#3B82F6]" />
                    </div>
                  </div>
                  <div className="w-full bg-[#7C88C3] text-white text-center py-2 rounded-lg text-[12px] font-bold shadow-sm">양식 분석</div>
                </div>
              </div>

              {/* ── 2. 내 자료 카드 (Bottom Left) ── */}
              <div className="absolute bottom-[8%] left-[-320px] z-30 w-[220px] hidden xl:flex flex-col items-center">
                <div className="w-full bg-white rounded-2xl shadow-[0_15px_35px_rgba(0,0,0,0.07),_0_0_0_1px_rgba(0,0,0,0.02)] p-4 transform rotate-4 transition-transform duration-500 hover:rotate-0 relative">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-6 h-6 rounded-md bg-emerald-50 flex items-center justify-center text-emerald-600">
                      <FileSpreadsheet size={14} />
                    </div>
                    <span className="font-bold text-[16px] text-gray-800 tracking-tight">내 자료</span>
                  </div>
                  <p className="text-[12px] text-gray-500 mb-3 leading-tight">엑셀, 워드, 텍스트 또는 직접 입력</p>
                  <div className="relative border-[2px] border-dashed border-emerald-200 rounded-xl py-3 px-4 flex flex-col items-center justify-center bg-emerald-50/50 mb-3">
                    <div className="absolute -top-2 flex -space-x-1 z-20 transform animate-[bounce_3.5s_infinite]">
                      <div className="relative w-12 h-14 bg-white rounded-lg flex flex-col items-center justify-center border border-[#107C41]/30 shadow-md transform -rotate-12 z-30">
                        <div className="w-6 h-6 bg-[#107C41] rounded-[3px] flex items-center justify-center text-white font-black text-[11px] shadow-sm mb-0.5">X</div>
                      </div>
                      <div className="relative w-12 h-14 bg-white rounded-lg flex flex-col items-center justify-center border border-[#2B579A]/30 shadow-md z-20 -translate-y-1">
                        <div className="w-6 h-6 bg-[#2B579A] rounded-[3px] flex items-center justify-center text-white font-black text-[11px] shadow-sm mb-0.5">W</div>
                      </div>
                      <div className="relative w-12 h-14 bg-white rounded-lg flex flex-col items-center justify-center border border-[#00A1E9]/30 shadow-md transform rotate-12 z-10">
                        <div className="w-6 h-6 bg-[#00A1E9] rounded-[3px] flex items-center justify-center text-white font-black text-[11px] shadow-sm mb-0.5">H</div>
                      </div>
                    </div>
                    <div className="mt-6 w-8 h-8 rounded-full bg-white shadow-sm flex items-center justify-center">
                      <UploadCloud size={16} className="text-emerald-500" />
                    </div>
                  </div>
                  <div className="w-full bg-emerald-50 text-emerald-600 border border-emerald-200 text-center py-2 rounded-lg text-[12px] font-bold shadow-sm">직접 입력</div>
                </div>
              </div>

              {/* ── 화살표 ── */}
              <div className="absolute top-1/2 left-[-60px] -translate-y-1/2 z-40">
                <div className="bg-white p-3 rounded-full shadow-xl border border-gray-200">
                  <ArrowRight size={22} className="text-[#2563EB]" />
                </div>
              </div>

              {/* ── 메인 3D 문서 카드 ── */}
              <div className="relative w-[520px] bg-white shadow-[-20px_30px_60px_rgba(0,0,0,0.18),_-5px_10px_30px_rgba(0,0,0,0.10),_0_0_0_1px_rgba(0,0,0,0.04)] overflow-hidden font-sans"
                style={{ transform: 'rotateX(12deg) rotateY(-22deg) rotateZ(2deg) scale(1.0)', transformStyle: 'preserve-3d' }}>

                {/* 클릭 유도 오버레이 */}
                {!isAiScanning && !isAiDone && (
                  <div className="absolute inset-0 z-30 flex items-center justify-center bg-white/5">
                    <div className="relative group cursor-pointer" onClick={startScan}>
                      <div className="absolute -top-7 left-1/2 -translate-x-1/2 flex flex-col items-center gap-0.5 pointer-events-none text-gray-800 font-extrabold text-[12px] animate-bounce">
                        <span>클릭</span>
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="M12 5v14" /><path d="m19 12-7 7-7-7" /></svg>
                      </div>
                      <button className="bg-blue-600 group-hover:bg-blue-700 text-white px-8 py-4 rounded-full font-bold shadow-2xl flex items-center gap-3 transform transition-all group-hover:scale-105 active:scale-95 text-[15px] pointer-events-none">
                        <Wand2 size={24} />
                        AI로 양식 자동 완성하기
                      </button>
                      <div className="absolute -bottom-6 -right-6 text-gray-800 transform rotate-[-15deg] group-hover:-translate-x-2 group-hover:-translate-y-2 transition-transform duration-300 drop-shadow-xl pointer-events-none hidden sm:block">
                        <svg width="32" height="32" viewBox="0 0 24 24" fill="white" stroke="#1f2937" strokeWidth="1.5"><path d="M4 2v20l6-6h10z" /></svg>
                      </div>
                    </div>
                  </div>
                )}

                {/* BEFORE: 빈 양식 */}
                <div className="bg-white p-5 relative w-full h-[520px] flex flex-col gap-2">
                  <div className="border-[1.5px] border-gray-500 bg-[#E5E7EB] py-2.5 text-center">
                    <h2 className="text-[18px] font-extrabold text-black tracking-tighter">사업계획서</h2>
                  </div>
                  <div className="flex items-center gap-2 mt-3">
                    <div className="w-3 h-3 border border-gray-400 bg-white" />
                    <span className="font-bold text-[13px] text-black tracking-tight">일반현황</span>
                  </div>
                  <table className="w-full border-collapse border-[1.5px] border-gray-400 text-[10px] text-center tracking-tight">
                    <tbody>
                      <tr>
                        <th className="border-[1.5px] border-gray-400 bg-[#F3F4F6] w-[20%] py-1.5 font-bold text-black">기업명</th>
                        <td className="border-[1.5px] border-gray-400 w-[30%] py-1.5 text-blue-500 italic px-1">O O O O</td>
                        <th className="border-[1.5px] border-gray-400 bg-[#F3F4F6] w-[20%] py-1.5 font-bold text-black">개업연월일</th>
                        <td className="border-[1.5px] border-gray-400 w-[30%] py-1.5 text-blue-500 italic px-1">00. 00. 00</td>
                      </tr>
                      <tr>
                        <th className="border-[1.5px] border-gray-400 bg-[#F3F4F6] py-1.5 font-bold text-black">사업자 구분</th>
                        <td className="border-[1.5px] border-gray-400 py-1.5 text-blue-500 italic">개인 / 법인</td>
                        <th className="border-[1.5px] border-gray-400 bg-[#F3F4F6] py-1.5 font-bold text-black">대표자 유형</th>
                        <td className="border-[1.5px] border-gray-400 py-1.5 text-blue-500 italic">단독 / 공동</td>
                      </tr>
                      <tr>
                        <th className="border-[1.5px] border-gray-400 bg-[#F3F4F6] py-1.5 font-bold text-black">사업자등록번호</th>
                        <td className="border-[1.5px] border-gray-400 py-1.5 text-blue-500 italic">000-00-00000</td>
                        <th className="border-[1.5px] border-gray-400 bg-[#F3F4F6] py-1.5 font-bold text-black">소재지</th>
                        <td className="border-[1.5px] border-gray-400 py-1.5 text-blue-500 italic">OO도 OO시</td>
                      </tr>
                    </tbody>
                  </table>
                  <table className="w-full border-collapse border-[1.5px] border-gray-400 text-[10px] text-center tracking-tight mt-2">
                    <tbody>
                      <tr>
                        <th className="border-[1.5px] border-gray-400 bg-[#F3F4F6] w-[20%] py-1.5 font-bold text-black">창업아이템명</th>
                        <td className="border-[1.5px] border-gray-400 w-[80%] py-1.5 text-blue-500 italic" colSpan={3}>OO기술 적용 제품/서비스</td>
                      </tr>
                      <tr>
                        <th className="border-[1.5px] border-gray-400 bg-[#F3F4F6] py-1.5 font-bold text-black">산출물</th>
                        <td className="border-[1.5px] border-gray-400 py-1.5 text-blue-500 italic px-2 text-left" colSpan={3}>웹사이트(0개), 앱(0개)</td>
                      </tr>
                    </tbody>
                  </table>
                  <div className="flex items-center gap-2 mt-4">
                    <div className="w-3 h-3 border border-gray-400 bg-white" />
                    <span className="font-bold text-[13px] text-black tracking-tight">대표자 현황</span>
                  </div>
                  <table className="w-full border-collapse border-[1.5px] border-gray-400 text-[10px] text-center tracking-tight">
                    <tbody>
                      <tr>
                        <th className="border-[1.5px] border-gray-400 bg-[#F3F4F6] w-[20%] py-1.5 font-bold text-black">성명</th>
                        <td className="border-[1.5px] border-gray-400 w-[30%] py-1.5 text-blue-500 italic">O O O</td>
                        <th className="border-[1.5px] border-gray-400 bg-[#F3F4F6] w-[20%] py-1.5 font-bold text-black">생년월일</th>
                        <td className="border-[1.5px] border-gray-400 w-[30%] py-1.5 text-blue-500 italic">00. 00. 00</td>
                      </tr>
                      <tr>
                        <th className="border-[1.5px] border-gray-400 bg-[#F3F4F6] py-1.5 font-bold text-black">최종학력</th>
                        <td className="border-[1.5px] border-gray-400 py-1.5 text-blue-500 italic">OO대학교</td>
                        <th className="border-[1.5px] border-gray-400 bg-[#F3F4F6] py-1.5 font-bold text-black">전공</th>
                        <td className="border-[1.5px] border-gray-400 py-1.5 text-blue-500 italic">OO학과</td>
                      </tr>
                      <tr>
                        <th className="border-[1.5px] border-gray-400 bg-[#F3F4F6] py-1.5 font-bold text-black">연락처</th>
                        <td className="border-[1.5px] border-gray-400 py-1.5 text-blue-500 italic">010-0000-0000</td>
                        <th className="border-[1.5px] border-gray-400 bg-[#F3F4F6] py-1.5 font-bold text-black">이메일</th>
                        <td className="border-[1.5px] border-gray-400 py-1.5 text-blue-500 italic">OOO@OO.com</td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                {/* AFTER: AI가 채운 양식 */}
                <div className="absolute inset-0 bg-white p-5 h-[520px] flex flex-col gap-2 transition-all duration-[2500ms] ease-in-out"
                  style={{ clipPath: isAiScanning ? 'inset(0 0 0 0)' : 'inset(0 100% 0 0)' }}>
                  <div className="absolute top-3 right-3 flex items-center gap-2 z-10">
                    {isAiDone && (
                      <button onClick={() => { setIsAiScanning(false); setIsAiDone(false); }}
                        className="bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 px-2.5 py-0.5 rounded-full flex items-center gap-1 shadow-sm text-[9px] font-bold transition-all active:scale-95 cursor-pointer">
                        <RefreshCw size={10} /> 되돌리기
                      </button>
                    )}
                    <div className="bg-blue-50 border border-blue-200 px-2.5 py-0.5 rounded-full shadow-sm">
                      <span className="text-[9px] font-bold text-blue-600">AI 자동 채우기 완료</span>
                    </div>
                  </div>
                  <div className="border-[1.5px] border-gray-500 bg-[#E5E7EB] py-2.5 text-center">
                    <h2 className="text-[18px] font-extrabold text-black tracking-tighter">사업계획서</h2>
                  </div>
                  <div className="flex items-center gap-2 mt-3">
                    <div className="w-3 h-3 border border-gray-400 bg-black" />
                    <span className="font-bold text-[13px] text-black tracking-tight">일반현황</span>
                  </div>
                  <table className="w-full border-collapse border-[1.5px] border-gray-400 text-[10px] text-center tracking-tight">
                    <tbody>
                      <tr>
                        <th className="border-[1.5px] border-gray-400 bg-[#F3F4F6] w-[20%] py-1.5 font-bold text-black">기업명</th>
                        <td className="border-[1.5px] border-gray-400 w-[30%] py-1.5 text-black font-semibold px-1 bg-[#EFF6FF]">(주)이지테크</td>
                        <th className="border-[1.5px] border-gray-400 bg-[#F3F4F6] w-[20%] py-1.5 font-bold text-black">개업연월일</th>
                        <td className="border-[1.5px] border-gray-400 w-[30%] py-1.5 text-black font-semibold px-1 bg-[#EFF6FF]">2024. 01. 15</td>
                      </tr>
                      <tr>
                        <th className="border-[1.5px] border-gray-400 bg-[#F3F4F6] py-1.5 font-bold text-black">사업자 구분</th>
                        <td className="border-[1.5px] border-gray-400 py-1.5 text-black font-semibold bg-[#EFF6FF]">법인사업자</td>
                        <th className="border-[1.5px] border-gray-400 bg-[#F3F4F6] py-1.5 font-bold text-black">대표자 유형</th>
                        <td className="border-[1.5px] border-gray-400 py-1.5 text-black font-semibold bg-[#EFF6FF]">단독</td>
                      </tr>
                      <tr>
                        <th className="border-[1.5px] border-gray-400 bg-[#F3F4F6] py-1.5 font-bold text-black">사업자등록번호</th>
                        <td className="border-[1.5px] border-gray-400 py-1.5 text-black font-semibold bg-[#EFF6FF]">123-45-67890</td>
                        <th className="border-[1.5px] border-gray-400 bg-[#F3F4F6] py-1.5 font-bold text-black">소재지</th>
                        <td className="border-[1.5px] border-gray-400 py-1.5 text-black font-semibold bg-[#EFF6FF]">서울 강남구</td>
                      </tr>
                    </tbody>
                  </table>
                  <table className="w-full border-collapse border-[1.5px] border-gray-400 text-[10px] text-center tracking-tight mt-2">
                    <tbody>
                      <tr>
                        <th className="border-[1.5px] border-gray-400 bg-[#F3F4F6] w-[20%] py-1.5 font-bold text-black">창업아이템명</th>
                        <td className="border-[1.5px] border-gray-400 w-[80%] py-1.5 text-black font-semibold bg-[#EFF6FF]" colSpan={3}>LLM기반 HWPX 문서 자동 작성</td>
                      </tr>
                      <tr>
                        <th className="border-[1.5px] border-gray-400 bg-[#F3F4F6] py-1.5 font-bold text-black">산출물</th>
                        <td className="border-[1.5px] border-gray-400 py-1.5 text-black font-semibold px-2 text-left bg-[#EFF6FF]" colSpan={3}>SaaS 웹 플랫폼 (1식)</td>
                      </tr>
                    </tbody>
                  </table>
                  <div className="flex items-center gap-2 mt-4">
                    <div className="w-3 h-3 border border-gray-400 bg-black" />
                    <span className="font-bold text-[13px] text-black tracking-tight">대표자 현황</span>
                  </div>
                  <table className="w-full border-collapse border-[1.5px] border-gray-400 text-[10px] text-center tracking-tight">
                    <tbody>
                      <tr>
                        <th className="border-[1.5px] border-gray-400 bg-[#F3F4F6] w-[20%] py-1.5 font-bold text-black">성명</th>
                        <td className="border-[1.5px] border-gray-400 w-[30%] py-1.5 text-black font-semibold bg-[#EFF6FF]">홍길동</td>
                        <th className="border-[1.5px] border-gray-400 bg-[#F3F4F6] w-[20%] py-1.5 font-bold text-black">생년월일</th>
                        <td className="border-[1.5px] border-gray-400 w-[30%] py-1.5 text-black font-semibold bg-[#EFF6FF]">1990. 03. 15</td>
                      </tr>
                      <tr>
                        <th className="border-[1.5px] border-gray-400 bg-[#F3F4F6] py-1.5 font-bold text-black">최종학력</th>
                        <td className="border-[1.5px] border-gray-400 py-1.5 text-black font-semibold bg-[#EFF6FF]">한국대학교</td>
                        <th className="border-[1.5px] border-gray-400 bg-[#F3F4F6] py-1.5 font-bold text-black">전공</th>
                        <td className="border-[1.5px] border-gray-400 py-1.5 text-black font-semibold bg-[#EFF6FF]">컴퓨터공학</td>
                      </tr>
                      <tr>
                        <th className="border-[1.5px] border-gray-400 bg-[#F3F4F6] py-1.5 font-bold text-black">연락처</th>
                        <td className="border-[1.5px] border-gray-400 py-1.5 text-black font-semibold bg-[#EFF6FF]">010-1234-5678</td>
                        <th className="border-[1.5px] border-gray-400 bg-[#F3F4F6] py-1.5 font-bold text-black">이메일</th>
                        <td className="border-[1.5px] border-gray-400 py-1.5 text-black font-semibold bg-[#EFF6FF]">hong@eazy.kr</td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                {/* 스캔 디바이더 */}
                <div className={`absolute top-0 bottom-0 z-20 pointer-events-none transition-all duration-[2500ms] ease-in-out ${isAiScanning && !isAiDone ? 'opacity-100' : 'opacity-0'}`}
                  style={{ left: isAiScanning ? '100%' : '0%' }}>
                  <div className="w-[3px] h-full bg-gradient-to-b from-transparent via-[#3B82F6] to-transparent"
                    style={{ boxShadow: '0 0 16px rgba(37,99,235,0.8)' }} />
                  <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-[#2563EB] flex items-center justify-center shadow-lg"
                    style={{ animation: 'aiIconPulse 1.5s ease-in-out infinite' }}>
                    <Wand2 size={16} className="text-white" />
                  </div>
                </div>
              </div>

            </div>
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════════
          섹션 2: 이렇게 동작합니다 (3단계)
      ══════════════════════════════════════════ */}
      <section className="py-16 bg-white border-t border-gray-100">
        <div className="max-w-screen-xl mx-auto px-8 lg:px-12">
          <h2 className="text-2xl font-extrabold tracking-tight text-center mb-2">
            이렇게 동작합니다
          </h2>
          <p className="text-sm text-[#57423c]/60 text-center mb-10">
            3단계, 평균 <strong className="text-[#1a1c1b]">3분</strong> — 반복 복붙이 사라집니다
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-3xl mx-auto">
            {/* Step 1 */}
            <div className="scroll-fade relative flex flex-col items-center text-center p-6 rounded-2xl bg-[#f9f9f6] border border-gray-100" data-delay="0">
              <div className="w-10 h-10 rounded-xl bg-[#1a1c1b] text-white flex items-center justify-center font-black text-lg mb-4">1</div>
              <h3 className="font-bold text-base text-[#1a1c1b] mb-1.5">양식 파일 올리기</h3>
              <p className="text-sm text-[#57423c]/70 leading-relaxed">사업계획서, 견적서, 이력서 등<br />채워야 할 HWP·HWPX·DOCX 양식</p>
              <div className="hidden md:flex absolute -right-3 top-1/2 -translate-y-1/2 z-10 w-6 h-6 rounded-full bg-white border border-gray-200 items-center justify-center text-[#57423c]/65 text-xs font-bold">→</div>
            </div>
            {/* Step 2 */}
            <div className="scroll-fade relative flex flex-col items-center text-center p-6 rounded-2xl bg-[#f9f9f6] border border-gray-100" data-delay="100">
              <div className="w-10 h-10 rounded-xl bg-[#2563EB] text-white flex items-center justify-center font-black text-lg mb-4">2</div>
              <h3 className="font-bold text-base text-[#1a1c1b] mb-1.5">내 자료 올리기</h3>
              <p className="text-sm text-[#57423c]/70 leading-relaxed">엑셀, 워드, 텍스트<br />— 어떤 형식이든.</p>
              <div className="hidden md:flex absolute -right-3 top-1/2 -translate-y-1/2 z-10 w-6 h-6 rounded-full bg-white border border-gray-200 items-center justify-center text-[#57423c]/65 text-xs font-bold">→</div>
            </div>
            {/* Step 3 */}
            <div className="scroll-fade flex flex-col items-center text-center p-6 rounded-2xl bg-[#f9f9f6] border border-gray-100" data-delay="200">
              <div className="w-10 h-10 rounded-xl bg-[#1E40AF] text-white flex items-center justify-center font-black text-lg mb-4">3</div>
              <h3 className="font-bold text-base text-[#1a1c1b] mb-1.5">완성!</h3>
              <p className="text-sm text-[#57423c]/70 leading-relaxed">AI가 양식에 맞춰 넣어드립니다.<br />HWP·HWPX·DOCX·엑셀로 다운로드.</p>
            </div>
          </div>
          {/* 신뢰 배지 라인 */}
          <div className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 mt-10 text-xs text-[#57423c]/60">
            <span className="whitespace-nowrap">파일 3시간 후 자동 삭제</span>
            <span className="w-1 h-1 rounded-full bg-[#57423c]/40 hidden sm:block" />
            <span className="whitespace-nowrap">AI 학습에 사용 안 함</span>
            <span className="w-1 h-1 rounded-full bg-[#57423c]/40 hidden sm:block" />
            <span className="whitespace-nowrap">로그인 없이 무료 체험</span>
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════════
          섹션 3: 이런 것도 됩니다 (부가 기능)
      ══════════════════════════════════════════ */}
      <section id="demo-section" className="w-full pt-20 pb-20 bg-[#FAFAFA] border-t border-gray-100">
        <div className="max-w-screen-xl mx-auto px-6 lg:px-12">

          <h2 className="scroll-fade text-2xl lg:text-3xl font-bold tracking-tight text-center mb-3">
            이런 것도 됩니다
          </h2>
          <p className="text-sm text-[#57423c]/60 text-center mb-12">AI 매핑 외에도 다양한 자동화 기능을 무료로 쓸 수 있어요</p>

          {/* 메인 기능 2개 (큰 카드) */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mb-5">

            {/* 엑셀 ↔ 문서 쌍방향 */}
            <div className="scroll-fade bg-white p-6 rounded-2xl border border-[#BFDBFE]/20 shadow-[0_4px_20px_rgba(26,28,27,0.04)]" data-delay="0">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-xl bg-[#EFF6FF] flex items-center justify-center">
                  <Layers size={20} className="text-[#2563EB]" />
                </div>
                <h3 className="text-base font-extrabold text-[#1a1c1b] tracking-tight">엑셀 ↔ 문서 쌍방향</h3>
              </div>
              <div className="flex gap-3">
                <Link href="/tool?tab=batch" className="flex-1 p-3 rounded-xl bg-[#f9f9f6] hover:bg-[#EFF6FF] transition-colors group text-center">
                  <p className="text-xs font-bold text-gray-700 mb-1">엑셀 → 문서</p>
                  <p className="text-xs text-gray-500">엑셀 100행 → 문서 100개</p>
                </Link>
                <Link href="/tool?tab=extract" className="flex-1 p-3 rounded-xl bg-[#f9f9f6] hover:bg-[#EFF6FF] transition-colors group text-center">
                  <p className="text-xs font-bold text-gray-700 mb-1">문서 → 엑셀</p>
                  <p className="text-xs text-gray-500">문서 내용을 엑셀로 추출</p>
                </Link>
              </div>
            </div>

            {/* 대량 생성 */}
            <div className="scroll-fade bg-white p-6 rounded-2xl border border-[#BFDBFE]/20 shadow-[0_4px_20px_rgba(26,28,27,0.04)]" data-delay="80">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-xl bg-[#F0FDF4] flex items-center justify-center">
                  <FileSpreadsheet size={20} className="text-emerald-600" />
                </div>
                <div>
                  <h3 className="text-base font-extrabold text-[#1a1c1b] tracking-tight">대량 생성</h3>
                  <p className="text-xs text-[#57423c]/65 mt-0.5">엑셀에 100명 데이터 → 문서 100개 한번에</p>
                </div>
              </div>
              <div className="flex gap-2 flex-wrap">
                {["급여명세서 × 100", "수료증 × 50", "계약서 × 30"].map((ex) => (
                  <span key={ex} className="text-xs bg-[#f0fdf4] text-emerald-700 font-semibold px-2.5 py-1 rounded-full border border-emerald-100">{ex}</span>
                ))}
              </div>
            </div>
          </div>

          {/* 보조 기능 태그 */}
          <div className="scroll-fade flex flex-wrap gap-3 mb-5 justify-center" data-delay="120">
            {[
              { icon: FileText, label: "HWP / HWPX / DOCX 변환 무료" },
              { icon: Merge, label: "다량 문서 합치기" },
              { icon: Stamp, label: "자동 도장 날인" },
              { icon: TableProperties, label: "텍스트 추출" },
              { icon: Calendar, label: "매월 반복 문서" },
            ].map(({ icon: Icon, label }) => (
              <span key={label} className="flex items-center gap-1.5 text-xs bg-white text-[#57423c] font-semibold px-3 py-1.5 rounded-full border border-gray-200 shadow-sm">
                <Icon size={12} className="text-[#2563EB]" />
                {label}
              </span>
            ))}
          </div>

          {/* AI 초안 작성 별도 박스 */}
          <div className="scroll-fade bg-white rounded-2xl border border-amber-100 p-5 max-w-2xl mx-auto" data-delay="160">
            <div className="flex items-start gap-3">
              <div className="w-9 h-9 rounded-xl bg-amber-50 flex items-center justify-center shrink-0 mt-0.5">
                <Wand2 size={16} className="text-amber-500" />
              </div>
              <div>
                <h3 className="text-sm font-extrabold text-[#1a1c1b] mb-1">AI 초안 작성 — 자료가 없어도 괜찮아요</h3>
                <p className="text-sm text-[#57423c]/60 leading-relaxed">
                  양식에 맞는 핵심 질문을 안내해드립니다. 답변하면 초안이 채워져요.
                  <span className="text-[#57423c]/60 ml-1">중요 문서는 반드시 본인이 검토하세요.</span>
                </p>
              </div>
            </div>
          </div>

          {/* 더 많은 기능 토글 */}
          <div className="mt-8 flex justify-center scroll-fade" data-delay="200">
            <button
              onClick={() => setShowMoreFeatures(!showMoreFeatures)}
              className="text-xs font-bold text-gray-500 hover:text-[#2563EB] flex items-center gap-1 px-4 py-2 rounded-full border border-gray-200 hover:border-[#2563EB]/30 transition-all bg-white shadow-sm"
            >
              특수 기능 더보기
              <ChevronRight size={14} className={`transform transition-transform ${showMoreFeatures ? 'rotate-90' : 'rotate-0'}`} />
            </button>
          </div>

          {/* 특수 기능 (도장, 정기문서, 합치기) */}
          <div className={`transition-all duration-500 overflow-hidden ${showMoreFeatures ? 'max-h-75 opacity-100 mt-5' : 'max-h-0 opacity-0'}`}>
            <div className="flex flex-wrap justify-center gap-3 max-w-5xl mx-auto">
              {[
                { icon: Calendar, label: "매월 반복 문서", benefit: "12개월치 문서를 한번에", tab: "periodic" },
                { icon: Stamp, label: "자동 도장 날인", benefit: "(인) 자리에 자동 도장 삽입", tab: "stamp" },
                { icon: Merge, label: "다량 문서 합치기", benefit: "수십 개의 한글 파일 병합", tab: "merge" },
              ].map((feat) => {
                const Icon = feat.icon;
                return (
                  <Link
                    key={feat.label}
                    href={`/tool?tab=${feat.tab}`}
                    className="group py-3 px-5 rounded-xl transition-all hover:-translate-y-1 bg-white border border-[#BFDBFE]/20 hover:border-[#BFDBFE] shadow-[0_4px_16px_rgba(26,28,27,0.03)] hover:shadow-md flex items-center gap-3 w-fit"
                  >
                    <div className="w-10 h-10 rounded-lg bg-[#f9f9f6] group-hover:bg-[#EFF6FF] flex items-center justify-center transition-colors">
                      <Icon size={20} className="text-gray-500 group-hover:text-blue-600" />
                    </div>
                    <div className="text-left">
                      <div className="text-[15px] font-extrabold text-gray-800 tracking-tight">{feat.label}</div>
                      <div className="text-[12px] text-gray-500 mt-0.5">{feat.benefit}</div>
                    </div>
                  </Link>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════════
          섹션 3.5: 인기 양식 갤러리
      ══════════════════════════════════════════ */}
      <section className="w-full py-20 bg-white border-t border-gray-100">
        <div className="max-w-screen-2xl mx-auto px-8 lg:px-12">
          <div className="flex items-center justify-between mb-8 scroll-fade">
            <div>
              <h2 className="text-xl lg:text-2xl font-extrabold text-[#1a1c1b] mb-1">
                다른 사람들이 쓰는 양식, 바로 사용하세요
              </h2>
              <p className="text-base text-[#57423c]">양식 구하러 돌아다닐 필요 없이, 여기서 선택하면 AI가 채워드립니다</p>
            </div>
            <Link
              href="/gallery"
              className="hidden sm:flex items-center gap-1 text-sm font-semibold text-[#2563EB] hover:text-[#1E40AF] transition-colors"
            >
              전체 보기 <ChevronRight size={14} />
            </Link>
          </div>
          <PopularForms />
          <div className="sm:hidden mt-4 text-center">
            <Link
              href="/gallery"
              className="inline-flex items-center gap-1 text-sm font-semibold text-[#2563EB]"
            >
              전체 보기 <ChevronRight size={14} />
            </Link>
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════════
          섹션 4: FAQ + 보안 + 최종 CTA
      ══════════════════════════════════════════ */}
      <section className="py-16 px-8 lg:px-12 bg-[#f9f9f6] border-t border-gray-100">
        <div className="max-w-screen-xl mx-auto">

          {/* FAQ */}
          <div className="max-w-2xl mx-auto mb-16">
            <h2 className="text-2xl font-extrabold tracking-tight text-center mb-8">자주 묻는 질문</h2>
            <div className="space-y-2">
              {FAQS.map((faq, i) => (
                <div key={i} className="bg-white rounded-xl border border-gray-100 overflow-hidden">
                  <button
                    onClick={() => setOpenFaq(openFaq === i ? null : i)}
                    className="w-full flex items-center justify-between px-5 py-4 text-left"
                  >
                    <span className="text-sm font-bold text-[#1a1c1b]">{faq.q}</span>
                    <ChevronDown
                      size={16}
                      className={`text-[#57423c]/60 shrink-0 ml-3 transition-transform duration-200 ${openFaq === i ? 'rotate-180' : ''}`}
                    />
                  </button>
                  {openFaq === i && (
                    <div className="px-5 pb-4">
                      <p className="text-sm text-[#57423c]/70 leading-relaxed">{faq.a}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* 보안 + CTA */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 items-center">

            {/* 왼쪽: 보안 */}
            <div className="scroll-fade" data-delay="0">
              <div className="flex items-center gap-2 mb-5">
                <Shield size={16} className="text-[#1a1c1b]" />
                <span className="text-sm font-bold">내 데이터는 안전합니다</span>
              </div>
              <div className="space-y-2.5">
                <div className="flex items-start gap-3 bg-white rounded-lg px-4 py-3 border border-gray-100">
                  <Server size={14} className="text-[#57423c]/60 mt-0.5 shrink-0" />
                  <span className="text-base text-[#57423c]">양식 분석과 문서 생성은 이 서버에서만 처리됩니다</span>
                </div>
                <div className="flex items-start gap-3 bg-white rounded-lg px-4 py-3 border border-gray-100">
                  <Lock size={14} className="text-[#57423c]/60 mt-0.5 shrink-0" />
                  <span className="text-base text-[#57423c]">AI 자동 채우기만 Google AI를 사용하며, 데이터는 학습에 사용되지 않습니다</span>
                </div>
                <div className="flex items-start gap-3 bg-white rounded-lg px-4 py-3 border border-gray-100">
                  <Trash2 size={14} className="text-[#57423c]/60 mt-0.5 shrink-0" />
                  <span className="text-base text-[#57423c]">업로드된 파일은 3시간 후 자동 삭제됩니다</span>
                </div>
              </div>
            </div>

            {/* 오른쪽: CTA */}
            <div className="scroll-fade text-center lg:text-left" data-delay="150">
              <h2 className="text-2xl lg:text-3xl font-bold mb-3">
                양식 문서, 이제 직접 쓰지 마세요
              </h2>
              <p className="text-base text-[#57423c] mb-6">
                파일 하나만 올리면 바로 시작할 수 있습니다
              </p>
              <Link
                href="/tool"
                className="cta-warm inline-flex items-center gap-2.5 bg-linear-to-r from-[#2563EB] to-[#1E40AF] text-white px-8 py-3.5 rounded-xl text-base font-bold shadow-lg shadow-[#1E40AF]/20 hover:shadow-xl transition-all active:scale-95"
              >
                무료로 시작하기 <ArrowRight size={17} />
              </Link>
              <p className="text-sm text-[#57423c]/60 mt-3">
                <Clock size={10} className="inline mr-1" />
                회원가입 없이 / HWP · HWPX · DOCX 지원
              </p>
            </div>
          </div>
        </div>
      </section>

    </div>
  );
}
