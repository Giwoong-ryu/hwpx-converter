"use client";

import { useState, useEffect, useCallback } from "react";
import { X, ChevronRight, Upload, Wand2, Download, Sparkles } from "lucide-react";

const STEPS = [
  {
    target: "onboard-upload",
    title: "1. 양식 올리기",
    desc: "완성하고 싶은 HWP/HWPX 파일을 여기에 드래그하거나 클릭해서 올리세요.",
    icon: Upload,
    align: "right",
  },
  {
    target: "onboard-analyze",
    title: "2. 양식 분석",
    desc: "파일을 올린 뒤 이 버튼을 누르면 AI가 채울 항목을 자동으로 찾습니다.",
    icon: Sparkles,
    align: "right",
  },
  {
    target: "onboard-tabs",
    title: "3. 기능 선택",
    desc: "AI 자동 채우기, 엑셀 변환, 도장 삽입 등 원하는 기능을 선택하세요.",
    icon: Wand2,
    align: "bottom",
  },
];

const STORAGE_KEY = "eazyhwpx_onboarding_done";
const LAST_VISIT_KEY = "eazyhwpx_last_visit";
const NEVER_SHOW_KEY = "eazyhwpx_onboarding_never";
const REVISIT_DAYS = 30;
const PADDING = 8;

