"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import { listPresets, createPreset, updatePreset, deletePreset } from "@/lib/api";
import { Database, Plus, Pencil, Trash2, X, Save, Loader2 } from "lucide-react";
import Link from "next/link";

interface Preset {
  id: number;
  name: string;
  data: Record<string, string>;
  created_at: string;
  updated_at: string;
}

export default function PresetManager() {
  const { user } = useAuth();
  const [presets, setPresets] = useState<Preset[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [formName, setFormName] = useState("");
  const [formData, setFormData] = useState<[string, string][]>([["", ""]]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const plan = user?.plan || "free";
  const limit = user?.preset_limit || 1;

  useEffect(() => {
    if (!user) return;
    listPresets().then((list) => { setPresets(list); setLoading(false); });
  }, [user]);

  if (!user) return null;

  const startEdit = (p: Preset) => {
    setEditingId(p.id);
    setFormName(p.name);
    setFormData(Object.entries(p.data).length > 0 ? Object.entries(p.data) : [["", ""]]);
    setError("");
  };

  const startCreate = () => {
    setShowCreate(true);
    setEditingId(null);
    setFormName("");
    setFormData([["", ""]]);
    setError("");
  };

  const cancel = () => {
    setEditingId(null);
    setShowCreate(false);
    setError("");
  };

  const addField = () => setFormData([...formData, ["", ""]]);

  const removeField = (i: number) => {
    const copy = [...formData];
    copy.splice(i, 1);
    setFormData(copy.length > 0 ? copy : [["", ""]]);
  };

  const doSave = async () => {
    if (!formName.trim()) { setError("프리셋 이름을 입력해주세요."); return; }
    const data: Record<string, string> = {};
    formData.forEach(([k, v]) => { if (k.trim()) data[k.trim()] = v.trim(); });
    if (Object.keys(data).length === 0) { setError("항목을 1개 이상 입력해주세요."); return; }

    setSaving(true);
    setError("");
    try {
      if (editingId) {
        await updatePreset(editingId, formName.trim(), data);
        setPresets((prev) => prev.map((p) => p.id === editingId ? { ...p, name: formName.trim(), data } : p));
      } else {
        const res = await createPreset(formName.trim(), data);
        if (res.preset) setPresets((prev) => [res.preset, ...prev]);
      }
      cancel();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "저장 실패");
    } finally {
      setSaving(false);
    }
  };

  const doDelete = async (id: number) => {
    if (!confirm("이 프리셋을 삭제할까요? 삭제하면 되돌릴 수 없어요.")) return;
    try {
      await deletePreset(id);
      setPresets((prev) => prev.filter((p) => p.id !== id));
    } catch {
      setError("삭제 실패");
    }
  };

  const isEditing = editingId !== null || showCreate;

  return (
    <div className="bg-white rounded-2xl border border-gray-200/80 p-6 shadow-[0_4px_20px_rgba(26,28,27,0.03)]">
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2">
          <Database size={18} className="text-[#2563EB]" />
          <h3 className="font-bold text-[#1a1c1b]">내 정보 프리셋</h3>
        </div>
        {!isEditing && presets.length < limit && (
          <button onClick={startCreate} className="text-xs text-[#2563EB] font-semibold flex items-center gap-1 hover:underline">
            <Plus size={12} /> 새 프리셋
          </button>
        )}
      </div>
      <p className="text-sm text-[#57423c]/60 mb-4">자주 쓰는 정보를 저장해두면 다음에 바로 사용할 수 있어요.</p>

      {/* 편집/생성 폼 */}
      {isEditing && (
        <div className="border border-[#93C5FD]/50 rounded-xl p-4 mb-4 space-y-3">
          <input
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#2563EB]/40"
            placeholder="프리셋 이름 (예: 회사 정보)"
            value={formName}
            onChange={(e) => setFormName(e.target.value)}
          />
          {formData.map(([k, v], i) => (
            <div key={i} className="flex gap-2">
              <input
                className="flex-1 border border-gray-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-[#2563EB]/40"
                placeholder="항목명 (예: 회사명)"
                value={k}
                onChange={(e) => { const c = [...formData]; c[i] = [e.target.value, v]; setFormData(c); }}
              />
              <input
                className="flex-[2] border border-gray-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-[#2563EB]/40"
                placeholder="값 (예: 주식회사 OO)"
                value={v}
                onChange={(e) => { const c = [...formData]; c[i] = [k, e.target.value]; setFormData(c); }}
              />
              <button onClick={() => removeField(i)} className="text-[#57423c]/65 hover:text-red-500 p-1"><X size={14} /></button>
            </div>
          ))}
          <button onClick={addField} className="text-xs text-[#2563EB] hover:underline">+ 항목 추가</button>
          {error && <p className="text-sm text-red-500">{error}</p>}
          <div className="flex gap-2 justify-end">
            <button onClick={cancel} className="px-3 py-1.5 text-xs text-[#57423c] hover:bg-[#f4f4f1] rounded-lg">취소</button>
            <button onClick={doSave} disabled={saving} className="px-4 py-1.5 text-xs font-semibold text-white bg-[#2563EB] rounded-lg hover:bg-[#1E40AF] disabled:opacity-50 flex items-center gap-1">
              {saving ? <Loader2 size={12} className="animate-spin" /> : <Save size={12} />}
              저장
            </button>
          </div>
        </div>
      )}

      {/* 프리셋 목록 */}
      {loading ? (
        <div className="text-center py-6 text-base text-[#57423c]/60"><Loader2 size={16} className="animate-spin inline" /> 불러오는 중...</div>
      ) : presets.length === 0 && !isEditing ? (
        <div className="text-center py-6">
          <p className="text-base text-[#57423c]/65 mb-2">아직 저장한 프리셋이 없어요.</p>
          <p className="text-sm text-[#57423c]/60">도구 페이지에서 문서 작성 시 자주 쓰는 정보를 저장해보세요.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {presets.map((p) => (
            <div key={p.id} className="border border-gray-100 rounded-xl p-3 hover:border-[#93C5FD]/50 transition-colors">
              <div className="flex items-center justify-between mb-2">
                <span className="text-base font-semibold text-[#1a1c1b]">{p.name}</span>
                <div className="flex items-center gap-1">
                  <button onClick={() => startEdit(p)} className="p-1 text-[#57423c]/65 hover:text-[#2563EB]"><Pencil size={12} /></button>
                  <button onClick={() => doDelete(p.id)} className="p-1 text-[#57423c]/65 hover:text-red-500"><Trash2 size={12} /></button>
                </div>
              </div>
              <div className="space-y-0.5">
                {Object.entries(p.data).slice(0, 4).map(([k, v]) => (
                  <p key={k} className="text-xs text-[#57423c]/70">
                    <span className="text-[#57423c] font-medium">{k}:</span> {String(v)}
                  </p>
                ))}
                {Object.keys(p.data).length > 4 && (
                  <p className="text-xs text-[#57423c]/60">+{Object.keys(p.data).length - 4}개 더</p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 한도 표시 */}
      <div className="mt-4 pt-3 border-t border-gray-100 flex items-center justify-between">
        <span className="text-xs text-[#57423c]/60">{presets.length}/{limit >= 9999 ? "무제한" : limit}개 사용 중</span>
        {presets.length >= limit && limit < 9999 && (
          <Link href="/pricing" className="text-xs text-[#2563EB] hover:underline">
            {plan === "free" ? "Plus로 업그레이드 →" : "Pro로 업그레이드 →"}
          </Link>
        )}
      </div>
    </div>
  );
}
