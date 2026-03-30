"use client";

import { useEffect, useRef } from "react";
import Link from "next/link";
import {
  Wand2, Layers, TableProperties, Calendar,
  Stamp, Merge, FileSpreadsheet, ArrowRight,
  Upload, FileText, Download, Shield, Zap,
  Clock, Sparkles
} from "lucide-react";

/* ───── 데이터 ───── */

const FEATURES = [
  { icon: Wand2, label: "AI 자동 작성", benefit: "주제만 알려주면 문서를 대신 써줍니다", highlight: true, span: "col-span-2" },
  { icon: Layers, label: "엑셀 → 문서", benefit: "엑셀 100행이면 문서 100개가 한번에", span: "" },
  { icon: TableProperties, label: "문서 → 엑셀", benefit: "문서 안의 모든 글자를 엑셀로 정리", span: "" },
  { icon: Calendar, label: "정기문서", benefit: "매달 보고서를 12개월치 한번에", span: "" },
  { icon: Stamp, label: "도장", benefit: "(인) 자리에 도장을 자동으로 찍어줍니다", span: "" },
  { icon: Merge, label: "합치기", benefit: "여러 파일을 하나로 합쳐줍니다", span: "" },
  { icon: FileSpreadsheet, label: "엑셀 채우기", benefit: "엑셀 양식의 빈칸을 자동으로 채웁니다", span: "" },
];

const STEPS = [
  { icon: Upload, title: "양식 업로드", desc: "HWP · HWPX · DOCX", color: "from-indigo-500 to-indigo-600" },
  { icon: FileText, title: "내용 채우기", desc: "텍스트 · 엑셀 · AI 작성", color: "from-violet-500 to-violet-600" },
  { icon: Download, title: "완성 다운로드", desc: "HWP · HWPX · DOCX", color: "from-emerald-500 to-emerald-600" },
];

const STATS = [
  { icon: Zap, value: "7가지", label: "자동화 도구" },
  { icon: Clock, value: "3단계", label: "간단한 사용법" },
  { icon: Sparkles, value: "무료", label: "바로 사용 가능" },
];

/* ───── 스크롤 애니메이션 훅 ───── */

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
            // stagger: data-delay 속성으로 개별 딜레이
            const delay = Number(entry.target.getAttribute("data-delay") || 0);
            setTimeout(() => entry.target.classList.add("visible"), delay);
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.08 }
    );
    targets.forEach((t) => observer.observe(t));
    return () => observer.disconnect();
  }, []);
  return ref;
}

/* ───── 페이지 ───── */

