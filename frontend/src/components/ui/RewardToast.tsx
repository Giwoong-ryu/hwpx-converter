"use client";

import { useEffect, useState } from "react";
import { Trophy, Flame, Star, Gift } from "lucide-react";

export interface RewardItem {
  type: "achievement" | "level_up" | "streak" | "lucky" | "share" | "referral";
  label: string;
  reward: number;
}

interface Props {
  rewards: RewardItem[];
  onDone: () => void;
}

const ICONS: Record<string, typeof Trophy> = {
  achievement: Trophy,
  level_up: Star,
  streak: Flame,
  lucky: Gift,
  share: Star,
  referral: Gift,
};

const COLORS: Record<string, string> = {
  achievement: "text-amber-500 bg-amber-50",
  level_up: "text-purple-500 bg-purple-50",
  streak: "text-orange-500 bg-orange-50",
  lucky: "text-emerald-500 bg-emerald-50",
  share: "text-blue-500 bg-blue-50",
  referral: "text-pink-500 bg-pink-50",
};

export default function RewardToast({ rewards, onDone }: Props) {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setVisible(false);
      setTimeout(onDone, 300);
    }, 4000);
    return () => clearTimeout(timer);
  }, [onDone]);

  if (rewards.length === 0) return null;

  return (
    <div className={`fixed top-4 right-4 z-[110] flex flex-col gap-2 transition-all duration-300 ${visible ? "opacity-100 translate-y-0" : "opacity-0 -translate-y-4"}`}>
      {rewards.map((r, i) => {
        const Icon = ICONS[r.type] || Gift;
        const color = COLORS[r.type] || "text-gray-500 bg-gray-50";
        return (
          <div key={i} className="bg-white border border-gray-200/80 rounded-xl shadow-lg px-4 py-3 flex items-center gap-3 min-w-[280px]"
            style={{ animationDelay: `${i * 150}ms` }}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${color}`}>
              <Icon size={16} />
            </div>
            <div className="flex-1">
              <p className="text-sm font-bold text-[#1a1c1b]">{r.label}</p>
              <p className="text-xs text-emerald-600 font-bold">+{r.reward}% 게이지</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
