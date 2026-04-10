"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import { listMyMappings, deleteMapping, updateMappingPublic } from "@/lib/api";
import { FileText, Trash2, Globe, Lock, Loader2 } from "lucide-react";
import Link from "next/link";

interface SavedMapping {
  id: number;
  form_name: string;
  form_field_count: number;
  is_public: boolean;
  likes: number;
  created_at: string;
}

export default function MappingManager() {
  const { user } = useAuth();
  const [mappings, setMappings] = useState<SavedMapping[]>([]);
  const [loading, setLoading] = useState(true);
  const [toggling, setToggling] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [rewardMsg, setRewardMsg] = useState("");

  const plan = user?.plan || "free";
  const limit = user?.mapping_save_limit || 0;

  useEffect(() => {
    if (!user) return;
    listMyMappings().then((list) => { setMappings(list); setLoading(false); });
  }, [user]);

  if (!user) return null;

  const doDelete = async (id: number) => {
    if (!confirm("이 매핑을 삭제할까요? 삭제하면 되돌릴 수 없어요.")) return;
    try {
      await deleteMapping(id);
      setMappings((prev) => prev.filter((m) => m.id !== id));
    } catch {
      setError("삭제 실패");
    }
  };

  const doTogglePublic = async (m: SavedMapping) => {
    setToggling(m.id);
    setError("");
    try {
      const res = await updateMappingPublic(m.id, !m.is_public);
      setMappings((prev) => prev.map((x) => x.id === m.id ? { ...x, is_public: !m.is_public } : x));
      if (res.rewards?.length > 0) {
        setRewardMsg(`공개 보상으로 +${res.rewards[0].reward}% 게이지가 충전되었어요!`);
        setTimeout(() => setRewardMsg(""), 3000);
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "공개 설정 실패");
    } finally {
      setToggling(null);
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-gray-200/80 p-6 shadow-[0_4px_20px_rgba(26,28,27,0.03)]">
      <div className="flex items-center gap-2 mb-1">
        <FileText size={18} className="text-[#2563EB]" />
        <h3 className="font-bold text-[#1a1c1b]">저장된 양식 매핑</h3>
      </div>
      <p className="text-sm text-[#57423c]/60 mb-4">한번 만든 매핑을 저장하면 같은 양식에 다시 쓸 수 있어요.</p>

      {error && <p className="text-sm text-red-500 mb-2">{error}</p>}
      {rewardMsg && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl px-3 py-2 text-base text-emerald-700 mb-3">
          {rewardMsg}
        </div>
      )}

      {/* Free 사용자 */}
      {plan === "free" && limit === 0 ? (
        <div className="text-center py-6">
          <p className="text-base text-[#57423c]/65 mb-2">무료 플랜은 매핑 저장을 지원하지 않아요.</p>
          <Link href="/pricing" className="text-sm text-[#2563EB] font-semibold hover:underline">
            Plus로 업그레이드하면 10개까지 저장할 수 있어요 →
          </Link>
        </div>
      ) : loading ? (
        <div className="text-center py-6 text-base text-[#57423c]/60"><Loader2 size={16} className="animate-spin inline" /> 불러오는 중...</div>
      ) : mappings.length === 0 ? (
        <div className="text-center py-6">
          <p className="text-base text-[#57423c]/65 mb-2">아직 저장한 매핑이 없어요.</p>
          <p className="text-sm text-[#57423c]/60">도구 페이지에서 AI 매핑 후 &apos;매핑 저장&apos; 버튼을 눌러보세요.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {mappings.map((m) => (
            <div key={m.id} className="border border-gray-100 rounded-xl p-3 hover:border-[#93C5FD]/50 transition-colors">
              <div className="flex items-center justify-between mb-1">
                <span className="text-base font-semibold text-[#1a1c1b] truncate">{m.form_name}</span>
                <div className="flex items-center gap-1 shrink-0">
                  <button
                    onClick={() => doTogglePublic(m)}
                    disabled={toggling === m.id}
                    className={`p-1.5 rounded-lg text-xs font-semibold flex items-center gap-1 transition-colors ${
                      m.is_public
                        ? "text-emerald-600 bg-emerald-50 hover:bg-emerald-100"
                        : "text-[#57423c]/60 hover:text-[#2563EB] hover:bg-[#EFF6FF]"
                    }`}
                  >
                    {toggling === m.id ? <Loader2 size={10} className="animate-spin" /> : m.is_public ? <Globe size={10} /> : <Lock size={10} />}
                    {m.is_public ? "공개" : "비공개"}
                  </button>
                  <button onClick={() => doDelete(m.id)} className="p-1 text-[#57423c]/65 hover:text-red-500"><Trash2 size={12} /></button>
                </div>
              </div>
              <div className="flex items-center gap-3 text-xs text-[#57423c]/60">
                <span>{m.form_field_count}개 항목</span>
                {m.likes > 0 && <span>{m.likes}명이 사용</span>}
                <span>{new Date(m.created_at).toLocaleDateString("ko-KR")}</span>
              </div>
              {!m.is_public && (
                <p className="text-xs text-[#57423c]/65 mt-1">공개하면 다른 사용자도 이 매핑을 사용할 수 있어요. 처음 공개 시 +25% 보상!</p>
              )}
            </div>
          ))}
        </div>
      )}

      {/* 한도 표시 */}
      {limit > 0 && (
        <div className="mt-4 pt-3 border-t border-gray-100 flex items-center justify-between">
          <span className="text-xs text-[#57423c]/60">{mappings.length}/{limit >= 9999 ? "무제한" : limit}개 사용 중</span>
          {mappings.length >= limit && limit < 9999 && (
            <Link href="/pricing" className="text-xs text-[#2563EB] hover:underline">Pro로 업그레이드 →</Link>
          )}
        </div>
      )}
    </div>
  );
}
