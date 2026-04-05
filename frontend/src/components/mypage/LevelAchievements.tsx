"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import { listAchievements } from "@/lib/api";
import { Trophy, CheckCircle2, Circle } from "lucide-react";

const LEVELS = [
  { level: 1, title: "새내기", docs: 0 },
  { level: 2, title: "문서러", docs: 5 },
  { level: 3, title: "자동화 전문가", docs: 20 },
  { level: 4, title: "문서 마스터", docs: 50 },
  { level: 5, title: "DocFlow 달인", docs: 100 },
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
      <p className="text-xs text-[#57423c]/60 mb-5">문서를 만들수록 레벨이 오르고, 보상이 쌓여요.</p>

      {/* 레벨 진행도 */}
      <div className="mb-6">
        <div className="flex items-center gap-1 mb-2">
          {LEVELS.map((l) => (
            <div key={l.level} className="flex-1 flex flex-col items-center gap-1">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
                l.level === level
                  ? "bg-[#2563EB] text-white ring-2 ring-[#93C5FD] ring-offset-2"
                  : l.level < level
                  ? "bg-[#DBEAFE] text-[#1E40AF]"
                  : "bg-gray-100 text-[#57423c]/40"
              }`}>
                {l.level}
              </div>
              <span className={`text-[10px] ${l.level === level ? "font-bold text-[#1a1c1b]" : "text-[#57423c]/40"}`}>
                {l.title}
              </span>
            </div>
          ))}
        </div>
        {nextLevel && (
          <p className="text-xs text-[#57423c]/60 text-center mt-2">
            다음 레벨({nextLevel.title})까지 문서 <span className="font-bold text-[#2563EB]">{docsToNext}건</span> 남았어요
          </p>
        )}
        {!nextLevel && (
          <p className="text-xs text-[#2563EB] font-semibold text-center mt-2">
            최고 레벨에 도달했어요!
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
                <Circle size={16} className="text-[#57423c]/40 shrink-0" />
              )}
              <div className="flex-1 min-w-0">
                <span className={`text-sm ${done ? "text-[#1a1c1b] font-semibold" : "text-[#57423c]"}`}>
                  {def.label}
                </span>
                <span className={`text-xs ml-2 ${done ? "text-emerald-600" : "text-[#57423c]/60"}`}>
                  +{def.reward}%
                </span>
              </div>
              <span className={`text-[11px] shrink-0 ${done ? "text-[#57423c]/50" : "text-[#2563EB]/70"}`}>
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
