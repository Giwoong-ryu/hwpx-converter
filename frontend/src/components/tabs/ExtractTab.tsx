"use client";

import { useState } from "react";
import { extractData, downloadBlob } from "@/lib/api";
import FileUpload from "@/components/ui/FileUpload";
import { Loader2, Download } from "lucide-react";

export default function ExtractTab() {
  const [files, setFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const doExtract = async () => {
    if (!files.length) return;
    setLoading(true);
    setError("");
    try {
      const blob = await extractData(files);
      downloadBlob(blob, "DocFlow_extracted.xlsx");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "추출 실패");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="rounded-xl p-4 mb-2 bg-[#f4f4f1]">
        <p className="text-base font-semibold text-[#1a1c1b]">한글 문서 안의 텍스트를 엑셀로 뽑아줍니다.</p>
        <p className="text-sm mt-1 text-[#57423c]">예: 접수된 신청서 50건의 내용을 엑셀 하나로 정리. 양식 분석 없이 바로 사용 가능합니다.</p>
      </div>
      <div>
        <div className="w-full"><FileUpload accept=".hwp,.hwpx,.docx" multiple label="문서 파일 (여러 개 가능)" onFiles={setFiles} /></div>
      </div>
      <button
        onClick={doExtract}
        disabled={loading || !files.length}
        className="w-full bg-gradient-to-r from-[#2563EB] to-[#1E40AF] text-white py-3 rounded-xl font-semibold text-sm hover:opacity-90 disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-all active:scale-[0.98]"
      >
        {loading ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
        {loading ? "추출 중..." : "추출하기"}
      </button>
      {error && <div className="text-sm text-red-600 bg-red-50 p-3 rounded-xl">{error}</div>}
    </div>
  );
}