export default function OnboardingGuide({ forceShow, onClose }: { forceShow?: boolean; onClose?: () => void } = {}) {
  const [step, setStep] = useState(0);
  const [show, setShow] = useState(false);
  const [rect, setRect] = useState<DOMRect | null>(null);

  useEffect(() => {
    // "다시 보지 않기" 설정 시 forceShow도 무시
    if (localStorage.getItem(NEVER_SHOW_KEY) === "true" && !forceShow) return;

    if (forceShow) {
      setStep(0);
      setShow(true);
      return;
    }

    const done = localStorage.getItem(STORAGE_KEY);
    const lastVisit = localStorage.getItem(LAST_VISIT_KEY);
    const now = Date.now();

    localStorage.setItem(LAST_VISIT_KEY, String(now));

    if (!done) {
      const timer = setTimeout(() => setShow(true), 800);
      return () => clearTimeout(timer);
    }

    if (lastVisit) {
      const daysSince = (now - Number(lastVisit)) / (1000 * 60 * 60 * 24);
      if (daysSince >= REVISIT_DAYS) {
        const timer = setTimeout(() => setShow(true), 800);
        return () => clearTimeout(timer);
      }
    }
  }, [forceShow]);

  const updateRect = useCallback(() => {
    if (!show) return;
    const el = document.getElementById(STEPS[step]?.target);
    if (el) {
      setRect(el.getBoundingClientRect());
      el.scrollIntoView({ behavior: "smooth", block: "center" });
    } else {
      setRect(null);
    }
  }, [step, show]);

  useEffect(() => {
    updateRect();
    window.addEventListener("resize", updateRect);
    return () => window.removeEventListener("resize", updateRect);
  }, [updateRect]);

  const finish = (never = false) => {
    setShow(false);
    localStorage.setItem(STORAGE_KEY, "true");
    localStorage.setItem(LAST_VISIT_KEY, String(Date.now()));
    if (never) localStorage.setItem(NEVER_SHOW_KEY, "true");
    onClose?.();
  };

  const next = () => {
    if (step < STEPS.length - 1) {
      setStep(step + 1);
    } else {
      finish();
    }
  };

  if (!show) return null;

  const current = STEPS[step];
  const Icon = current.icon;

  // 스포트라이트 위치 (타겟 주변에 구멍 뚫기)
  const spotlight = rect
    ? {
        top: rect.top - PADDING,
        left: rect.left - PADDING,
        width: rect.width + PADDING * 2,
        height: rect.height + PADDING * 2,
      }
    : null;

  // 가이드 카드 위치 계산
  const getCardStyle = (): React.CSSProperties => {
    if (!rect) return { top: "50%", left: "50%", transform: "translate(-50%, -50%)" };

    const cardW = 320;
    const cardH = 200;
    const gap = 16;

    if (current.align === "right") {
      const left = rect.right + gap + PADDING;
      const top = rect.top + rect.height / 2 - cardH / 2;
      // 화면 밖으로 나가면 아래로
      if (left + cardW > window.innerWidth) {
        return { top: rect.bottom + gap + PADDING, left: Math.max(16, rect.left - 40) };
      }
      return { top: Math.max(16, top), left };
    }
    if (current.align === "bottom") {
      return { top: rect.bottom + gap + PADDING, left: Math.max(16, rect.left) };
    }
    // left
    const left = rect.left - cardW - gap - PADDING;
    return { top: Math.max(16, rect.top), left: Math.max(16, left) };
  };

  return (
    <>
      {/* SVG 오버레이 - 스포트라이트 구멍 */}
      <svg
        className="fixed inset-0 z-[9998] pointer-events-none"
        width="100%" height="100%"
        style={{ pointerEvents: "auto" }}
        onClick={() => finish(false)}
      >
        <defs>
          <mask id="spotlight-mask">
            <rect width="100%" height="100%" fill="white" />
            {spotlight && (
              <rect
                x={spotlight.left}
                y={spotlight.top}
                width={spotlight.width}
                height={spotlight.height}
                rx={12}
                fill="black"
              />
            )}
          </mask>
        </defs>
        <rect
          width="100%" height="100%"
          fill="rgba(0,0,0,0.5)"
          mask="url(#spotlight-mask)"
        />
      </svg>

      {/* 스포트라이트 테두리 (구멍 주변 강조) */}
      {spotlight && (
        <div
          className="fixed z-[9998] rounded-xl border-2 border-[#2563EB] pointer-events-none"
          style={{
            top: spotlight.top,
            left: spotlight.left,
            width: spotlight.width,
            height: spotlight.height,
            boxShadow: "0 0 0 4px rgba(37, 99, 235, 0.2)",
            transition: "all 0.3s ease",
          }}
        />
      )}

      {/* 가이드 카드 */}
      <div
        className="fixed z-[9999] bg-white rounded-2xl shadow-2xl border border-[#93C5FD] p-5 w-[320px]"
        style={{ ...getCardStyle(), transition: "all 0.3s ease" }}
      >
        {/* 스텝 인디케이터 */}
        <div className="flex gap-1.5 mb-3">
          {STEPS.map((_, i) => (
            <div
              key={i}
              className={`h-1 rounded-full flex-1 transition-colors ${
                i <= step ? "bg-[#2563EB]" : "bg-gray-200"
              }`}
            />
          ))}
        </div>

        {/* 아이콘 + 제목 */}
        <div className="flex items-center gap-2.5 mb-2">
          <div className="w-9 h-9 rounded-xl bg-[#DBEAFE] flex items-center justify-center shrink-0">
            <Icon size={18} className="text-[#1E40AF]" />
          </div>
          <h3 className="text-base font-bold text-[#1a1c1b]">{current.title}</h3>
        </div>

        {/* 설명 */}
        <p className="text-sm text-[#57423c] leading-relaxed mb-4">{current.desc}</p>

        {/* 버튼 */}
        <div className="space-y-2.5">
          {/* 마지막 스텝: 다시 보지 않기 체크박스 */}
          {step === STEPS.length - 1 && (
            <label className="flex items-center gap-2 cursor-pointer select-none">
              <input
                type="checkbox"
                onChange={(e) => {
                  if (e.target.checked) localStorage.setItem(NEVER_SHOW_KEY, "true");
                  else localStorage.removeItem(NEVER_SHOW_KEY);
                }}
                defaultChecked={localStorage.getItem(NEVER_SHOW_KEY) === "true"}
                className="rounded accent-[#2563EB] w-3.5 h-3.5"
              />
              <span className="text-xs text-gray-400">다시 보지 않기</span>
            </label>
          )}
          <div className="flex items-center justify-between">
            <button onClick={() => finish(false)} className="text-xs text-gray-400 hover:text-gray-600">
              건너뛰기
            </button>
            <button
              onClick={next}
              className="flex items-center gap-1.5 bg-linear-to-r from-[#2563EB] to-[#1E40AF] text-white px-4 py-2 rounded-xl text-sm font-bold hover:opacity-90 transition-opacity"
            >
              {step < STEPS.length - 1 ? (
                <>다음 <ChevronRight size={14} /></>
              ) : (
                "시작하기"
              )}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
