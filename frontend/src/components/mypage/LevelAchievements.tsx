"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import { listAchievements } from "@/lib/api";
import { Trophy, CheckCircle2, Circle, Award } from "lucide-react";

const LEVELS = [
  { level: 1, title: "복붙 탈출", docs: 0, medal: "참가", color: "text-gray-400", bg: "bg-gray-100", ring: "ring-gray-300" },
  { level: 2, title: "자동화 입문", docs: 5, medal: "동메달", color: "text-amber-700", bg: "bg-amber-50", ring: "ring-amber-300" },
  { level: 3, title: "칼퇴 요정", docs: 20, medal: "은메달", color: "text-slate-400", bg: "bg-slate-50", ring: "ring-slate-300" },
  { level: 4, title: "팀 에이스", docs: 50, medal: "금메달", color: "text-yellow-500", bg: "bg-yellow-50", ring: "ring-yellow-300" },
  { level: 5, title: "자동화의 신", docs: 100, medal: "트로피", color: "text-amber-500", bg: "bg-amber-50", ring: "ring-amber-400" },
];

interface AchDef { label: string; reward: number; condition?: string }
interface AchRecord { achievement_key: string; gauge_reward: number; created_at: string }

export default function LevelAchievements() {
  const { user } = useAuth();
  const [achieved, setAchieved] = useState<AchRecord[]>([]);
  const [defs, setDefs] = useState<Record<string, AchDef>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    listAchievements().then((data) => {
      setAchieved(data.achievements || []);
      setDefs(data.definitions || {});
      setLoading(false);
    });
  }, [user]);

  if (!user || loading) return null;

  const level = user.level || 1;
  const totalDocs = user.total_docs || 0;
  const nextLevel = LEVELS.find((l) => l.level > level);
  const docsToNext = nextLevel ? nextLevel.docs - totalDocs : 0;

  const achievedKeys = new Set(achieved.map((a) => a.achievement_key));
  const achievedMap = Object.fromEntries(achieved.map((a) => [a.achievement_key, a]));

  // 표시할 업적 (정의 순서대로, 레벨 업적 제외 — 레벨은 별도 표시)
  const displayKeys = Object.keys(defs).filter((k) => !k.startsWith("level_"));

  return (
    <div className="bg-white rounded-2xl border border-gray-200/80 p-6 shadow-[0_4px_20px_rgba(26,28,27,0.03)]">
      <div className="flex items-center gap-2 mb-1">
        <Trophy size={18} className="text-[#2563EB]" />
        <h3 className="font-bold text-[#1a1c1b]">내 성장 기록</h3>
      </div>
      <p className="text-sm text-[#57423c]/60 mb-5">문서를 만들수록 단계가 오르고, 보상이 쌓여요.</p>

      {/* 단계 진행도 */}
      <div className="mb-6">
        <div className="flex items-center gap-1 mb-2">
          {LEVELS.map((l) => {
            const isCurrent = l.level === level;
            const isPast = l.level < level;
            const isLast = l.level === 5;
            return (
              <div key={l.level} className="flex-1 flex flex-col items-center gap-1.5">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center transition-all ${
                  isCurrent
                    ? `${l.bg} ring-2 ring-offset-2 ${l.ring} ${l.color}`
                    : isPast
                    ? `${l.bg} ${l.color}`
                    : "bg-gray-50 text-[#57423c]/40"
                }`}>
                  {isLast ? (
                    <Trophy size={18} strokeWidth={isCurrent ? 2.5 : 1.8} />
                  ) : (
                    <Award size={18} strokeWidth={isCurrent ? 2.5 : 1.8} />
                  )}
                </div>
                <span className={`text-xs leading-tight text-center ${isCurrent ? "font-bold text-[#1a1c1b]" : isPast ? "font-medium text-[#57423c]/70" : "text-[#57423c]/60"}`}>
                  {l.title}
                </span>
                <span className={`text-xs ${isCurrent ? "font-semibold " + l.color : "text-[#57423c]/65"}`}>
                  {l.medal}
                </span>
              </div>
            );
          })}
        </div>
        {nextLevel && (
          <p className="text-sm text-[#57423c]/60 text-center mt-3">
            다음 단계({nextLevel.title})까지 문서 <span className="font-bold text-[#2563EB]">{docsToNext}건</span> 남았어요
          </p>
        )}
        {!nextLevel && (
          <p className="text-sm text-[#2563EB] font-semibold text-center mt-3">
            최고 단계에 도달했어요!
          </p>
        )}
      </div>

      {/* 업적 목록 */}
      <div className="space-y-2">
        {displayKeys.map((key) => {
          const def = defs[key];
          const done = achievedKeys.has(key);
          const record = achievedMap[key];
          const remaining = _remaining(key, totalDocs, user.streak_days || 0);

          return (
            <div key={key} className={`flex items-center gap-3 p-2.5 rounded-xl transition-colors ${done ? "bg-[#f0fdf4]" : "bg-[#f4f4f1]/50"}`}>
              {done ? (
                <CheckCircle2 size={16} className="text-emerald-600 shrink-0" />
              ) : (
                <Circle size={16} className="text-[#57423c]/60 shrink-0" />
              )}
              <div className="flex-1 min-w-0">
                <span className={`text-base ${done ? "text-[#1a1c1b] font-semibold" : "text-[#57423c]"}`}>
                  {def.label}
                </span>
                <span className={`text-xs ml-2 ${done ? "text-emerald-600" : "text-[#57423c]/60"}`}>
                  +{def.reward}%
                </span>
              </div>
              <span className={`text-xs shrink-0 ${done ? "text-[#57423c]/65" : "text-[#2563EB]/70"}`}>
                {done && record
                  ? new Date(record.created_at).toLocaleDateString("ko-KR", { month: "short", day: "numeric" })
                  : remaining}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function _remaining(key: string, totalDocs: number, streak: number): string {
  if (key === "first_doc" && totalDocs < 1) return "1건 만들면 달성!";
  if (key === "docs_5" && totalDocs < 5) return `${5 - totalDocs}건 남았어요`;
  if (key === "docs_10" && totalDocs < 10) return `${10 - totalDocs}건 남았어요`;
  if (key === "streak_3" && streak < 3) return `${3 - streak}일 남았어요`;
  if (key === "streak_7" && streak < 7) return `${7 - streak}일 남았어요`;
  if (key === "streak_14" && streak < 14) return `${14 - streak}일 남았어요`;
  if (key === "streak_30" && streak < 30) return `${30 - streak}일 남았어요`;
  return "";
}
