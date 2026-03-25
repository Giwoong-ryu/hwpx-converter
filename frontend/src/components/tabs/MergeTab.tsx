"use client";

import { useState } from "react";
import { mergeDocs, downloadBlob } from "@/lib/api";
import FileUpload from "@/components/ui/FileUpload";
import { Loader2, Download } from "lucide-react";

export default function MergeTab() {
  const [files, setFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const doMerge = async () => {
    if (files.length < 2) return;
    setLoading(true);
    setError("");
    try {
      const blob = await mergeDocs(files);
      downloadBlob(blob, "DocFlow_merged.hwpx");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "병합 실패");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="rounded-xl p-4 mb-2 bg-gray-50">
        <p className="text-sm font-medium text-gray-700">여러 한글 파일을 하나의 문서로 합쳐줍니다.</p>
        <p className="text-xs mt-1 text-gray-800">예: 팀원 5명의 보고서를 하나의 파일로 합본. 양식 분석 없이 바로 사용 가능합니다.</p>
      </div>
      <FileUpload accept=".hwpx" multiple label="HWPX 파일들 (2개 이상)" onFiles={setFiles} />
      <button
        onClick={doMerge}
        disabled={loading || files.length < 2}
        className="w-full bg-black text-white py-3 rounded-lg font-semibold text-sm hover:bg-gray-800 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center gap-2"
      >
        {loading ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
        {loading ? "합치는 중..." : "합치기"}
      </button>
      {error && <div className="text-sm text-red-500 bg-red-50 p-3 rounded-lg">{error}</div>}
    </div>
  );
}
