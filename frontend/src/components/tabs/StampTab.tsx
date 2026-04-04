"use client";

import { useState } from "react";
import { useForm } from "@/context/FormContext";
import { stampInsert, downloadBlob } from "@/lib/api";
import FileUpload from "@/components/ui/FileUpload";
import { Loader2, Download } from "lucide-react";

export default function StampTab() {
  const { fileId, isAnalyzed } = useForm();
  const [image, setImage] = useState<File | null>(null);
  const [target, setTarget] = useState("(인)");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const doStamp = async () => {
    if (!fileId || !image) return;
    setLoading(true);
    setError("");
    try {
      const blob = await stampInsert(fileId, image, target);
      downloadBlob(blob, "DocFlow_stamped.hwpx");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "도장 삽입 실패");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <p className="text-base text-[#57423c]">
        문서에서 &quot;(인)&quot; 글자를 찾아 도장 이미지로 바꿔줍니다.
        <span className="text-sm block mt-1 text-[#57423c]">예: 계약서의 (인) 자리에 직인 이미지 삽입</span>
      </p>
      {!isAnalyzed && (
        <div className="text-sm px-3 py-2 rounded-xl inline-flex items-center gap-1 bg-[#DBEAFE] text-[#1E40AF] font-medium">
          왼쪽에서 양식을 먼저 분석해주세요
        </div>
      )}

      <div>
        <div className="w-full"><FileUpload accept=".png,.jpg,.jpeg,.gif,.bmp" label="도장/서명 이미지 (PNG, JPG)" onFiles={(f) => setImage(f[0])} /></div>
      </div>

      <div>
        <label className="text-sm text-[#1a1c1b] font-medium mb-1 block">바꿀 글자 (문서에서 이 글자를 찾아 도장으로 바꿉니다)</label>
        <input className="w-full border border-[#93C5FD]/400 rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-[#1E40AF]/40 bg-white transition-colors" value={target} onChange={(e) => setTarget(e.target.value)} />
      </div>

      <button
        onClick={doStamp}
        disabled={loading || !isAnalyzed || !image}
        className="w-full bg-gradient-to-r from-[#2563EB] to-[#1E40AF] text-white py-3 rounded-xl font-semibold text-sm hover:opacity-90 disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-all active:scale-[0.98]"
      >
        {loading ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
        {loading ? "삽입 중..." : "도장 삽입"}
      </button>

      {error && <div className="text-sm text-red-600 bg-red-50 p-3 rounded-xl">{error}</div>}
    </div>
  );
}
