"use client";

import Link from "next/link";
import { Zap, X } from "lucide-react";

interface Props {
  onClose: () => void;
  errorCode: string;
  plan: string;
  gaugePct: number;
}

export default function GaugeEmptyModal({ onClose, errorCode, plan, gaugePct }: Props) {
  const isLoginRequired = errorCode === "LOGIN_REQUIRED";

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-[100] flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-[#f9f9f6] rounded-2xl p-8 w-full max-w-sm border border-gray-200/80" onClick={(e) => e.stopPropagation()}>
        <button onClick={onClose} className="absolute top-4 right-4 text-gray-400 hover:text-gray-600">
          <X size={18} />
        </button>

        <div className="text-center">
          <div className="w-12 h-12 bg-amber-50 rounded-full flex items-center justify-center mx-auto mb-4">
            <Zap size={24} className="text-amber-500" />
          </div>

          {isLoginRequired ? (
            <>
              <h3 className="text-lg font-extrabold text-[#1a1c1b] mb-2">
                AI 채우기, 무료로 시작하세요
              </h3>
              <p className="text-sm text-[#57423c]/60 mb-6">
                가입하면 하루 10회 AI 자동 채우기를 무료로 사용할 수 있어요.
                <br />가입은 10초면 끝나요.
              </p>
            </>
          ) : plan === "free" ? (
            <>
              <h3 className="text-lg font-extrabold text-[#1a1c1b] mb-2">
                오늘의 무료 사용량을 다 쓰셨어요
              </h3>
              <p className="text-sm text-[#57423c]/60 mb-6">
                자정에 자동으로 10회 다시 충전됩니다.
                <br />저장·자동화가 필요하다면 Plus로 업그레이드하세요.
              </p>
            </>
          ) : (
            <>
              <h3 className="text-lg font-extrabold text-[#1a1c1b] mb-2">
                게이지가 부족합니다
              </h3>
              <p className="text-sm text-[#57423c]/60 mb-2">
                현재 게이지: <span className="font-bold text-red-500">{Math.round(gaugePct)}%</span>
              </p>
              <p className="text-sm text-[#57423c]/60 mb-6">
                게이지를 충전하면 계속 사용할 수 있습니다.
              </p>
            </>
          )}

          <Link href="/pricing" onClick={onClose}
            className="block w-full py-3 rounded-xl bg-gradient-to-r from-[#2563EB] to-[#1E40AF] text-white font-bold text-sm hover:opacity-90 transition-all text-center">
            {isLoginRequired ? "무료로 가입하기" : "게이지 충전하기"}
          </Link>

          <button onClick={onClose} className="mt-3 text-xs text-[#57423c]/40 hover:text-[#57423c]/60">
            나중에
          </button>
        </div>
      </div>
    </div>
  );
}
