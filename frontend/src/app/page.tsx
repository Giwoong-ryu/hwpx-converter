"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  Wand2, Layers, TableProperties, Calendar,
  Stamp, Merge, FileSpreadsheet, ArrowRight,
  FileText, Shield, ChevronRight,
  Lock, Server, Trash2, Clock, CheckCircle2, ChevronDown
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
              className="bg-linear-to-r from-[#2563EB] to-[#1E40AF] text-white px-5 py-2 rounded-lg font-semibold text-sm hover:opacity-90 transition-all active:scale-95"
            >
              무료로 시작하기
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

          {/* 오른쪽: AI 매핑 플로우 시각화 */}
          <div className="lg:col-span-6 relative hidden lg:flex items-center justify-center py-8">
            <div className="relative flex items-stretch gap-5 w-full max-w-125">

              {/* 왼쪽: 내 자료 */}
              <div className="flex-1 bg-white rounded-2xl border border-[#BFDBFE]/50 shadow-[0_8px_30px_rgba(0,0,0,0.06)] p-5">
                <p className="text-[10px] font-bold text-[#57423c]/40 mb-3 uppercase tracking-widest">내 자료</p>
                <div className="space-y-2">
                  <div className="flex items-center gap-2.5 px-3 py-2 bg-[#f0fdf4] rounded-lg border border-[#107C41]/15">
                    <div className="w-5 h-5 bg-[#107C41] rounded-[3px] flex items-center justify-center text-white font-black text-[9px] shrink-0">X</div>
                    <span className="text-xs font-semibold text-gray-700 truncate">매출현황.xlsx</span>
                  </div>
                  <div className="flex items-center gap-2.5 px-3 py-2 bg-[#EFF6FF] rounded-lg border border-[#2B579A]/15">
                    <div className="w-5 h-5 bg-[#2B579A] rounded-[3px] flex items-center justify-center text-white font-black text-[9px] shrink-0">W</div>
                    <span className="text-xs font-semibold text-gray-700 truncate">회사소개서.docx</span>
                  </div>
                  <div className="flex items-center gap-2.5 px-3 py-2 bg-[#f9f9f6] rounded-lg border border-gray-200">
                    <div className="w-5 h-5 bg-[#4B5563] rounded-[3px] flex items-center justify-center text-white font-black text-[8px] shrink-0">T</div>
                    <span className="text-xs font-semibold text-gray-700 truncate">붙여넣기 텍스트</span>
                  </div>
                  <p className="text-[10px] text-[#57423c]/40 text-center pt-1">어떤 형식이든 OK</p>
                </div>
              </div>

              {/* 가운데: AI 매핑 화살표 */}
              <div className="flex flex-col items-center justify-center gap-3 shrink-0 w-16">
                <div className="w-10 h-10 rounded-full bg-linear-to-br from-[#2563EB] to-[#1E40AF] flex items-center justify-center shadow-lg shadow-[#1E40AF]/20">
                  <Wand2 size={16} className="text-white" />
                </div>
                <div className="flex flex-col items-center gap-1">
                  <div className="w-0.5 h-6 bg-linear-to-b from-[#2563EB]/60 to-transparent" />
                  <span className="text-[9px] font-bold text-[#2563EB] bg-[#EFF6FF] px-2 py-0.5 rounded-full whitespace-nowrap">AI 매핑</span>
                  <div className="w-0.5 h-6 bg-linear-to-b from-transparent to-[#2563EB]/60" />
                </div>
                <ArrowRight size={18} className="text-[#2563EB]" />
              </div>

              {/* 오른쪽: 완성된 양식 */}
              <div className="flex-1 bg-white rounded-2xl border border-[#BFDBFE]/50 shadow-[0_8px_30px_rgba(37,99,235,0.08)] p-4 relative">
                <div className="absolute -top-2.5 right-3 bg-[#2563EB] text-white text-[9px] font-bold px-2.5 py-0.5 rounded-full shadow">완성</div>
                <p className="text-[10px] font-bold text-[#57423c]/40 mb-2 uppercase tracking-widest">완성된 양식</p>
                <div className="bg-[#E5E7EB] py-1.5 text-center mb-2 rounded-sm">
                  <span className="text-[11px] font-extrabold text-black">사업계획서</span>
                </div>
                <table className="w-full text-[8px] border-collapse">
                  <tbody>
                    <tr>
                      <td className="bg-[#F3F4F6] border border-gray-300 px-1.5 py-1 font-bold text-gray-600 w-[38%]">기업명</td>
                      <td className="border border-gray-300 px-1.5 py-1 bg-[#EFF6FF] text-[#1E40AF] font-semibold">(주)이지테크</td>
                    </tr>
                    <tr>
                      <td className="bg-[#F3F4F6] border border-gray-300 px-1.5 py-1 font-bold text-gray-600">대표자</td>
                      <td className="border border-gray-300 px-1.5 py-1 bg-[#EFF6FF] text-[#1E40AF] font-semibold">홍길동</td>
                    </tr>
                    <tr>
                      <td className="bg-[#F3F4F6] border border-gray-300 px-1.5 py-1 font-bold text-gray-600">매출액</td>
                      <td className="border border-gray-300 px-1.5 py-1 bg-[#EFF6FF] text-[#1E40AF] font-semibold">2.4억원</td>
                    </tr>
                    <tr>
                      <td className="bg-[#F3F4F6] border border-gray-300 px-1.5 py-1 font-bold text-gray-600">소재지</td>
                      <td className="border border-gray-300 px-1.5 py-1 bg-[#EFF6FF] text-[#1E40AF] font-semibold">서울 강남구</td>
                    </tr>
                  </tbody>
                </table>
                <div className="mt-2 flex justify-end">
                  <span className="text-[9px] text-emerald-600 font-bold flex items-center gap-0.5">
                    <CheckCircle2 size={9} /> 4개 항목 자동 채움
                  </span>
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
          <p className="text-sm text-[#57423c]/40 text-center mb-10">
            3단계, 평균 <strong className="text-[#1a1c1b]">3분</strong> — 반복 복붙이 사라집니다
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-3xl mx-auto">
            {/* Step 1 */}
            <div className="scroll-fade relative flex flex-col items-center text-center p-6 rounded-2xl bg-[#f9f9f6] border border-gray-100" data-delay="0">
              <div className="w-10 h-10 rounded-xl bg-[#1a1c1b] text-white flex items-center justify-center font-black text-lg mb-4">1</div>
              <h3 className="font-bold text-base text-[#1a1c1b] mb-1.5">양식 파일 올리기</h3>
              <p className="text-sm text-[#57423c]/55 leading-relaxed">사업계획서, 견적서, 이력서 등<br />채워야 할 HWP·HWPX·DOCX 양식</p>
              <div className="hidden md:flex absolute -right-3 top-1/2 -translate-y-1/2 z-10 w-6 h-6 rounded-full bg-white border border-gray-200 items-center justify-center text-[#57423c]/30 text-xs font-bold">→</div>
            </div>
            {/* Step 2 */}
            <div className="scroll-fade relative flex flex-col items-center text-center p-6 rounded-2xl bg-[#f9f9f6] border border-gray-100" data-delay="100">
              <div className="w-10 h-10 rounded-xl bg-[#2563EB] text-white flex items-center justify-center font-black text-lg mb-4">2</div>
              <h3 className="font-bold text-base text-[#1a1c1b] mb-1.5">내 자료 올리기</h3>
              <p className="text-sm text-[#57423c]/55 leading-relaxed">엑셀, 워드, 텍스트<br />— 어떤 형식이든.</p>
              <div className="hidden md:flex absolute -right-3 top-1/2 -translate-y-1/2 z-10 w-6 h-6 rounded-full bg-white border border-gray-200 items-center justify-center text-[#57423c]/30 text-xs font-bold">→</div>
            </div>
            {/* Step 3 */}
            <div className="scroll-fade flex flex-col items-center text-center p-6 rounded-2xl bg-[#f9f9f6] border border-gray-100" data-delay="200">
              <div className="w-10 h-10 rounded-xl bg-[#1E40AF] text-white flex items-center justify-center font-black text-lg mb-4">3</div>
              <h3 className="font-bold text-base text-[#1a1c1b] mb-1.5">완성!</h3>
              <p className="text-sm text-[#57423c]/55 leading-relaxed">AI가 양식에 맞춰 넣어드립니다.<br />HWP·HWPX·DOCX·엑셀로 다운로드.</p>
            </div>
          </div>
          {/* 신뢰 배지 라인 */}
          <div className="flex items-center justify-center gap-8 mt-10 text-xs text-[#57423c]/35">
            <span>파일 3시간 후 자동 삭제</span>
            <span className="w-1 h-1 rounded-full bg-[#57423c]/20" />
            <span>AI 학습에 사용 안 함</span>
            <span className="w-1 h-1 rounded-full bg-[#57423c]/20" />
            <span>로그인 없이 무료 체험</span>
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
          <p className="text-sm text-[#57423c]/40 text-center mb-12">AI 매핑 외에도 다양한 자동화 기능을 무료로 쓸 수 있어요</p>

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
                  <p className="text-xs text-[#57423c]/50 mt-0.5">엑셀에 100명 데이터 → 문서 100개 한번에</p>
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
                  <span className="text-[#57423c]/40 ml-1">중요 문서는 반드시 본인이 검토하세요.</span>
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
                      className={`text-[#57423c]/40 shrink-0 ml-3 transition-transform duration-200 ${openFaq === i ? 'rotate-180' : ''}`}
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
                  <Server size={14} className="text-[#57423c]/40 mt-0.5 shrink-0" />
                  <span className="text-base text-[#57423c]">양식 분석과 문서 생성은 이 서버에서만 처리됩니다</span>
                </div>
                <div className="flex items-start gap-3 bg-white rounded-lg px-4 py-3 border border-gray-100">
                  <Lock size={14} className="text-[#57423c]/40 mt-0.5 shrink-0" />
                  <span className="text-base text-[#57423c]">AI 자동 채우기만 Google AI를 사용하며, 데이터는 학습에 사용되지 않습니다</span>
                </div>
                <div className="flex items-start gap-3 bg-white rounded-lg px-4 py-3 border border-gray-100">
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
                className="cta-warm inline-flex items-center gap-2.5 bg-linear-to-r from-[#2563EB] to-[#1E40AF] text-white px-8 py-3.5 rounded-xl text-base font-bold shadow-lg shadow-[#1E40AF]/20 hover:shadow-xl transition-all active:scale-95"
              >
                무료로 시작하기 <ArrowRight size={17} />
              </Link>
              <p className="text-sm text-[#57423c]/40 mt-3">
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
