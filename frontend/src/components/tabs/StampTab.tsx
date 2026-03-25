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
      <p className="text-sm text-gray-800">
        문서에서 &quot;(인)&quot; 글자를 찾아 도장 이미지로 바꿔줍니다.
        <span className="text-xs block mt-1 text-gray-600">예: 계약서의 (인) 자리에 직인 이미지 삽입</span>
      </p>
      {!isAnalyzed && (
        <div className="text-xs px-3 py-2 rounded-lg inline-flex items-center gap-1 bg-gray-100 text-gray-600">
          왼쪽에서 양식을 먼저 분석해주세요
        </div>
      )}

      <FileUpload accept=".png,.jpg,.jpeg,.gif,.bmp" label="도장/서명 이미지 (PNG, JPG)" onFiles={(f) => setImage(f[0])} />

      <div>
        <label className="text-xs text-gray-800 mb-1 block">바꿀 글자 (문서에서 이 글자를 찾아 도장으로 바꿉니다)</label>
        <input className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-gray-400" value={target} onChange={(e) => setTarget(e.target.value)} />
      </div>

      <button
        onClick={doStamp}
        disabled={loading || !isAnalyzed || !image}
        className="w-full bg-black text-white py-3 rounded-lg font-semibold text-sm hover:bg-gray-800 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center gap-2"
      >
        {loading ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
        {loading ? "삽입 중..." : "도장 삽입"}
      </button>

      {error && <div className="text-sm text-red-500 bg-red-50 p-3 rounded-lg">{error}</div>}
    </div>
  );
}
