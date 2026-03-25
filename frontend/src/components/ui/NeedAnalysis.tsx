"use client";

import { FileText } from "lucide-react";

interface Props {
  title: string;
  desc: string;
  example: string;
  needsForm?: boolean;
}

export default function NeedAnalysis({ title, desc, example, needsForm = true }: Props) {
  return (
    <div className="text-center py-4 px-4">
      <h3 className="text-sm font-bold mb-1 text-gray-900">{title}</h3>
      <p className="text-xs mb-2 text-gray-800">{desc}</p>
      <p className="text-xs text-gray-600">{example}</p>
      {needsForm && (
        <div className="mt-3 inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
          <FileText size={12} />
          왼쪽에서 양식 파일을 먼저 분석해주세요
        </div>
      )}
    </div>
  );
}
