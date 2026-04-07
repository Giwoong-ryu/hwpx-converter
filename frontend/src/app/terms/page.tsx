import Link from "next/link";
import { FileText } from "lucide-react";

export const metadata = {
  title: "이용약관 | Eazy HWPX",
  description: "Eazy HWPX 서비스 이용약관",
};

const SECTIONS = [
  {
    title: "제1조 (목적)",
    body: `이 약관은 Eazy HWPX(이하 "서비스")가 제공하는 HWP·HWPX 문서 처리 및 AI 자동 완성 서비스의 이용 조건과 절차에 관한 사항을 규정합니다.`,
  },
  {
    title: "제2조 (서비스 내용)",
    body: `서비스는 다음 기능을 제공합니다.
• HWP·HWPX·DOCX 파일 형식 변환
• 문서 내 표 데이터 엑셀 추출
• AI를 활용한 양식 자동 채우기 및 내용 생성
• 도장 이미지 삽입, 문서 합치기, 엑셀 일괄 생성

AI 기능은 Gemini API를 통해 제공되며 응답 품질은 입력 내용에 따라 달라질 수 있습니다.`,
  },
  {
    title: "제3조 (파일 처리 방침)",
    body: `업로드된 파일은 서비스 처리 목적으로만 사용됩니다.
• 모든 업로드 파일은 처리 완료 후 3시간 이내에 서버에서 자동 삭제됩니다.
• 파일 내용은 AI 학습 데이터로 사용되지 않습니다.
• 서비스는 파일 내용을 제3자에게 제공하지 않습니다.`,
  },
  {
    title: "제4조 (요금 및 결제)",
    body: `서비스는 무료 기능과 유료 AI 기능으로 구분됩니다.
• 무료: 파일 변환, 엑셀 추출, 도장, 합치기 기능
• 유료: AI 자동 채우기 및 생성 기능 (게이지 충전 방식)
결제는 Polar(polar.sh)를 통해 처리되며, 결제 시 Polar 이용약관도 함께 적용됩니다.`,
  },
  {
    title: "제5조 (환불 정책)",
    body: `다음 조건을 모두 충족하는 경우 전액 환불이 가능합니다.
• 결제일로부터 7일 이내
• AI 기능(게이지)을 사용하지 않은 경우

환불 요청은 support@eazyhwpx.kr 로 이메일 문의해주세요. 영업일 기준 3일 이내 처리합니다.`,
  },
  {
    title: "제6조 (이용 제한)",
    body: `다음 행위는 금지됩니다.
• 서비스를 통해 타인의 저작권을 침해하는 파일 처리
• 악성 코드가 포함된 파일 업로드
• 자동화 프로그램을 이용한 대량 요청 (API 직접 호출)
• 타인의 계정 정보 도용`,
  },
  {
    title: "제7조 (책임 제한)",
    body: `서비스는 AI 기능의 결과물 정확성을 보장하지 않습니다. AI가 생성한 내용은 반드시 사용자가 검토 후 사용해주세요.
서비스 장애, 데이터 손실 등 불가항력적인 사유로 인한 손해에 대해 서비스는 책임을 지지 않습니다.`,
  },
  {
    title: "제8조 (약관 변경)",
    body: `약관이 변경될 경우 변경 7일 전 서비스 내 공지사항 또는 이메일로 안내합니다. 변경된 약관에 동의하지 않는 경우 서비스 이용을 중단하고 탈퇴할 수 있습니다.`,
  },
];

export default function TermsPage() {
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
          <span className="text-sm text-[#57423c]/40">/</span>
          <span className="text-sm text-[#57423c]/60">이용약관</span>
        </div>
      </nav>

      <main className="pt-24 pb-20 max-w-2xl mx-auto px-8">
        <h1 className="text-3xl font-extrabold tracking-tight mb-2">이용약관</h1>
        <p className="text-sm text-[#57423c]/40 mb-10">최종 업데이트: 2025년 1월 1일</p>

        <div className="space-y-8">
          {SECTIONS.map((s) => (
            <section key={s.title}>
              <h2 className="text-base font-bold text-[#1a1c1b] mb-3">{s.title}</h2>
              <p className="text-sm text-[#57423c]/70 leading-relaxed whitespace-pre-line">{s.body}</p>
            </section>
          ))}
        </div>

        <div className="mt-12 pt-8 border-t border-gray-200/60 flex gap-6 text-sm text-[#57423c]/40">
          <Link href="/privacy" className="hover:text-[#1a1c1b] transition-colors">개인정보처리방침</Link>
          <Link href="/" className="hover:text-[#1a1c1b] transition-colors">홈으로</Link>
        </div>
      </main>
    </div>
  );
}
