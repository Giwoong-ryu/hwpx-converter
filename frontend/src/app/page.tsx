"use client";

import { useState } from "react";
import { FormProvider, useForm } from "@/context/FormContext";
import { analyzeForm } from "@/lib/api";
import FileUpload from "@/components/ui/FileUpload";
import AiMappingTab from "@/components/tabs/AiMappingTab";
import BatchTab from "@/components/tabs/BatchTab";
import ExtractTab from "@/components/tabs/ExtractTab";
import PeriodicTab from "@/components/tabs/PeriodicTab";
import StampTab from "@/components/tabs/StampTab";
import MergeTab from "@/components/tabs/MergeTab";
import ExcelTab from "@/components/tabs/ExcelTab";
import {
  FileText, Loader2, Shield, Wand2, Layers, TableProperties,
  Calendar, Stamp, Merge, CheckCircle2, FileSpreadsheet
} from "lucide-react";

const TABS = [
  { id: "ai", label: "AI 매핑", icon: Wand2, desc: "AI가 양식에 맞게 자동 배치" },
  { id: "batch", label: "엑셀->문서", icon: Layers, desc: "엑셀로 N개 문서 한번에" },
  { id: "extract", label: "문서->엑셀", icon: TableProperties, desc: "문서 텍스트를 엑셀로" },
  { id: "periodic", label: "정기문서", icon: Calendar, desc: "날짜만 바꿔서 반복 생성" },
  { id: "stamp", label: "도장", icon: Stamp, desc: "(인) -> 도장 이미지" },
  { id: "merge", label: "합치기", icon: Merge, desc: "여러 파일 -> 하나" },
  { id: "excel", label: "엑셀 채우기", icon: FileSpreadsheet, desc: "엑셀 양식에 데이터 채우기" },
];

function Main() {
  const { isAnalyzed, filename, fieldCount, setForm } = useForm();
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [warning, setWarning] = useState("");
  const [activeTab, setActiveTab] = useState("ai");
  const [showInfo, setShowInfo] = useState(false);

  const doAnalyze = async () => {
    if (!file) return;
    setLoading(true);
    setError("");
    try {
      const res = await analyzeForm(file);
      setForm({
        fileId: res.file_id,
        filename: res.filename,
        fields: res.fields,
        fieldCount: res.field_count,
        isAnalyzed: true,
      });
      setWarning(res.warning || "");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "분석 실패");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-white">
      {/* 헤더 */}
      <header className="border-b border-black py-6 text-center">
        <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Eazy HWPX</h1>
        <p className="text-sm text-gray-600 mt-1">한글 양식에 내용을 채워 새 문서를 만듭니다</p>
      </header>

      {/* 메인 */}
      <div className="max-w-6xl mx-auto px-6 py-6 flex gap-6 items-stretch">

        {/* 왼쪽: 양식 넣기 */}
        <div className="w-[300px] shrink-0">
          <div className="border border-black rounded-2xl p-5 sticky top-6">
            <div className="flex items-center gap-2 mb-3">
              <FileText size={18} className="text-gray-600" />
              <h2 className="font-semibold text-gray-800">양식 넣기</h2>
            </div>
            <p className="text-xs text-gray-600 mb-4">
              양식을 올리고 분석하면 오른쪽 기능들에서 사용됩니다.
            </p>

            <FileUpload accept=".hwp,.hwpx" label="HWP / HWPX 파일" onFiles={(f) => setFile(f[0])} />

            <button
              onClick={doAnalyze}
              disabled={loading || !file}
              className="w-full mt-3 bg-black text-white py-2.5 rounded-lg font-semibold text-sm hover:bg-gray-800 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? <Loader2 size={14} className="animate-spin" /> : null}
              {loading ? "분석 중..." : "양식 분석"}
            </button>

            {error && <div className="text-xs text-red-500 mt-2 bg-red-50 rounded-lg p-2">{error}</div>}
            {warning && <div className="text-xs text-amber-700 mt-2 bg-amber-50 rounded-lg p-2">{warning}</div>}

            {isAnalyzed && (
              <div className="mt-3 bg-green-50 border border-green-100 rounded-lg px-3 py-2 flex items-start gap-2">
                <CheckCircle2 size={16} className="text-green-600 mt-0.5 shrink-0" />
                <div>
                  <div className="text-xs font-bold">{filename}</div>
                  <div className="text-xs opacity-80">{fieldCount}개 필드 발견</div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* 오른쪽: 기능 탭 */}
        <div className="flex-1 min-w-0">
          {/* 탭 헤더 */}
          <div className="flex border-b border-black mb-4 overflow-x-auto">
            {TABS.map((tab) => {
              const Icon = tab.icon;
              const active = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-1.5 px-4 py-2.5 text-sm whitespace-nowrap border-b-2 transition-colors ${
                    active
                      ? "border-black text-black font-bold"
                      : "border-transparent text-gray-900 hover:bg-gray-50"
                  }`}
                >
                  <Icon size={15} />
                  {tab.label}
                </button>
              );
            })}
          </div>

          {/* 탭 콘텐츠 */}
          <div className="border border-black rounded-2xl p-5">
            {activeTab === "ai" && <AiMappingTab />}
            {activeTab === "batch" && <BatchTab />}
            {activeTab === "extract" && <ExtractTab />}
            {activeTab === "periodic" && <PeriodicTab />}
            {activeTab === "stamp" && <StampTab />}
            {activeTab === "merge" && <MergeTab />}
            {activeTab === "excel" && <ExcelTab />}
          </div>
        </div>
      </div>

      {/* 푸터 */}
      <footer className="py-6 text-center">
        <button
          onClick={() => setShowInfo(!showInfo)}
          className="bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-lg px-4 py-2 inline-flex items-center gap-2 transition-colors"
        >
          <Shield size={13} className="text-gray-700" />
          <span className="text-xs text-gray-900">내 데이터는 어떻게 처리되나요?</span>
        </button>
        {showInfo && (
          <div className="max-w-md mx-auto mt-3 text-left text-xs text-gray-600 leading-relaxed bg-gray-50 rounded-xl p-4 border border-gray-200 space-y-2">
            <p><strong className="text-gray-700">AI 자동 매핑</strong> — 이 기능만 Google AI를 사용합니다. 양식 필드와 입력 내용을 AI에 보내 자동 배치하기 위해서입니다. 데이터는 학습에 사용되지 않으며, 55일 후 삭제됩니다.</p>
            <p><strong className="text-gray-700">그 외 모든 기능</strong> — 외부 전송 없이 이 PC에서만 처리됩니다.</p>
            <p><strong className="text-gray-700">파일</strong> — 분석과 생성 단계 사이에 사용하기 위해 임시 저장됩니다. 서버 종료 시 자동 삭제됩니다.</p>
          </div>
        )}
      </footer>
    </div>
  );
}

export default function Page() {
  return (
    <FormProvider>
      <Main />
    </FormProvider>
  );
}
