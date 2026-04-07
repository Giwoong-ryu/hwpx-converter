"use client";

import { useAuth } from "@/context/AuthContext";
import { CreditCard, ArrowRight } from "lucide-react";
import Link from "next/link";

const PLAN_FEATURES: Record<string, { label: string; features: string[] }> = {
  free: {
    label: "Free",
    features: ["AI 매핑 10회/일 무료", "AI 작성 3회/일 무료", "변환/추출/병합 무제한", "내 정보 저장 1개"],
  },
  plus: {
    label: "Plus",
    features: ["AI 게이지 기반 사용", "대량 생성 30건", "프리셋 3개", "매핑 저장 10개"],
  },
  pro: {
    label: "Pro",
    features: ["AI 무제한 (매주 리셋)", "대량 생성 200건", "프리셋/매핑 무제한", "스트릭 프리즈 주 2회"],
  },
};

export default function PlanInfo() {
  const { user } = useAuth();
  if (!user) return null;

  const plan = user.plan || "free";
  const info = PLAN_FEATURES[plan] || PLAN_FEATURES.free;
  const gauge = user.gauge_pct || 0;

  return (
    <div className="bg-white rounded-2xl border border-gray-200/80 p-6 shadow-[0_4px_20px_rgba(26,28,27,0.03)]">
      <div className="flex items-center gap-2 mb-4">
        <CreditCard size={18} className="text-[#2563EB]" />
        <h3 className="font-bold text-[#1a1c1b]">현재 요금제: {info.label}</h3>
      </div>

      <ul className="space-y-1.5 mb-4">
        {info.features.map((f, i) => (
          <li key={i} className="text-sm text-[#57423c] flex items-center gap-2">
            <span className="w-1 h-1 bg-[#2563EB] rounded-full shrink-0" />
            {f}
          </li>
        ))}
        {plan !== "free" && (
          <li className="text-sm text-[#57423c] flex items-center gap-2">
            <span className="w-1 h-1 bg-[#2563EB] rounded-full shrink-0" />
            현재 게이지: <span className="font-bold text-[#1a1c1b]">{Math.round(gauge)}%</span>
          </li>
        )}
      </ul>

      {/* 업그레이드 유도 (자연스럽게) */}
      {plan === "free" && (
        <Link href="/pricing" className="block bg-linear-to-r from-[#2563EB] to-[#1E40AF] text-white rounded-xl px-4 py-3 text-center hover:opacity-90 transition-all active:scale-[0.98]">
          <p className="text-sm font-semibold mb-0.5">자주 쓰는 정보·양식을 저장해두면 매번 다시 입력하지 않아도 돼요</p>
          <p className="text-xs opacity-80">4,900원 · 첫 구매 2배 충전 · 기간 만료 없음</p>
        </Link>
      )}
      {plan === "plus" && (
        <Link href="/pricing" className="block border border-[#93C5FD]/50 rounded-xl px-4 py-3 hover:border-[#2563EB]/50 transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold text-[#1a1c1b]">Pro를 사용하면 매주 게이지가 자동 리셋돼요</p>
              <p className="text-xs text-[#57423c]/60">횟수 걱정 없이 사용할 수 있어요</p>
            </div>
            <ArrowRight size={16} className="text-[#2563EB] shrink-0" />
          </div>
        </Link>
      )}
      {plan === "pro" && (
        <Link href="/pricing" className="text-xs text-[#57423c]/40 hover:text-[#2563EB] transition-colors">
          요금제 자세히 보기 →
        </Link>
      )}
    </div>
  );
}
