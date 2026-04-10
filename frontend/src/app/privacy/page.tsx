import Link from "next/link";
import { FileText } from "lucide-react";

export const metadata = {
  title: "개인정보처리방침 | Eazy HWPX",
  description: "Eazy HWPX 개인정보처리방침",
};

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-[#f9f9f6] text-[#1a1c1b]">
      <nav className="fixed top-0 w-full z-50 bg-[#f9f9f6]/80 backdrop-blur-xl border-b border-gray-200/40">
        <div className="flex items-center gap-3 px-8 py-4 max-w-screen-xl mx-auto">
          <Link href="/" className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-md bg-[#1a1c1b] flex items-center justify-center">
              <FileText size={12} className="text-white" strokeWidth={2.2} />
            </div>
            <span className="text-sm font-extrabold tracking-tighter">Eazy HWPX</span>
          </Link>
          <span className="text-sm text-[#57423c]/60">/</span>
          <span className="text-sm text-[#57423c]/60">개인정보처리방침</span>
        </div>
      </nav>

      <main className="pt-24 pb-20 max-w-2xl mx-auto px-8">
        <h1 className="text-3xl font-extrabold tracking-tight mb-2">개인정보처리방침</h1>
        <p className="text-sm text-[#57423c]/60 mb-10">최종 업데이트: 2025년 1월 1일</p>

        <div className="space-y-8 text-sm text-[#57423c]/70 leading-relaxed">

          {/* 핵심 원칙 */}
          <div className="bg-[#EFF6FF] rounded-2xl p-6">
            <h2 className="text-base font-bold text-[#1E40AF] mb-3">핵심 원칙</h2>
            <ul className="space-y-2">
              <li>• 업로드된 파일은 <strong className="text-[#1a1c1b]">처리 후 3시간 이내</strong> 서버에서 자동 삭제됩니다.</li>
              <li>• 파일 내용은 AI 모델 학습에 사용되지 않습니다.</li>
              <li>• 로그인 없이 사용 시 어떠한 개인정보도 수집하지 않습니다.</li>
              <li>• 광고 목적으로 개인정보를 활용하지 않습니다.</li>
            </ul>
          </div>

          <section>
            <h2 className="text-base font-bold text-[#1a1c1b] mb-3">제1조 (수집하는 개인정보)</h2>
            <p className="mb-3">회원가입 시에만 아래 정보를 수집합니다. 비회원은 어떠한 정보도 수집하지 않습니다.</p>
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="bg-gray-50">
                  <th className="text-left p-3 border border-gray-200 font-semibold text-[#1a1c1b]">항목</th>
                  <th className="text-left p-3 border border-gray-200 font-semibold text-[#1a1c1b]">필수/선택</th>
                  <th className="text-left p-3 border border-gray-200 font-semibold text-[#1a1c1b]">목적</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className="p-3 border border-gray-200">이메일 주소</td>
                  <td className="p-3 border border-gray-200">필수</td>
                  <td className="p-3 border border-gray-200">계정 식별, 결제 처리</td>
                </tr>
                <tr>
                  <td className="p-3 border border-gray-200">이름</td>
                  <td className="p-3 border border-gray-200">선택</td>
                  <td className="p-3 border border-gray-200">서비스 이용 편의</td>
                </tr>
                <tr>
                  <td className="p-3 border border-gray-200">소셜 로그인 식별자</td>
                  <td className="p-3 border border-gray-200">선택</td>
                  <td className="p-3 border border-gray-200">Google/카카오 연동 시</td>
                </tr>
              </tbody>
            </table>
          </section>

          <section>
            <h2 className="text-base font-bold text-[#1a1c1b] mb-3">제2조 (업로드 파일 처리)</h2>
            <p>업로드된 파일은 개인정보가 아니며, 아래 원칙에 따라 처리됩니다.</p>
            <ul className="mt-3 space-y-1.5">
              <li>• 처리 목적: 변환, 추출, AI 자동 완성 작업 수행</li>
              <li>• 보관 기간: 처리 완료 후 최대 3시간. 이후 자동 삭제.</li>
              <li>• 제3자 제공: 없음 (AI 처리를 위한 Gemini API 전송 포함, 해당 데이터는 Google이 학습에 사용하지 않도록 설정됨)</li>
              <li>• 파일 내용은 서버 로그에 저장되지 않습니다.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-base font-bold text-[#1a1c1b] mb-3">제3조 (보관 기간)</h2>
            <ul className="space-y-1.5">
              <li>• 회원 탈퇴 시: 즉시 삭제 (단, 결제 관련 기록은 전자상거래법에 따라 5년 보관)</li>
              <li>• 비활성 계정: 마지막 로그인 후 3년 경과 시 자동 삭제</li>
            </ul>
          </section>

          <section>
            <h2 className="text-base font-bold text-[#1a1c1b] mb-3">제4조 (처리 위탁)</h2>
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="bg-gray-50">
                  <th className="text-left p-3 border border-gray-200 font-semibold text-[#1a1c1b]">수탁업체</th>
                  <th className="text-left p-3 border border-gray-200 font-semibold text-[#1a1c1b]">위탁 업무</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className="p-3 border border-gray-200">Supabase Inc.</td>
                  <td className="p-3 border border-gray-200">회원 인증 및 계정 정보 저장</td>
                </tr>
                <tr>
                  <td className="p-3 border border-gray-200">Railway Corp.</td>
                  <td className="p-3 border border-gray-200">서버 인프라 운영 (파일 임시 처리)</td>
                </tr>
                <tr>
                  <td className="p-3 border border-gray-200">Polar.sh</td>
                  <td className="p-3 border border-gray-200">결제 처리 (이메일, 결제 정보)</td>
                </tr>
                <tr>
                  <td className="p-3 border border-gray-200">Google LLC</td>
                  <td className="p-3 border border-gray-200">AI 기능 (Gemini API), 소셜 로그인</td>
                </tr>
              </tbody>
            </table>
          </section>

          <section>
            <h2 className="text-base font-bold text-[#1a1c1b] mb-3">제5조 (이용자 권리)</h2>
            <p>이용자는 언제든지 아래 권리를 행사할 수 있습니다.</p>
            <ul className="mt-3 space-y-1.5">
              <li>• 개인정보 열람 요청</li>
              <li>• 개인정보 수정·삭제 요청</li>
              <li>• 회원 탈퇴 (마이페이지 → 계정 삭제)</li>
              <li>• 위 요청은 <a href="mailto:eazypick.service@gmail.com" className="text-[#2563EB] hover:underline">eazypick.service@gmail.com</a>으로 이메일 문의해주세요.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-base font-bold text-[#1a1c1b] mb-3">제6조 (쿠키)</h2>
            <p>서비스는 로그인 상태 유지를 위해 세션 쿠키를 사용합니다. 브라우저 설정에서 쿠키를 거부할 수 있으나, 일부 기능이 제한될 수 있습니다.</p>
          </section>

          <section>
            <h2 className="text-base font-bold text-[#1a1c1b] mb-3">문의</h2>
            <p>개인정보 관련 문의: <a href="mailto:eazypick.service@gmail.com" className="text-[#2563EB] hover:underline">eazypick.service@gmail.com</a></p>
          </section>

        </div>

        <div className="mt-12 pt-8 border-t border-gray-200/60 flex gap-6 text-sm text-[#57423c]/60">
          <Link href="/terms" className="hover:text-[#1a1c1b] transition-colors">이용약관</Link>
          <Link href="/" className="hover:text-[#1a1c1b] transition-colors">홈으로</Link>
        </div>
      </main>
    </div>
  );
}
