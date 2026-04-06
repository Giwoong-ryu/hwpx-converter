"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  ArrowRight, FileText, Shield, ChevronDown,
  FileSpreadsheet, Layers, Upload, Wand2,
  ArrowRightLeft, Stamp, Merge, TableProperties,
  Calendar, Check
} from "lucide-react";

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

/* ═══ 인기 양식 ═══ */

function PopularForms() {
  const [forms, setForms] = useState<{ id: number; title: string; category: string; likes: number; downloads: number; field_count: number }[]>([]);

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL || "/api"}/gallery/list?sort=popular&size=6`)
      .then((r) => r.json())
      .then((d) => setForms(d.forms || []))
      .catch(() => {});
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

  return (
    <div ref={scrollRef} className="min-h-screen bg-[#f9f9f6] text-[#1a1c1b] overflow-hidden">

      {/* ── 네비게이션 ── */}
      <nav className="fixed top-0 w-full z-50 bg-[#f9f9f6]/80 backdrop-blur-xl border-b border-[#BFDBFE]/40">
        <div className="flex justify-between items-center px-8 lg:px-16 py-4 max-w-screen-2xl mx-auto">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-[#1a1c1b] flex items-center justify-center">
              <FileText size={14} className="text-white" strokeWidth={2.2} />
            </div>
            <span className="text-lg font-extrabold tracking-tighter">Eazy HWPX</span>
          </Link>
          <div className="flex items-center gap-6">
            <Link href="/pricing" className="text-sm text-[#57423c]/70 hover:text-[#1a1c1b] transition-colors">요금제</Link>
            <Link href="/tool" className="bg-gradient-to-r from-[#2563EB] to-[#1E40AF] text-white px-5 py-2 rounded-lg font-semibold text-sm hover:opacity-90 transition-all active:scale-95">
              무료로 시작하기
            </Link>
          </div>
        </div>
      </nav>

      {/* ══════════════════════════════════════════
          섹션 1: 히어로 — 공감 + 가치 + 매핑 플로우
      ══════════════════════════════════════════ */}
      <section className="pt-28 pb-16 lg:pb-20">
        <div className="max-w-screen-xl mx-auto px-8 lg:px-16 grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">

          {/* 왼쪽: 카피 */}
          <div>
            {/* 지원 형식 배지 */}
            <div className="flex items-center gap-2 mb-6 flex-wrap">
              {["HWP", "HWPX", "DOCX", "엑셀", "워드", "TXT"].map((fmt) => (
                <span key={fmt} className="text-xs font-bold text-[#1E40AF] bg-[#DBEAFE]/50 px-2.5 py-1 rounded-md">{fmt}</span>
              ))}
            </div>

            <h1 className="text-[2.2rem] lg:text-[2.8rem] font-extrabold leading-[1.15] tracking-tight mb-5">
              또 양식에 하나하나<br />
              <span className="text-[#1E40AF]">복사 붙여넣기</span> 하실 건가요?
            </h1>

            <p className="text-lg text-[#57423c] leading-relaxed max-w-lg mb-8">
              내 자료만 올리면<br />
              양식에 맞춰 <strong className="text-[#1a1c1b]">AI가 넣어드립니다.</strong><br />
              <span className="text-[#57423c]/70">엑셀, 워드, 텍스트 — 어떤 자료든.</span>
            </p>

            <div className="flex flex-wrap items-center gap-4 mb-6">
              <Link
                href="/tool"
                className="bg-gradient-to-r from-[#2563EB] to-[#1E40AF] text-white px-8 py-3.5 rounded-xl text-base font-bold shadow-lg shadow-[#1E40AF]/20 hover:shadow-xl transition-all active:scale-95 flex items-center gap-2"
              >
                무료로 시작하기 <ArrowRight size={17} />
              </Link>
              <span className="text-sm text-[#57423c]/50">회원가입 없이 바로 사용</span>
            </div>

            <div className="flex items-center gap-6 text-sm text-[#57423c]/60">
              <span><strong className="text-[#1a1c1b]">7가지</strong> 자동화 도구</span>
              <span className="text-[#BFDBFE]">|</span>
              <span>평균 <strong className="text-[#1a1c1b]">3분</strong> 완성</span>
              <span className="text-[#BFDBFE]">|</span>
              <span><strong className="text-[#1a1c1b]">무료</strong> 사용</span>
            </div>
          </div>

          {/* 오른쪽: 매핑 플로우 시각화 */}
          <div className="hidden lg:block">
            <div className="relative flex items-center justify-center gap-6">

              {/* 내 자료 */}
              <div className="flex flex-col gap-3 items-center">
                <span className="text-xs font-bold text-[#57423c]/50 mb-1">내 자료</span>
                <div className="space-y-2.5">
                  {[
                    { icon: FileSpreadsheet, label: "엑셀", color: "text-emerald-600 bg-emerald-50 border-emerald-200" },
                    { icon: FileText, label: "워드", color: "text-blue-600 bg-blue-50 border-blue-200" },
                    { icon: FileText, label: "텍스트", color: "text-gray-600 bg-gray-50 border-gray-200" },
                  ].map(({ icon: Icon, label, color }) => (
                    <div key={label} className={`flex items-center gap-2.5 px-4 py-2.5 rounded-xl border ${color} shadow-sm`}>
                      <Icon size={16} />
                      <span className="text-sm font-semibold">{label}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* AI 매핑 화살표 */}
              <div className="flex flex-col items-center gap-2 px-4">
                <div className="w-10 h-10 rounded-full bg-[#2563EB] flex items-center justify-center shadow-lg shadow-[#2563EB]/30">
                  <Wand2 size={18} className="text-white" />
                </div>
                <span className="text-xs font-bold text-[#2563EB]">AI 매핑</span>
                <svg width="60" height="24" className="text-[#2563EB]/40">
                  <line x1="0" y1="12" x2="48" y2="12" stroke="currentColor" strokeWidth="2" strokeDasharray="4 4" />
                  <polygon points="48,6 60,12 48,18" fill="currentColor" />
                </svg>
              </div>

              {/* 완성된 양식 */}
              <div className="flex flex-col items-center">
                <span className="text-xs font-bold text-[#57423c]/50 mb-1">완성된 문서</span>
                <div className="w-[200px] bg-white rounded-2xl border border-gray-200 shadow-xl p-4">
                  <div className="text-center font-bold text-sm text-[#1a1c1b] mb-3 pb-2 border-b border-gray-100">사업계획서</div>
                  <div className="space-y-2">
                    {[
                      { label: "기업명", value: "주식회사 이지테크" },
                      { label: "대표자", value: "홍길동" },
                      { label: "설립일", value: "2024. 01. 15" },
                      { label: "업종", value: "소프트웨어 개발" },
                    ].map(({ label, value }) => (
                      <div key={label} className="flex text-xs">
                        <span className="w-14 text-[#57423c]/50 shrink-0">{label}</span>
                        <span className="text-[#1a1c1b] font-medium">{value}</span>
                      </div>
                    ))}
                  </div>
                  <div className="mt-3 pt-2 border-t border-gray-100 flex items-center gap-1.5">
                    <Check size={12} className="text-emerald-500" />
                    <span className="text-xs text-emerald-600 font-semibold">자동 완성</span>
                  </div>
                </div>
              </div>

            </div>
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════════
          섹션 2: 이렇게 동작합니다 — 3단계
      ══════════════════════════════════════════ */}
      <section className="py-20 bg-white border-y border-gray-100">
        <div className="max-w-screen-xl mx-auto px-8 lg:px-16">
          <h2 className="scroll-fade text-2xl font-extrabold tracking-tight text-center mb-3">이렇게 동작합니다</h2>
          <p className="scroll-fade text-sm text-[#57423c]/50 text-center mb-12" data-delay="100">양식 + 내 자료, 두 개만 올리면 끝이에요.</p>

          <div className="grid md:grid-cols-3 gap-8 max-w-3xl mx-auto">
            {[
              {
                step: "1",
                icon: Upload,
                title: "양식 올리기",
                desc: "사업계획서, 견적서, 이력서 등\nHWP, HWPX, DOCX 양식 파일",
              },
              {
                step: "2",
                icon: FileSpreadsheet,
                title: "내 자료 올리기",
                desc: "엑셀, 워드, 텍스트\n— 어떤 형식이든",
              },
              {
                step: "3",
                icon: Check,
                title: "완성!",
                desc: "AI가 양식에 맞춰 넣어드려요.\nHWP · HWPX · DOCX · 엑셀\n원하는 형식으로 다운로드",
              },
            ].map(({ step, icon: Icon, title, desc }, i) => (
              <div key={step} className="scroll-fade text-center" data-delay={i * 120}>
                <div className={`w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-4 ${
                  step === "3"
                    ? "bg-gradient-to-br from-[#2563EB] to-[#1E40AF] text-white shadow-lg shadow-[#2563EB]/20"
                    : "bg-[#DBEAFE] text-[#1E40AF]"
                }`}>
                  <Icon size={24} />
                </div>
                <div className="text-xs font-bold text-[#2563EB] mb-2">STEP {step}</div>
                <h3 className="text-lg font-bold text-[#1a1c1b] mb-2">{title}</h3>
                <p className="text-sm text-[#57423c]/60 leading-relaxed whitespace-pre-line">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════════
          섹션 3: 이런 것도 됩니다 — 부가 기능
      ══════════════════════════════════════════ */}
      <section className="py-20">
        <div className="max-w-screen-xl mx-auto px-8 lg:px-16">
          <h2 className="scroll-fade text-2xl font-extrabold tracking-tight text-center mb-3">이런 것도 됩니다</h2>
          <p className="scroll-fade text-sm text-[#57423c]/50 text-center mb-12" data-delay="100">양식 채우기 외에도 문서 작업을 자동화해요.</p>

          {/* 메인 2개 */}
          <div className="grid md:grid-cols-2 gap-6 max-w-3xl mx-auto mb-8">
            <div className="scroll-fade bg-white rounded-2xl border border-gray-200/80 p-6 hover:border-[#93C5FD] transition-colors" data-delay="0">
              <ArrowRightLeft size={22} className="text-[#2563EB] mb-3" />
              <h3 className="font-bold text-[#1a1c1b] mb-1">엑셀 ↔ 문서 쌍방향</h3>
              <p className="text-sm text-[#57423c]/60 leading-relaxed">엑셀 데이터를 문서로, 문서 내용을 엑셀로. 양방향 변환이 자유로워요.</p>
            </div>
            <div className="scroll-fade bg-white rounded-2xl border border-gray-200/80 p-6 hover:border-[#93C5FD] transition-colors" data-delay="100">
              <Layers size={22} className="text-[#2563EB] mb-3" />
              <h3 className="font-bold text-[#1a1c1b] mb-1">대량 생성</h3>
              <p className="text-sm text-[#57423c]/60 leading-relaxed">엑셀에 100명 데이터가 있으면, 양식 하나로 문서 100개를 한번에 만들어요.</p>
            </div>
          </div>

          {/* 보조 기능 태그 */}
          <div className="scroll-fade flex flex-wrap justify-center gap-3 mb-10" data-delay="200">
            {[
              { icon: FileText, label: "HWP/HWPX/DOCX 변환 무료" },
              { icon: Merge, label: "다량 문서 합치기" },
              { icon: Stamp, label: "자동 도장 날인" },
              { icon: TableProperties, label: "문서→엑셀 추출" },
              { icon: Calendar, label: "매월 반복 문서" },
            ].map(({ icon: Icon, label }) => (
              <span key={label} className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-full bg-white border border-gray-200/80 text-sm text-[#57423c]/70">
                <Icon size={14} className="text-[#2563EB]/60" /> {label}
              </span>
            ))}
          </div>

          {/* AI 초안 작성 (보조 기능) */}
          <div className="scroll-fade max-w-2xl mx-auto" data-delay="300">
            <div className="bg-[#FAFBFF] rounded-2xl border border-[#93C5FD]/30 p-6">
              <div className="flex items-center gap-2 mb-2">
                <Wand2 size={18} className="text-[#2563EB]" />
                <h3 className="font-bold text-[#1a1c1b]">AI 초안 작성</h3>
              </div>
              <p className="text-sm text-[#57423c]/60 leading-relaxed">
                자료가 없어도 괜찮아요. 양식에 맞는 <strong className="text-[#1a1c1b]">핵심 질문을 안내</strong>해드립니다.<br />
                답변하면 초안이 채워져요. 중요 문서는 반드시 본인이 검토하세요.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════════
          섹션 3.5: 인기 양식 갤러리
      ══════════════════════════════════════════ */}
      <section className="py-16 bg-white border-y border-gray-100">
        <div className="max-w-screen-xl mx-auto px-8 lg:px-16">
          <h2 className="scroll-fade text-2xl font-extrabold tracking-tight text-center mb-2">다른 사람들이 쓰는 양식</h2>
          <p className="scroll-fade text-sm text-[#57423c]/50 text-center mb-10" data-delay="100">양식 구하러 돌아다닐 필요 없이, 여기서 선택하면 바로 사용할 수 있어요.</p>
          <PopularForms />
          <div className="text-center mt-8">
            <Link href="/gallery" className="inline-flex items-center gap-1 text-sm text-[#2563EB] font-semibold hover:underline">
              양식 더 보기 <ArrowRight size={14} />
            </Link>
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════════
          섹션 4: FAQ + 최종 CTA
      ══════════════════════════════════════════ */}
      <section className="py-20">
        <div className="max-w-2xl mx-auto px-8 lg:px-16">
          <h2 className="scroll-fade text-2xl font-extrabold tracking-tight text-center mb-8">자주 묻는 질문</h2>
          <div className="space-y-3 mb-16">
            <FAQ q="한글 프로그램이 없어도 되나요?" a="네. 브라우저만 있으면 됩니다. Mac, 태블릿, 스마트폰에서도 사용할 수 있어요." />
            <FAQ q="내 자료가 서버에 남나요?" a="파일은 처리 후 30분 안에 자동 삭제돼요. 서버에 보관하지 않습니다." />
            <FAQ q="어떤 파일 형식을 지원하나요?" a="양식: HWP, HWPX, DOCX. 자료: 엑셀, 워드, 텍스트, CSV, JSON. 출력: HWP, HWPX, DOCX, 엑셀." />
            <FAQ q="유료인가요?" a="문서 변환, 추출, 합치기는 무료예요. AI 매핑은 하루 3회 무료, 그 이상은 Plus(4,900원, 기간 만료 없음)부터 사용할 수 있어요." />
            <FAQ q="AI 초안 작성은 정확한가요?" a="양식에 맞는 핵심 질문을 안내하고, 답변을 바탕으로 초안을 만들어드려요. 정부지원 서류 같은 중요 문서는 반드시 본인이 검토하세요." />
          </div>

          {/* 최종 CTA */}
          <div className="scroll-fade text-center">
            <h2 className="text-2xl font-extrabold tracking-tight mb-3">양식 문서, 이제 직접 쓰지 마세요</h2>
            <p className="text-sm text-[#57423c]/50 mb-6">내 자료만 올리면 AI가 알아서 넣어드립니다.</p>
            <Link
              href="/tool"
              className="inline-flex items-center gap-2 bg-gradient-to-r from-[#2563EB] to-[#1E40AF] text-white px-8 py-3.5 rounded-xl text-base font-bold shadow-lg shadow-[#1E40AF]/20 hover:shadow-xl transition-all active:scale-95"
            >
              무료로 시작하기 <ArrowRight size={17} />
            </Link>
          </div>
        </div>
      </section>

      {/* ── 신뢰 바 + 푸터 ── */}
      <footer className="border-t border-gray-200/60 py-6">
        <div className="max-w-screen-xl mx-auto px-8 lg:px-16 flex flex-col sm:flex-row items-center justify-center gap-4 sm:gap-8 text-sm text-[#57423c]/40">
          <span className="flex items-center gap-1.5"><Shield size={12} /> HTTPS 암호화</span>
          <span className="flex items-center gap-1.5"><Shield size={12} /> 파일 30분 후 삭제</span>
          <span className="flex items-center gap-1.5"><Shield size={12} /> 광고 없음</span>
          <span>Eazy HWPX</span>
        </div>
      </footer>

      {/* ── 글로벌 스타일 ── */}
      <style jsx global>{`
        .scroll-fade {
          opacity: 0;
          transform: translateY(24px);
          transition: opacity 0.6s ease, transform 0.6s ease;
        }
        .scroll-fade.visible {
          opacity: 1;
          transform: translateY(0);
        }
      `}</style>
    </div>
  );
}

/* ═══ FAQ 컴포넌트 ═══ */

function FAQ({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="scroll-fade bg-white rounded-xl border border-gray-200/80 overflow-hidden">
      <button onClick={() => setOpen(!open)} className="w-full p-5 flex items-center justify-between text-left">
        <span className="font-bold text-sm text-[#1a1c1b]">{q}</span>
        <ChevronDown size={16} className={`text-[#57423c]/30 transition-transform shrink-0 ml-4 ${open ? "rotate-180" : ""}`} />
      </button>
      {open && <p className="px-5 pb-5 text-sm text-[#57423c]/60 leading-relaxed -mt-1">{a}</p>}
    </div>
  );
}