export default function LandingPage() {
  const scrollRef = useScrollReveal();

  return (
    <div ref={scrollRef} className="min-h-screen bg-white overflow-hidden">

      {/* ── 헤더 ── */}
      <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-lg border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-6 py-3.5 flex items-center justify-between">
          <span className="text-lg font-bold tracking-tight text-gray-900">Eazy HWPX</span>
          <Link
            href="/tool"
            className="text-sm font-medium text-indigo-600 hover:text-indigo-700 transition-colors flex items-center gap-1"
          >
            바로 시작하기
            <ArrowRight size={14} />
          </Link>
        </div>
      </header>

      {/* ── 히어로 ── */}
      <section className="hero-mesh relative pt-20 pb-24 px-6">
        <div className="max-w-3xl mx-auto text-center">
          {/* 포맷 뱃지 */}
          <div className="hero-animate hero-delay-1 inline-flex items-center gap-2 bg-white/70 backdrop-blur-sm border border-gray-200/60 rounded-full px-4 py-1.5 mb-8">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            <span className="text-xs font-medium text-gray-700">HWP · HWPX · DOCX 지원</span>
          </div>

          {/* 헤드라인 */}
          <h1 className="hero-animate hero-delay-2 text-[2.75rem] leading-[1.2] font-bold tracking-tight text-gray-900 mb-5">
            아직도 양식에<br />
            <span className="bg-gradient-to-r from-indigo-600 via-violet-600 to-indigo-600 bg-clip-text text-transparent">
              하나하나 입력
            </span>하세요?
          </h1>

          {/* 서브 */}
          <p className="hero-animate hero-delay-3 text-lg text-gray-500 mb-10 leading-relaxed">
            양식 파일만 올리면, AI가 알아서 채워줍니다
          </p>

          {/* CTA */}
          <div className="hero-animate hero-delay-4">
            <Link
              href="/tool"
              className="cta-glow relative z-10 inline-flex items-center gap-2.5 bg-gradient-to-r from-indigo-600 to-violet-600 text-white px-9 py-4 rounded-2xl text-base font-semibold hover:shadow-lg hover:shadow-indigo-200 transition-all duration-300"
            >
              지금 시작하기
              <ArrowRight size={18} />
            </Link>
          </div>
        </div>
      </section>

      {/* ── 숫자 통계 ── */}
      <section className="border-y border-gray-100 bg-white">
        <div className="max-w-4xl mx-auto px-6 py-8 flex items-center justify-center gap-12">
          {STATS.map((stat, i) => {
            const Icon = stat.icon;
            return (
              <div key={stat.label} className="scroll-fade flex items-center gap-3" data-delay={i * 100}>
                <div className="w-10 h-10 rounded-xl bg-indigo-50 flex items-center justify-center">
                  <Icon size={18} className="text-indigo-600" />
                </div>
                <div>
                  <div className="text-lg font-bold text-gray-900">{stat.value}</div>
                  <div className="text-xs text-gray-500">{stat.label}</div>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* ── 3단계 사용 흐름 ── */}
      <section className="py-20 px-6 bg-white">
        <div className="max-w-4xl mx-auto">
          <h2 className="scroll-fade text-center text-2xl font-bold text-gray-900 mb-4">이렇게 사용합니다</h2>
          <p className="scroll-fade text-center text-sm text-gray-500 mb-14" data-delay="100">복잡한 설정 없이, 3단계면 끝납니다</p>

          <div className="flex items-start justify-center gap-4">
            {STEPS.map((step, i) => {
              const Icon = step.icon;
              return (
                <div key={step.title} className="flex items-center gap-4">
                  <div className="scroll-fade text-center w-[160px]" data-delay={i * 150}>
                    <div className={`w-16 h-16 bg-gradient-to-br ${step.color} text-white rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg shadow-indigo-100`}>
                      <Icon size={26} strokeWidth={1.8} />
                    </div>
                    <div className="text-[10px] text-gray-400 font-bold tracking-[0.2em] mb-1.5">STEP {i + 1}</div>
                    <div className="text-sm font-bold text-gray-900">{step.title}</div>
                    <div className="text-xs text-gray-500 mt-1">{step.desc}</div>
                  </div>
                  {i < STEPS.length - 1 && (
                    <div className="scroll-fade flex items-center mt-[-32px]" data-delay={i * 150 + 75}>
                      <div className="w-8 border-t border-dashed border-gray-300" />
                      <ArrowRight size={14} className="text-gray-300 -ml-0.5" />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── 기능 벤토 그리드 ── */}
      <section className="py-20 px-6 bg-gradient-to-b from-gray-50/50 to-white">
        <div className="max-w-4xl mx-auto">
          <h2 className="scroll-fade text-center text-2xl font-bold text-gray-900 mb-4">이런 것들을 할 수 있습니다</h2>
          <p className="scroll-fade text-center text-sm text-gray-500 mb-14" data-delay="100">양식 문서가 필요한 거의 모든 상황에 대응합니다</p>

          <div className="grid grid-cols-3 gap-3">
            {FEATURES.map((feat, i) => {
              const Icon = feat.icon;
              return (
                <Link
                  key={feat.label}
                  href="/tool"
                  className={`scroll-fade glass-card group relative rounded-2xl p-6 ${
                    feat.span || ""
                  } ${
                    feat.highlight
                      ? "bg-gradient-to-br from-indigo-50/80 to-violet-50/50 border-indigo-200/40"
                      : ""
                  }`}
                  data-delay={i * 80}
                >
                  {feat.highlight && (
                    <span className="absolute top-4 right-4 bg-gradient-to-r from-indigo-500 to-violet-500 text-white text-[9px] px-2.5 py-1 rounded-full font-bold shadow-sm">
                      추천
                    </span>
                  )}
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center mb-3 ${
                    feat.highlight
                      ? "bg-gradient-to-br from-indigo-500 to-violet-500 text-white"
                      : "bg-gray-100 text-gray-600 group-hover:bg-indigo-50 group-hover:text-indigo-600"
                  } transition-colors`}>
                    <Icon size={20} strokeWidth={1.8} />
                  </div>
                  <div className="text-sm font-bold text-gray-900 mb-1.5">{feat.label}</div>
                  <div className="text-xs text-gray-500 leading-relaxed">{feat.benefit}</div>
                </Link>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── 데이터 안내 ── */}
      <section className="py-16 px-6 bg-white">
        <div className="scroll-fade max-w-2xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 bg-gray-50 rounded-full px-4 py-2 mb-6">
            <Shield size={14} className="text-gray-500" />
            <span className="text-sm font-bold text-gray-900">내 데이터는 안전합니다</span>
          </div>
          <div className="space-y-3 text-sm text-gray-500 leading-relaxed">
            <p>양식 분석 · 문서 생성 · 추출 · 병합 — <strong className="text-gray-900">이 서버에서만 처리</strong>됩니다</p>
            <p>AI 자동 작성만 Google AI를 사용합니다 · 데이터는 <strong className="text-gray-900">학습에 사용되지 않으며</strong> 55일 후 삭제</p>
            <p>파일 <strong className="text-gray-900">3시간 후 자동 삭제</strong> · HTTPS 암호화 통신</p>
          </div>
        </div>
      </section>

      {/* ── 하단 CTA ── */}
      <section className="py-20 px-6 hero-mesh">
        <div className="scroll-fade max-w-xl mx-auto text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-3">준비되셨나요?</h2>
          <p className="text-sm text-gray-500 mb-8">양식 파일만 올리면 바로 시작할 수 있습니다</p>
          <Link
            href="/tool"
            className="cta-glow relative z-10 inline-flex items-center gap-2.5 bg-gradient-to-r from-indigo-600 to-violet-600 text-white px-9 py-4 rounded-2xl text-base font-semibold hover:shadow-lg hover:shadow-indigo-200 transition-all duration-300"
          >
            지금 시작하기
            <ArrowRight size={18} />
          </Link>
        </div>
      </section>

      {/* ── 푸터 ── */}
      <footer className="border-t border-gray-100 py-6 px-6 text-center">
        <span className="text-xs text-gray-400">Eazy HWPX</span>
      </footer>
    </div>
  );
}
