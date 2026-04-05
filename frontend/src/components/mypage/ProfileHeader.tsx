"use client";

import { useAuth } from "@/context/AuthContext";
import { User, Zap, Flame } from "lucide-react";
import Link from "next/link";

function gaugeMessage(gauge: number, plan: string): string {
  if (plan === "free") return "매일 AI 기능을 무료로 사용할 수 있어요.";
  if (gauge >= 100) return "넉넉하게 남아있어요. 마음껏 사용하세요.";
  if (gauge >= 50) return "아직 여유가 있어요. 자유롭게 문서를 만들어보세요.";
  if (gauge >= 20) return "게이지가 절반 이하에요. 필요하면 충전해두세요.";
  if (gauge > 0) return "게이지가 얼마 남지 않았어요.";
  if (plan === "pro") return "이번 주 게이지를 모두 사용했어요. 월요일에 자동으로 리셋됩니다.";
  return "게이지를 모두 사용했어요. 충전하면 바로 다시 시작할 수 있어요.";
}

function streakMessage(streak: number): string {
  if (streak === 0) return "오늘 첫 문서를 만들면 연속 사용이 시작돼요.";
  if (streak < 3) return `${streak}일째 사용 중이에요. 3일 연속이면 +10% 보상!`;
  if (streak < 7) return `잘 하고 있어요! 7일까지 ${7 - streak}일 남았어요.`;
  if (streak < 14) return `대단해요! 14일 달성하면 +25% 보상.`;
  if (streak < 30) return `꾸준하시네요. 30일까지 ${30 - streak}일!`;
  return "30일 연속 달성! 진정한 DocFlow 달인이시네요.";
}

const PLAN_LABEL: Record<string, string> = { free: "Free", plus: "Plus", pro: "Pro" };

export default function ProfileHeader() {
  const { user } = useAuth();
  if (!user) return null;

  const plan = user.plan || "free";
  const gauge = user.gauge_pct || 0;
  const streak = user.streak_days || 0;
  const level = user.level || 1;
  const levelTitle = user.level_title || "복붙 탈출";
  const totalDocs = user.total_docs || 0;

  const barColor = gauge > 100 ? "bg-emerald-500" : gauge > 30 ? "bg-[#2563EB]" : gauge > 10 ? "bg-amber-500" : "bg-red-500";
  const barWidth = Math.min(gauge, 100);

  const nextStreakReward = streak < 3 ? { days: 3, reward: 10 } : streak < 7 ? { days: 7, reward: 25 } : streak < 14 ? { days: 14, reward: 25 } : streak < 30 ? { days: 30, reward: 50 } : null;

  return (
    <div className="bg-white rounded-2xl border border-gray-200/80 p-6 shadow-[0_4px_20px_rgba(26,28,27,0.03)]">
      {/* 사용자 정보 */}
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 rounded-full bg-[#DBEAFE] flex items-center justify-center">
          <User size={20} className="text-[#1E40AF]" />
        </div>
        <div>
          <p className="font-bold text-[#1a1c1b]">{user.email}</p>
          <p className="text-base text-[#57423c]">
            {level}단계 {levelTitle}
            <span className="mx-1.5 text-[#57423c]/30">·</span>
            {plan === "free" ? (
              <span className="text-[#57423c]/60">Free 플랜</span>
            ) : plan === "pro" ? (
              <span className="font-bold text-white bg-[#1E40AF] px-1.5 py-0.5 rounded text-xs">PRO</span>
            ) : (
              <span className="font-bold text-[#2563EB] bg-[#DBEAFE] px-1.5 py-0.5 rounded text-xs">PLUS</span>
            )}
            <span className="mx-1.5 text-[#57423c]/30">·</span>
            문서 {totalDocs}건 완성
          </p>
        </div>
      </div>

      {/* 게이지 바 (유료만) */}
      {plan !== "free" && (
        <div className="mb-4">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-xs font-semibold text-[#57423c]">사용량 게이지</span>
            <span className="text-sm font-bold text-[#1a1c1b] tabular-nums">{Math.round(gauge)}%</span>
          </div>
          <div className="w-full h-2.5 bg-gray-100 rounded-full overflow-hidden">
            <div className={`h-full rounded-full transition-all duration-700 ${barColor}`} style={{ width: `${barWidth}%` }} />
          </div>
          <p className="text-sm text-[#57423c]/70 mt-1.5">{gaugeMessage(gauge, plan)}</p>
        </div>
      )}

      {/* Free 플랜 안내 */}
      {plan === "free" && (
        <div className="mb-4 bg-[#f4f4f1] rounded-xl p-3">
          <p className="text-base text-[#57423c]">{gaugeMessage(gauge, plan)}</p>
          <Link href="/pricing" className="text-sm text-[#2563EB] font-semibold mt-1 inline-block hover:underline">
            Plus로 업그레이드하면 AI를 더 많이 사용할 수 있어요 →
          </Link>
        </div>
      )}

      {/* 스트릭 */}
      <div className="flex items-center gap-2 text-base">
        <Flame size={16} className={streak >= 3 ? "text-orange-500" : "text-[#57423c]/30"} />
        <span className="text-[#57423c]">{streakMessage(streak)}</span>
        {nextStreakReward && streak > 0 && (
          <span className="text-xs text-[#57423c]/40 ml-auto">
            다음 보상: {nextStreakReward.days}일 (+{nextStreakReward.reward}%)
          </span>
        )}
      </div>
    </div>
  );
}
