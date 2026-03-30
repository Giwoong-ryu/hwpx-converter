"use client";

import { useState } from "react";
import Link from "next/link";
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
  Calendar, Stamp, Merge, CheckCircle2, FileSpreadsheet,
  Sparkles, ChevronLeft
} from "lucide-react";

const TABS = [
  { id: "ai", label: "AI 자동 작성", icon: Wand2, benefit: "주제만 알려주면 문서를 대신 써줍니다" },
  { id: "batch", label: "엑셀->문서", icon: Layers, benefit: "엑셀 100행이면 문서 100개가 한번에" },
  { id: "extract", label: "문서->엑셀", icon: TableProperties, benefit: "문서 안의 모든 글자를 엑셀로 정리" },
  { id: "periodic", label: "정기문서", icon: Calendar, benefit: "매달 보고서를 12개월치 한번에" },
  { id: "stamp", label: "도장", icon: Stamp, benefit: "(인) 자리에 도장을 자동으로 찍어줍니다" },
  { id: "merge", label: "합치기", icon: Merge, benefit: "여러 파일을 하나로 합쳐줍니다" },
  { id: "excel", label: "엑셀 채우기", icon: FileSpreadsheet, benefit: "엑셀 양식의 빈칸을 자동으로 채웁니다" },
];

