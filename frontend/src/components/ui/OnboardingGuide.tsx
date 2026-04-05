"use client";

import { useState, useEffect } from "react";
import { X, ChevronRight, Upload, Wand2, Download, Sparkles } from "lucide-react";

const STEPS = [
  {
    target: "upload-area",
    title: "1. 양식 올리기",
    desc: "완성하고 싶은 HWP/HWPX 파일을 여기에 올리세요.",
    icon: Upload,
    position: "right" as const,
  },
  {
    target: "analyze-btn",
    title: "2. 양식 분석",
    desc: "파일을 올린 뒤 이 버튼을 누르면 AI가 채울 항목을 찾습니다.",
    icon: Sparkles,
    position: "right" as const,
  },
  {
    target: "ai-input",
    title: "3. 내용 입력",
    desc: "\"사업계획서 써줘\"처럼 입력하면 AI가 자동 작성합니다. 엑셀/워드 파일을 올려도 됩니다.",
    icon: Wand2,
    position: "left" as const,
  },
  {
    target: "download-area",
    title: "4. 결과 다운로드",
    desc: "매핑 결과를 확인/수정한 뒤 문서를 만들어 다운받습니다.",
    icon: Download,
    position: "left" as const,
  },
];

const STORAGE_KEY = "eazyhwpx_onboarding_done";

export default function OnboardingGuide() {
  const [step, setStep] = useState(0);
  const [show, setShow] = useState(false);

  useEffect(() => {
    const done = localStorage.getItem(STORAGE_KEY);
    if (!done) {
      // 첫 방문: 1초 후 가이드 시작
      const timer = setTimeout(() => setShow(true), 1000);
      return () => clearTimeout(timer);
    }
  }, []);

  const finish = () => {
    setShow(false);
    localStorage.setItem(STORAGE_KEY, "true");
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

  return (
    <>
      {/* 배경 오버레이 */}
      <div className="fixed inset-0 bg-black/40 z-[9998]" onClick={finish} />

      {/* 가이드 카드 */}
      <div className="fixed z-[9999] inset-0 flex items-center justify-center pointer-events-none">
        <div className="pointer-events-auto bg-white rounded-2xl shadow-2xl border border-[#93C5FD] p-6 max-w-sm mx-4 animate-in fade-in slide-in-from-bottom-4 duration-300">
          {/* 닫기 */}
          <button onClick={finish} className="absolute top-3 right-3 text-gray-400 hover:text-gray-600">
            <X size={18} />
          </button>

          {/* 스텝 인디케이터 */}
          <div className="flex gap-1.5 mb-4">
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
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-xl bg-[#DBEAFE] flex items-center justify-center">
              <Icon size={20} className="text-[#1E40AF]" />
            </div>
            <h3 className="text-lg font-bold text-[#1a1c1b]">{current.title}</h3>
          </div>

          {/* 설명 */}
          <p className="text-sm text-[#57423c] leading-relaxed mb-5">{current.desc}</p>

          {/* 버튼 */}
          <div className="flex items-center justify-between">
            <button onClick={finish} className="text-xs text-gray-400 hover:text-gray-600">
              건너뛰기
            </button>
            <button
              onClick={next}
              className="flex items-center gap-1.5 bg-gradient-to-r from-[#2563EB] to-[#1E40AF] text-white px-5 py-2.5 rounded-xl text-sm font-bold hover:opacity-90 transition-opacity"
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
