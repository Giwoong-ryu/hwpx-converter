import Link from "next/link";
import { FileText, Shield } from "lucide-react";

export default function Footer() {
  return (
    <footer className="border-t border-gray-200/60 bg-[#f9f9f6] mt-auto">
      <div className="max-w-screen-xl mx-auto px-8 lg:px-12 py-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">

          {/* 브랜드 */}
          <div className="flex items-center gap-2.5">
            <div className="w-6 h-6 rounded-md bg-[#1a1c1b] flex items-center justify-center">
              <FileText size={12} className="text-white" strokeWidth={2.2} />
            </div>
            <span className="text-sm font-extrabold tracking-tighter text-[#1a1c1b]">Eazy HWPX</span>
          </div>

          {/* 신뢰 배지 */}
          <div className="flex items-center gap-6 text-xs font-medium text-[#57423c]/70">
            <span className="flex items-center gap-1.5">
              <Shield size={12} /> 파일 3시간 후 자동 삭제
            </span>
            <span className="flex items-center gap-1.5">
              <Shield size={12} /> 광고 없음
            </span>
            <span className="flex items-center gap-1.5">
              <Shield size={12} /> 개인정보 최소 수집
            </span>
          </div>

          {/* 법적 링크 */}
          <div className="flex items-center gap-4 text-xs font-medium text-[#57423c]/70">
            <Link href="/terms" className="hover:text-[#1a1c1b] transition-colors">이용약관</Link>
            <span>·</span>
            <Link href="/privacy" className="hover:text-[#1a1c1b] transition-colors">개인정보처리방침</Link>
            <span>·</span>
            <a href="mailto:eazypick.service@gmail.com" className="hover:text-[#1a1c1b] transition-colors">문의</a>
          </div>
        </div>

        <div className="mt-6 pt-5 border-t border-gray-100 text-center text-xs text-[#57423c]/65">
          © 2025 Eazy HWPX. HWP·HWPX는 한글과컴퓨터의 등록상표입니다.
        </div>
      </div>
    </footer>
  );
}
