"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  Wand2, Layers, TableProperties, Calendar,
  Stamp, Merge, FileSpreadsheet, ArrowRight,
  FileText, Shield, Check, ChevronRight,
  Lock, Server, Trash2, Clock, RefreshCw, UploadCloud
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
            <p className="text-sm text-[#57423c]/40 mt-3">아직 공유된 양식이 없습니다</p>
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
          <p className="text-sm text-[#57423c]/50 mb-3">{f.field_count}개 필드</p>
          <div className="flex items-center justify-between">
            <span className="text-sm text-[#57423c]/40">{f.likes} 좋아요 · {f.downloads}명 사용</span>
            <Link
              href={`/tool?gallery_id=${f.id}`}
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-gradient-to-r from-[#2563EB] to-[#1E40AF] text-white text-xs font-bold hover:opacity-90 transition-opacity"
            >
              바로 사용
            </Link>
          </div>
        </div>
      ))}
    </div>
  );
}

/* ═══ 페이지 ═══ */

export default function LandingPage() {
  const scrollRef = useScrollReveal();
  const [isAiScanning, setIsAiScanning] = useState(false);
  const [isAiDone, setIsAiDone] = useState(false);
  const [showMoreFeatures, setShowMoreFeatures] = useState(false);

  const startScan = () => {
    if (isAiScanning) return;
    setIsAiScanning(true);
    setTimeout(() => {
      setIsAiDone(true);
    }, 2500); // 2.5s duration
  };

  return (
    <div ref={scrollRef} className="min-h-screen bg-[#f9f9f6] text-[#1a1c1b] overflow-hidden">

      {/* ── 네비게이션 ── */}
      <nav className="fixed top-0 w-full z-50 bg-[#f9f9f6]/80 backdrop-blur-xl border-b border-[#BFDBFE]/40">
        <div className="flex justify-between items-center px-8 lg:px-12 py-4 max-w-screen-2xl mx-auto">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-[#1a1c1b] flex items-center justify-center">
              <FileText size={14} className="text-white" strokeWidth={2.2} />
            </div>
            <span className="text-lg font-extrabold tracking-tighter">Eazy HWPX</span>
          </Link>
          <div className="flex items-center gap-4">
            <CouponBadge />
            <Link href="/pricing" className="text-sm text-[#57423c]/70 hover:text-[#1a1c1b] transition-colors">
              요금제
            </Link>
            <Link
              href="/tool"
              className="bg-gradient-to-r from-[#2563EB] to-[#1E40AF] text-white px-5 py-2 rounded-lg font-semibold text-sm hover:opacity-90 transition-all active:scale-95"
            >
              무료로 시작하기
            </Link>
          </div>
        </div>
      </nav>

      {/* ══════════════════════════════════════════
          섹션 1: 히어로 — 좌우 스플릿
          왼쪽: 한글 100% 호환 강조 + 카피 + CTA
          오른쪽: 에디터 목업
      ══════════════════════════════════════════ */}
      <section className="relative pt-28 pb-16 lg:pb-12 lg:min-h-[95vh] flex items-center">
        <div className="absolute inset-0 warm-hero-bg" />
        <div className="relative w-full max-w-screen-2xl mx-auto px-8 lg:px-16 grid grid-cols-1 lg:grid-cols-12 gap-16 items-center">

          {/* 왼쪽: 카피 */}
          <div className="lg:col-span-6">
            {/* 한글 호환 — 히어로 최상단, 메인 메시지 */}
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
              양식 파일 올리고, 내 자료를 넣으면 <strong className="text-[#1a1c1b]">AI가 합쳐서 완성합니다.</strong><br />
              파일 업로드, 복사 붙여넣기, 직접 입력 — 어떤 방식이든.
            </p>

            <div className="hero-stagger hero-s4 flex flex-wrap items-center gap-4 mb-3">
              <Link
                href="/tool"
                className="cta-warm bg-gradient-to-r from-[#2563EB] to-[#1E40AF] text-white px-8 py-3.5 rounded-xl text-base font-bold shadow-lg shadow-[#1E40AF]/20 hover:shadow-xl transition-all active:scale-95 flex items-center gap-2"
              >
                무료로 시작하기 <ArrowRight size={17} />
              </Link>
              <span className="text-sm text-[#57423c]/50">회원가입 없이 바로 사용</span>
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

          {/* 오른쪽: 버블 프레임 + Before/After */}
          <div className="lg:col-span-6 relative hidden lg:flex items-center justify-center h-[460px] scale-[0.85] origin-center translate-x-44">

            {/* ── 입체 버블들 (배경) ── */}
            <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
              {/* 제일 큰 우측 하단 버블 */}
              <div className="absolute top-[15%] right-[-10%] w-[360px] h-[360px] rounded-full bg-white shadow-[inset_-25px_-25px_40px_rgba(0,0,0,0.03),_0_20px_40px_rgba(0,0,0,0.06)] border border-[#F9FAFB]" />

              {/* 좌측 메인 버블 */}
              <div className="absolute top-[5%] left-[5%] w-[260px] h-[260px] rounded-full bg-white shadow-[inset_-20px_-20px_35px_rgba(0,0,0,0.02),_10px_15px_30px_rgba(0,0,0,0.05)] border border-[#F9FAFB]" />

              {/* 상단 겹치는 버블 */}
              <div className="absolute top-[-5%] left-[25%] w-[200px] h-[200px] rounded-full bg-white shadow-[inset_-15px_-15px_30px_rgba(0,0,0,0.02),_5px_10px_20px_rgba(0,0,0,0.03)] border border-[#F9FAFB]" />

              {/* 작은 장식용 버블 (우측 상단) */}
              <div className="absolute top-[0%] right-[10%] w-[120px] h-[120px] rounded-full bg-white shadow-[inset_-10px_-10px_20px_rgba(0,0,0,0.02),_5px_5px_15px_rgba(0,0,0,0.04)]" />

              {/* 하단 겹치는 파란 틴트 버블 */}
              <div className="absolute bottom-[-10%] left-[15%] w-[220px] h-[220px] rounded-full bg-[#FAFAFA] shadow-[inset_-15px_-15px_30px_rgba(0,0,0,0.02),_10px_10px_25px_rgba(37,99,235,0.06)] border border-[#F3F4F6]" />

              {/* 미니 컬러 둥둥 버블 */}
              <div className="absolute top-[40%] right-[2%] w-[80px] h-[80px] rounded-full bg-blue-50 shadow-[inset_-8px_-8px_15px_rgba(37,99,235,0.1),_0_5px_10px_rgba(0,0,0,0.03)] border border-blue-100" />
              <div className="absolute top-[60%] left-[-2%] w-[90px] h-[90px] rounded-full bg-blue-100 shadow-[inset_-10px_-10px_20px_rgba(37,99,235,0.15),_0_5px_15px_rgba(37,99,235,0.1)] opacity-80 border border-blue-200" />
            </div>

            {/* ── 3D 투시 래퍼 ── */}
            <div style={{ perspective: '1600px' }} className="z-10 ml-16 relative flex items-center">

              {/* ── 1. 양식 파일 (Top Left) ── */}
              <div className="absolute top-[10%] left-[-360px] z-30 w-[220px] flex flex-col items-center">
                {/* 기존 UI 모형 박스 */}
                <div className="w-full bg-white rounded-2xl shadow-[0_20px_40px_rgba(0,0,0,0.08),_0_0_0_1px_rgba(0,0,0,0.02)] p-4 transform -rotate-6 transition-transform duration-500 hover:rotate-0 hidden xl:block relative">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-6 h-6 rounded-md bg-[#EEF2FF] flex items-center justify-center text-blue-600">
                      <UploadCloud size={14} />
                    </div>
                    <span className="font-bold text-[16px] text-gray-800 tracking-tight">양식 파일</span>
                  </div>
                  <p className="text-[12px] text-gray-500 mb-3 leading-tight">HWP, HWPX, DOCX 양식을 올리세요.</p>

                  {/* 드롭 존 & 아이콘 */}
                  <div className="relative border-[2px] border-dashed border-[#BFDBFE] rounded-xl py-4 px-4 flex flex-col items-center justify-center bg-[#EFF6FF]/50 mb-3">
                    {/* 양식 파일 아이콘 */}
                    <div className="absolute -top-2 z-20 w-16 h-20 bg-white rounded-lg flex flex-col items-center justify-center border border-[#00A1E9]/40 shadow-lg transform rotate-3 animate-[bounce_3s_infinite]">
                      <div className="absolute top-0 right-0 w-4 h-4 bg-[#00A1E9]/10 border-b border-l border-[#00A1E9]/30 rounded-bl-sm z-10" />
                      <div className="w-8 h-8 bg-[#00A1E9] rounded flex items-center justify-center text-white font-black text-[14px] shadow-sm mb-1 z-0 relative">
                        H
                      </div>
                      <span className="text-[8px] font-black text-[#00A1E9] tracking-tighter">.hwpx</span>
                    </div>
                    <div className="mt-8 w-8 h-8 rounded-full bg-white shadow-sm flex items-center justify-center">
                      <UploadCloud size={16} className="text-[#3B82F6]" />
                    </div>
                  </div>

                  <div className="w-full bg-[#7C88C3] text-white text-center py-2 rounded-lg text-[12px] font-bold shadow-sm">
                    양식 분석
                  </div>
                </div>
              </div>

              {/* ── 2. 내 자료 (Bottom Left) ── */}
              <div className="absolute bottom-[8%] left-[-320px] z-30 w-[220px] flex flex-col items-center">
                {/* 기존 UI 모형 박스 (드롭존으로 변경) */}
                <div className="w-full bg-white rounded-2xl shadow-[0_15px_35px_rgba(0,0,0,0.07),_0_0_0_1px_rgba(0,0,0,0.02)] p-4 transform rotate-4 transition-transform duration-500 hover:rotate-0 hidden xl:block relative">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-6 h-6 rounded-md bg-emerald-50 flex items-center justify-center text-emerald-600">
                      <FileSpreadsheet size={14} />
                    </div>
                    <span className="font-bold text-[16px] text-gray-800 tracking-tight">내 자료</span>
                  </div>
                  <p className="text-[12px] text-gray-500 mb-3 leading-tight">엑셀, 워드, 텍스트 또는 직접 입력</p>

                  {/* 드롭 존 & 아이콘들 */}
                  <div className="relative border-[2px] border-dashed border-emerald-200 rounded-xl py-3 px-4 flex flex-col items-center justify-center bg-emerald-50/50 mb-3">
                    {/* 데이터 아이콘들 */}
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

                  <div className="w-full bg-emerald-50 text-emerald-600 border border-emerald-200 text-center py-2 rounded-lg text-[12px] font-bold shadow-sm">
                    직접 입력
                  </div>
                </div>
              </div>

              {/* ── 큰 화살표 (양식+내자료 → 사업계획서) ── */}
              <div className="absolute top-1/2 left-[-60px] -translate-y-1/2 z-40">
                <div className="bg-white p-3 rounded-full shadow-xl border border-gray-200">
                  <ArrowRight size={22} className="text-[#2563EB]" />
                </div>
              </div>

              {/* ── 실제 양식 문서 카드 (3D 회전 적용) ── */}
              <div className="relative w-[520px] bg-white shadow-[-20px_30px_60px_rgba(0,0,0,0.18),_-5px_10px_30px_rgba(0,0,0,0.10),_0_0_0_1px_rgba(0,0,0,0.04)] overflow-hidden font-sans"
                style={{
                  transform: 'rotateX(12deg) rotateY(-22deg) rotateZ(2deg) scale(1.0)',
                  transformStyle: 'preserve-3d'
                }}>

                {/* 스캔 시작 버튼 오버레이 */}
                {!isAiScanning && !isAiDone && (
                  <div className="absolute inset-0 z-30 flex items-center justify-center bg-white/5 transition-opacity duration-300">
                    <div className="relative group cursor-pointer" onClick={startScan}>
                      {/* 깔끔한 검은 글씨 Click 유도 문구 */}
                      <div className="absolute -top-7 left-1/2 -translate-x-1/2 flex flex-col items-center gap-0.5 pointer-events-none text-gray-800 font-extrabold text-[12px] animate-bounce">
                        <span>클릭</span>
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="M12 5v14" /><path d="m19 12-7 7-7-7" /></svg>
                      </div>

                      {/* 마우스 커서 올릴 시 버튼 클릭되는 효과 */}
                      <button className="bg-blue-600 group-hover:bg-blue-700 text-white px-8 py-4 rounded-full font-bold shadow-2xl flex items-center gap-3 transform transition-all group-hover:scale-105 active:scale-95 text-[15px] pointer-events-none">
                        <Wand2 size={24} />
                        AI로 양식 자동 완성하기
                      </button>

                      {/* 가상 마우스 커서 */}
                      <div className="absolute -bottom-6 -right-6 text-gray-800 transform rotate-[-15deg] group-hover:-translate-x-2 group-hover:-translate-y-2 transition-transform duration-300 drop-shadow-xl pointer-events-none hidden sm:block">
                        <svg width="32" height="32" viewBox="0 0 24 24" fill="white" stroke="#1f2937" strokeWidth="1.5">
                          <path d="M4 2v20l6-6h10z" />
                        </svg>
                      </div>
                    </div>
                  </div>
                )}

                {/* BEFORE (아무것도 없는 빈 양식) */}
                <div className="bg-white p-5 relative w-full h-[520px] flex flex-col gap-2">
                  {/* 타이틀 영역 */}
                  <div className="border-[1.5px] border-gray-500 bg-[#E5E7EB] py-2.5 text-center">
                    <h2 className="text-[18px] font-extrabold text-black tracking-tighter">사업계획서</h2>
                  </div>

                  {/* 일반 현황 섹션 헤더 */}
                  <div className="flex items-center gap-2 mt-3">
                    <div className="w-3 h-3 border border-gray-400 bg-white" />
                    <span className="font-bold text-[13px] text-black tracking-tight">일반현황</span>
                  </div>

                  {/* 테이블 1 */}
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

                  {/* 테이블 2 */}
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
                      <tr>
                        <th className="border-[1.5px] border-gray-400 bg-[#F3F4F6] py-1.5 font-bold text-black">지원분야</th>
                        <td className="border-[1.5px] border-gray-400 py-1.5 text-left px-2 text-[9px] text-gray-500" colSpan={3}>기계 / 전기 / 정보통신 / 바이오 / 에너지</td>
                      </tr>
                    </tbody>
                  </table>

                  {/* 테이블 3 - 대표자 정보 */}
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
                      <tr>
                        <th className="border-[1.5px] border-gray-400 bg-[#F3F4F6] py-1.5 font-bold text-black">주소</th>
                        <td className="border-[1.5px] border-gray-400 py-1.5 text-blue-500 italic" colSpan={3}>OO시 OO구 OO로 000</td>
                      </tr>
                      <tr>
                        <th className="border-[1.5px] border-gray-400 bg-[#F3F4F6] py-1.5 font-bold text-black">창업경험</th>
                        <td className="border-[1.5px] border-gray-400 py-1.5 text-blue-500 italic" colSpan={3}>유 / 무</td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                {/* AFTER (AI가 완벽히 채운 상태) */}
                <div className="absolute inset-0 bg-white p-5 h-[520px] flex flex-col gap-2 transition-all duration-[2500ms] ease-in-out"
                  style={{ clipPath: isAiScanning ? 'inset(0 0 0 0)' : 'inset(0 100% 0 0)' }}>

                  {/* 우상단 라벨 및 시작 초기화 버튼 */}
                  <div className="absolute top-3 right-3 flex items-center gap-2 z-10">
                    {isAiDone && (
                      <button
                        onClick={() => { setIsAiScanning(false); setIsAiDone(false); }}
                        className="bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 px-2.5 py-0.5 rounded-full flex items-center gap-1 shadow-sm text-[9px] font-bold transition-all active:scale-95 cursor-pointer"
                      >
                        <RefreshCw size={10} />
                        되돌리기
                      </button>
                    )}
                    <div className="bg-blue-50 border border-blue-200 px-2.5 py-0.5 rounded-full shadow-sm">
                      <span className="text-[9px] font-bold text-blue-600">AI 자동 채우기 완료</span>
                    </div>
                  </div>

                  {/* 타이틀 영역 - BEFORE와 동일 */}
                  <div className="border-[1.5px] border-gray-500 bg-[#E5E7EB] py-2.5 text-center">
                    <h2 className="text-[18px] font-extrabold text-black tracking-tighter">사업계획서</h2>
                  </div>

                  {/* 일반 현황 섹션 헤더 */}
                  <div className="flex items-center gap-2 mt-3">
                    <div className="w-3 h-3 border border-gray-400 bg-black" />
                    <span className="font-bold text-[13px] text-black tracking-tight">일반현황</span>
                  </div>

                  {/* 테이블 1 */}
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

                  {/* 테이블 2 */}
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
                      <tr>
                        <th className="border-[1.5px] border-gray-400 bg-[#F3F4F6] py-1.5 font-bold text-black">지원분야</th>
                        <td className="border-[1.5px] border-gray-400 py-1.5 text-left px-2 text-[9px] text-black font-semibold bg-[#EFF6FF]" colSpan={3}>지식서비스 (정보통신)</td>
                      </tr>
                    </tbody>
                  </table>

                  {/* 테이블 3 - 대표자 정보 */}
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
                      <tr>
                        <th className="border-[1.5px] border-gray-400 bg-[#F3F4F6] py-1.5 font-bold text-black">주소</th>
                        <td className="border-[1.5px] border-gray-400 py-1.5 text-black font-semibold bg-[#EFF6FF]" colSpan={3}>서울시 강남구 테헤란로 123</td>
                      </tr>
                      <tr>
                        <th className="border-[1.5px] border-gray-400 bg-[#F3F4F6] py-1.5 font-bold text-black">창업경험</th>
                        <td className="border-[1.5px] border-gray-400 py-1.5 text-black font-semibold bg-[#EFF6FF]" colSpan={3}>유 (2년)</td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                {/* 좌우 스캐닝 디바이더 */}
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

        {/* 스크롤 유도 화살표 */}
        <div className="absolute bottom-6 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 animate-bounce cursor-pointer z-20 text-[#57423c]/40 hover:text-[#57423c]/80 transition-colors"
          onClick={() => document.getElementById('demo-section')?.scrollIntoView({ behavior: 'smooth', block: 'center' })}>
          <span className="text-xs uppercase font-bold tracking-widest hidden lg:block">Scroll to explore</span>
          <ArrowRight className="rotate-90 hidden lg:block" size={16} />
        </div>
      </section>

      {/* ══════════════════════════════════════════
          섹션 2: Before/After + 7가지 기능 (합침)
      ══════════════════════════════════════════ */}
      <section id="demo-section" className="w-full pt-40 pb-24 bg-[#FAFAFA] border-t border-gray-100">
        <div className="max-w-screen-xl mx-auto px-6 lg:px-12">

          {/* Before/After */}
          <h2 className="scroll-fade text-2xl lg:text-3xl font-bold tracking-tight text-center mb-10">
            실제로 이렇게 채워집니다
          </h2>

          <div className="grid grid-cols-1 lg:grid-cols-[1fr_auto_1fr] gap-6 items-center max-w-[1400px] mx-auto mb-20 px-4">
            <div className="scroll-fade" data-delay="0">
              <div className="text-[12px] font-bold text-[#57423c]/40 tracking-wide uppercase mb-3 text-center">Before</div>
              <div className="bg-white rounded-xl overflow-hidden shadow-[0_10px_30px_rgba(26,28,27,0.06)] border border-[#BFDBFE]/10 transition-transform duration-500 hover:scale-[1.02]">
                <img src="/images/before-empty.png" alt="빈 양식" className="w-full h-auto" />
              </div>
            </div>
            <div className="scroll-fade flex justify-center" data-delay="100">
              <div className="w-10 h-10 rounded-full bg-gradient-to-r from-[#2563EB] to-[#1E40AF] flex items-center justify-center shadow-md">
                <ArrowRight size={16} className="text-white lg:rotate-0 rotate-90" />
              </div>
            </div>
            <div className="scroll-fade" data-delay="200">
              <div className="text-xs font-bold text-[#1E40AF] tracking-wide uppercase mb-2 text-center">After — 3분</div>
              <div className="bg-white rounded-xl overflow-hidden shadow-[0_10px_30px_rgba(26,28,27,0.04)] border border-[#1E40AF]/10">
                <img src="/images/after-filled.png" alt="채워진 양식" className="w-full h-auto" />
              </div>
            </div>
          </div>

          {/* 3가지 핵심 기능 */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">

            {/* 1. AI 자동 채우기 */}
            <Link href="/tool?tab=ai" className="scroll-fade group text-center p-5 rounded-xl transition-all hover:-translate-y-1 bg-gradient-to-br from-[#2563EB] to-[#1E40AF] text-white shadow-lg shadow-[#1E40AF]/15 flex flex-col justify-center" data-delay="0">
              <div className="w-12 h-12 rounded-lg flex items-center justify-center mx-auto mb-3 bg-white/20 transition-colors">
                <Wand2 size={24} className="text-white" />
              </div>
              <div className="text-[17px] font-extrabold mb-1 tracking-tight">AI 자동 채우기</div>
              <div className="text-[13px] leading-relaxed text-white/90">내 자료를 양식에 맞춰 AI가 넣어드립니다</div>
            </Link>

            {/* 2. 문서 ⇄ 엑셀 (합친 버튼) */}
            <div className="scroll-fade bg-white p-3 rounded-xl border border-[#BFDBFE]/20 shadow-[0_4px_16px_rgba(26,28,27,0.03)] flex flex-col" data-delay="50">
              <div className="text-center text-[15px] font-extrabold text-gray-800 mb-3 mt-1 tracking-tight">문서 ⇄ 엑셀 쌍방향 변환</div>
              <div className="flex gap-2 flex-1 relative">
                <Link href="/tool?tab=batch" className="flex-1 flex flex-col items-center justify-center p-4 rounded-lg bg-[#f9f9f6] hover:bg-[#EFF6FF] transition-colors group">
                  <Layers size={22} className="text-gray-500 group-hover:text-[#2563EB] mb-2" />
                  <div className="text-[12px] font-extrabold text-gray-700">엑셀 → 문서 만들기</div>
                </Link>
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 flex items-center justify-center text-gray-300 z-10 w-6 h-6 bg-white rounded-full shadow-sm">
                  <ArrowRight size={14} className="transform rotate-0 absolute translate-y-1.5" />
                  <ArrowRight size={14} className="transform rotate-180 absolute -translate-y-1.5" />
                </div>
                <Link href="/tool?tab=extract" className="flex-1 flex flex-col items-center justify-center p-4 rounded-lg bg-[#f9f9f6] hover:bg-[#EFF6FF] transition-colors group">
                  <TableProperties size={22} className="text-gray-500 group-hover:text-[#2563EB] mb-2" />
                  <div className="text-[12px] font-extrabold text-gray-700">문서 → 엑셀표 추출</div>
                </Link>
              </div>
            </div>

            {/* 3. 엑셀 채우기 */}
            <Link href="/tool?tab=excel" className="scroll-fade group text-center p-5 rounded-xl transition-all hover:-translate-y-1 bg-white border border-[#BFDBFE]/20 shadow-[0_4px_16px_rgba(26,28,27,0.03)] flex flex-col justify-center" data-delay="100">
              <div className="w-12 h-12 rounded-lg flex items-center justify-center mx-auto mb-3 bg-[#f9f9f6] group-hover:bg-[#EFF6FF] transition-colors">
                <FileSpreadsheet size={24} className="text-gray-500 group-hover:text-[#2563EB]" />
              </div>
              <div className="text-[17px] font-extrabold mb-1 text-gray-800 tracking-tight">엑셀 빈칸 채우기</div>
              <div className="text-[13px] leading-relaxed text-gray-500">동일한 양식의 수백 개 빈칸 일괄 작성</div>
            </Link>

          </div>

          {/* 확장 토글 버튼 */}
          <div className="mt-6 flex justify-center scroll-fade" data-delay="150">
            <button
              onClick={() => setShowMoreFeatures(!showMoreFeatures)}
              className="text-xs font-bold text-gray-500 hover:text-[#2563EB] flex items-center gap-1 px-4 py-2 rounded-full border border-gray-200 hover:border-[#2563EB]/30 transition-all bg-white shadow-sm"
            >
              특수 기능 더보기
              <ChevronRight size={14} className={`transform transition-transform ${showMoreFeatures ? 'rotate-90' : 'rotate-0'}`} />
            </button>
          </div>

          {/* 특수 기능 (도장, 정기문서, 합치기) */}
          <div className={`transition-all duration-500 overflow-hidden ${showMoreFeatures ? 'max-h-[300px] opacity-100 mt-5' : 'max-h-0 opacity-0'}`}>
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
          섹션 2.5: 인기 양식 갤러리
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
          섹션 3: 보안 + CTA (합침)
      ══════════════════════════════════════════ */}
      <section className="py-14 px-8 lg:px-12">
        <div className="max-w-screen-2xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-10 items-center">

          {/* 왼쪽: 보안 */}
          <div className="scroll-fade" data-delay="0">
            <div className="flex items-center gap-2 mb-5">
              <Shield size={16} className="text-[#1a1c1b]" />
              <span className="text-sm font-bold">내 데이터는 안전합니다</span>
            </div>
            <div className="space-y-2.5">
              <div className="flex items-start gap-3 bg-[#f4f4f1] rounded-lg px-4 py-3">
                <Server size={14} className="text-[#57423c]/40 mt-0.5 shrink-0" />
                <span className="text-base text-[#57423c]">양식 분석과 문서 생성은 이 서버에서만 처리됩니다</span>
              </div>
              <div className="flex items-start gap-3 bg-[#f4f4f1] rounded-lg px-4 py-3">
                <Lock size={14} className="text-[#57423c]/40 mt-0.5 shrink-0" />
                <span className="text-base text-[#57423c]">AI 자동 채우기만 Google AI를 사용하며, 데이터는 학습에 사용되지 않습니다</span>
              </div>
              <div className="flex items-start gap-3 bg-[#f4f4f1] rounded-lg px-4 py-3">
                <Trash2 size={14} className="text-[#57423c]/40 mt-0.5 shrink-0" />
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
              className="cta-warm inline-flex items-center gap-2.5 bg-gradient-to-r from-[#2563EB] to-[#1E40AF] text-white px-8 py-3.5 rounded-xl text-base font-bold shadow-lg shadow-[#1E40AF]/20 hover:shadow-xl transition-all active:scale-95"
            >
              무료로 시작하기 <ArrowRight size={17} />
            </Link>
            <p className="text-sm text-[#57423c]/40 mt-3">
              <Clock size={10} className="inline mr-1" />
              회원가입 없이 / HWP · HWPX · DOCX 지원
            </p>
          </div>
        </div>
      </section>

      {/* ── 푸터 ── */}
      <footer className="border-t border-[#BFDBFE]/40 py-6 px-8 lg:px-12 bg-[#f4f4f1]">
        <div className="max-w-screen-2xl mx-auto flex justify-between items-center">
          <span className="text-base font-bold">Eazy HWPX</span>
          <span className="text-sm text-[#57423c]/40">HTTPS 암호화 · 파일 3시간 후 삭제</span>
        </div>
      </footer>
    </div>
  );
}