const TAB_GUIDE: Record<string, { what: string; examples: string[] }> = {
  ai: {
    what: "내용을 직접 붙여넣거나, AI에게 \"써줘\"라고 하면 문서를 대신 작성합니다.",
    examples: [
      "\"온라인 교육 플랫폼 사업계획서 써줘\" → AI가 빈 양식에 17페이지 내용을 채워줌",
      "내가 가진 텍스트를 복사 붙여넣기 → 양식의 빈칸에 알아서 넣어줌",
      "엑셀이나 워드 파일을 올리면 → 그 안의 내용을 양식에 자동으로 넣어줌",
    ],
  },
  batch: {
    what: "엑셀에 여러 사람 정보가 있으면, 같은 양식으로 사람 수만큼 문서를 만들어 줍니다.",
    examples: [
      "급여명세서 — 엑셀에 직원 100명 이름/급여 넣고, 양식 하나 올리면 → 100개 문서가 한번에 나옴",
      "수료증 — 엑셀에 수료자 이름/날짜 넣고, 수료증 양식 올리면 → 50장이 한번에 나옴",
      "계약서 — 엑셀에 업체명/금액 넣고, 계약서 양식 올리면 → 업체별 계약서 30개가 나옴",
    ],
  },
  extract: {
    what: "문서 안에 있는 글자를 전부 뽑아서 엑셀 파일로 만들어 줍니다.",
    examples: [
      "사업계획서 안의 모든 텍스트 → 엑셀로 정리해서 한눈에 보기",
      "양식 안에 어떤 빈칸들이 있는지 목록으로 확인하고 싶을 때",
      "여러 문서의 내용을 엑셀로 뽑아서 서로 비교할 때",
    ],
  },
  periodic: {
    what: "매달/매주 날짜만 바뀌는 같은 문서를, 한번에 여러 달치 만들어 줍니다.",
    examples: [
      "월간 보고서 — 1월~12월까지 날짜만 다른 보고서 12개를 한번에",
      "주간 업무일지 — 52주치 날짜가 자동으로 바뀐 일지를 한번에",
      "분기 보고서 — 1분기~4분기 보고서 4개를 한번에",
    ],
  },
  stamp: {
    what: "문서에 (인)이라고 써있는 곳에 실제 도장/서명 이미지를 넣어줍니다.",
    examples: [
      "공문서의 (인) 자리에 회사 직인 이미지를 자동으로 넣기",
      "계약서 하단 서명란에 내 서명 이미지 넣기",
      "문서 여러 개에 같은 도장을 한번에 찍기",
    ],
  },
  merge: {
    what: "여러 개의 문서 파일을 하나의 파일로 합쳐줍니다.",
    examples: [
      "각 부서에서 따로 받은 보고서 5개 → 하나의 파일로 합치기",
      "제안서를 파트별로 나눠 작성한 뒤 → 최종 하나로 합치기",
      "여러 장의 공문을 하나의 문서로 묶기",
    ],
  },
  excel: {
    what: "엑셀 파일의 특정 칸에 데이터를 자동으로 넣어줍니다.",
    examples: [
      "견적서 엑셀의 품목명, 수량, 금액 칸에 데이터 자동 입력",
      "출석부 엑셀의 이름/날짜 칸을 한번에 채우기",
      "정산서 엑셀의 매달 금액 칸을 자동으로 채우기",
    ],
  },
};

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

  const guide = TAB_GUIDE[activeTab] || TAB_GUIDE.ai;
  const activeTabData = TABS.find(t => t.id === activeTab);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 헤더 */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/" className="flex items-center gap-1 text-gray-400 hover:text-gray-600 transition-colors">
              <ChevronLeft size={16} />
            </Link>
            <h1 className="text-lg font-bold text-gray-900">Eazy HWPX</h1>
            <span className="text-sm text-gray-500">양식 파일을 올리면 AI가 내용을 채워서 완성된 문서를 만들어 줍니다</span>
          </div>
          <span className="text-xs text-gray-400">HWP · HWPX · DOCX</span>
        </div>
      </header>

      {/* 도구 영역 */}
      <div className="max-w-6xl mx-auto px-6 py-6 flex gap-5">
        {/* 왼쪽: 양식 넣기 */}
        <div className="w-[280px] shrink-0">
          <div className="bg-white border border-gray-200 rounded-xl p-5 sticky top-6">
            <div className="flex items-center gap-2 mb-2">
              <FileText size={16} className="text-gray-500" />
              <h2 className="font-bold text-sm text-gray-900">양식 넣기</h2>
            </div>
            <p className="text-xs text-gray-500 mb-4">내용을 넣을 빈 문서를 올리고 분석하세요.</p>

            <FileUpload accept=".hwp,.hwpx,.docx" label="HWP / HWPX / DOCX 파일" onFiles={(f) => setFile(f[0])} />

            <button
              onClick={doAnalyze}
              disabled={loading || !file}
              className="w-full mt-3 bg-gray-900 text-white py-2.5 rounded-lg font-semibold text-sm hover:bg-gray-800 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? <Loader2 size={14} className="animate-spin" /> : null}
              {loading ? "분석 중..." : "양식 분석"}
            </button>

            {error && <div className="text-xs text-red-600 mt-2 bg-red-50 rounded-lg p-2">{error}</div>}
            {warning && <div className="text-xs text-amber-700 mt-2 bg-amber-50 rounded-lg p-2">{warning}</div>}

            {isAnalyzed && (
              <div className="mt-3 bg-emerald-50 border border-emerald-100 rounded-lg px-3 py-2 flex items-start gap-2">
                <CheckCircle2 size={15} className="text-emerald-600 mt-0.5 shrink-0" />
                <div>
                  <div className="text-xs font-bold text-gray-900">{filename}</div>
                  <div className="text-xs text-gray-500">{fieldCount}개 항목 발견</div>
                </div>
              </div>
            )}

            {/* 사용 흐름 */}
            <div className="mt-5 pt-4 border-t border-gray-100 space-y-2">
              <p className="text-xs text-gray-400 font-medium">사용 흐름</p>
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <span className="w-4 h-4 bg-gray-200 rounded-full flex items-center justify-center text-[10px] font-bold text-gray-600">1</span>
                양식 업로드
              </div>
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <span className="w-4 h-4 bg-gray-200 rounded-full flex items-center justify-center text-[10px] font-bold text-gray-600">2</span>
                내용 채우기 (텍스트 · 엑셀 · AI)
              </div>
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <span className="w-4 h-4 bg-gray-200 rounded-full flex items-center justify-center text-[10px] font-bold text-gray-600">3</span>
                완성 문서 다운로드
              </div>
            </div>
          </div>
        </div>

        {/* 오른쪽 */}
        <div className="flex-1 min-w-0 space-y-4">
          {/* 탭 헤더 */}
          <div className="relative">
            <span className="absolute -top-2.5 left-[calc(100%/14+8px)] z-10 bg-emerald-500 text-white text-[9px] px-2 py-0.5 rounded-full font-bold shadow-sm">추천</span>
            <div className="flex bg-white border border-gray-200 rounded-xl overflow-hidden">
              {TABS.map((tab) => {
                const Icon = tab.icon;
                const active = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex-1 flex items-center justify-center gap-1.5 py-3 text-xs font-medium transition-colors ${
                      active
                        ? "bg-gray-900 text-white"
                        : "text-gray-600 hover:bg-gray-50"
                    }`}
                  >
                    <Icon size={14} />
                    {tab.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* 현재 탭 Benefit */}
          {activeTabData && (
            <div className="bg-white border border-gray-200 rounded-lg px-4 py-2.5 flex items-center gap-2">
              <Sparkles size={14} className="text-gray-400 shrink-0" />
              <span className="text-sm text-gray-700">{activeTabData.benefit}</span>
            </div>
          )}

          {/* 탭 콘텐츠 */}
          <div className="bg-white border border-gray-200 rounded-xl p-5">
            {activeTab === "ai" && <AiMappingTab />}
            {activeTab === "batch" && <BatchTab />}
            {activeTab === "extract" && <ExtractTab />}
            {activeTab === "periodic" && <PeriodicTab />}
            {activeTab === "stamp" && <StampTab />}
            {activeTab === "merge" && <MergeTab />}
            {activeTab === "excel" && <ExcelTab />}
          </div>

          {/* 탭별 예시 */}
          <div className="bg-white border border-gray-200 rounded-xl p-5">
            <p className="text-xs text-gray-500 mb-3">이런 식으로 사용합니다</p>
            <div className="space-y-2.5">
              {guide.examples.map((ex, i) => (
                <div key={`${activeTab}-${i}`} className="flex gap-3 items-start">
                  <span className="bg-gray-900 text-white text-xs font-bold w-5 h-5 rounded-full flex items-center justify-center shrink-0 mt-0.5">{i + 1}</span>
                  <span className="text-sm text-gray-700 leading-relaxed">{ex}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* 푸터 */}
      <footer className="max-w-6xl mx-auto px-6 py-6 text-center">
        <button
          onClick={() => setShowInfo(!showInfo)}
          className="bg-white hover:bg-gray-100 border border-gray-200 rounded-lg px-4 py-2 inline-flex items-center gap-2 transition-colors"
        >
          <Shield size={13} className="text-gray-500" />
          <span className="text-xs text-gray-700">내 데이터는 어떻게 처리되나요?</span>
        </button>
        {showInfo && (
          <div className="max-w-lg mx-auto mt-3 text-left text-xs text-gray-600 leading-relaxed bg-white rounded-xl p-4 border border-gray-200 space-y-2">
            <p><strong className="text-gray-800">양식 분석 / 문서 생성</strong> — 외부 서비스 없이 이 서버에서만 처리됩니다.</p>
            <p><strong className="text-gray-800">대량 생성 / 추출 / 병합</strong> — 외부 서비스 없이 이 서버에서만 처리됩니다.</p>
            <p><strong className="text-gray-800">AI 자동 작성</strong> — 이 기능만 Google AI를 사용합니다. 데이터는 학습에 사용되지 않으며, 55일 후 삭제됩니다.</p>
            <p><strong className="text-gray-800">파일 보관</strong> — 3시간 후 자동 삭제되며, 서버 종료 시에도 삭제됩니다.</p>
            <p><strong className="text-gray-800">네트워크</strong> — HTTPS(TLS) 암호화 통신을 사용합니다.</p>
          </div>
        )}
      </footer>
    </div>
  );
}

export default function ToolPage() {
  return (
    <FormProvider>
      <Main />
    </FormProvider>
  );
}
