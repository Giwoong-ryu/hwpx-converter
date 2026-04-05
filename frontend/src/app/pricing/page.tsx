"use client";

import { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import Link from "next/link";
import { FileText, ArrowDown, Check, Shield, Zap, Crown, ChevronDown, Gift, Flame, Trophy, Star } from "lucide-react";

const PLUS_ID = "307b2685-27de-4b96-ac7d-670a669c85d8";
const PRO_ID = "fe4b5d80-c912-403b-b940-58b4c50bb6b8";

export default function PricingPage() {
  const { user, accessToken } = useAuth();
  const [purchasing, setPurchasing] = useState<string | null>(null);
  const [showLogin, setShowLogin] = useState(false);

  async function handlePurchase(productId: string) {
    if (!user || !accessToken) {
      setShowLogin(true);
      return;
    }
    setPurchasing(productId);
    try {
      const API = process.env.NEXT_PUBLIC_API_URL || "/api";
      const res = await fetch(`${API}/payment/checkout`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${accessToken}` },
        body: JSON.stringify({ product_id: productId }),
      });
      const data = await res.json();
      if (data.checkout_url) window.location.href = data.checkout_url;
      else alert("결제 페이지를 열 수 없습니다.");
    } catch { alert("결제 처리 중 오류가 발생했습니다."); }
    finally { setPurchasing(null); }
  }

  return (
    <div className="min-h-screen bg-[#f9f9f6] text-[#1a1c1b]">

      {/* ── 네비게이션 ── */}
      <nav className="fixed top-0 w-full z-50 bg-[#f9f9f6]/80 backdrop-blur-xl border-b border-[#BFDBFE]/40">
        <div className="flex justify-between items-center px-8 lg:px-12 py-4 max-w-screen-2xl mx-auto">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-[#1a1c1b] flex items-center justify-center">
              <FileText size={14} className="text-white" strokeWidth={2.2} />
            </div>
            <span className="text-lg font-extrabold tracking-tighter">Eazy HWPX</span>
          </Link>
          <div className="flex items-center gap-6">
            <Link href="/tool" className="text-sm text-[#57423c]/70 hover:text-[#1a1c1b] transition-colors">도구</Link>
            {user ? (
              <span className="text-sm text-[#57423c]/50">{user.email}</span>
            ) : (
              <Link href="/tool" className="bg-gradient-to-r from-[#2563EB] to-[#1E40AF] text-white px-5 py-2 rounded-lg font-semibold text-sm hover:opacity-90 transition-all active:scale-95">
                무료로 시작하기
              </Link>
            )}
          </div>
        </div>
      </nav>

      <main className="pt-32 pb-20 max-w-screen-xl mx-auto px-8 lg:px-12">

        {/* ── 헤드라인 ── */}
        <div className="text-center mb-16">
          <h1 className="text-[2.2rem] lg:text-[2.8rem] font-extrabold leading-[1.15] tracking-tight mb-4">
            문서 변환/추출은 <span className="text-[#2563EB]">무료</span>.<br />
            AI 자동 작성만 유료입니다.
          </h1>
          <p className="text-base text-[#57423c]/60 max-w-lg mx-auto mb-6">
            광고 없음. 파일은 처리 후 즉시 삭제. 로그인 없이도 사용 가능.
          </p>
          <button onClick={() => document.getElementById("plans")?.scrollIntoView({ behavior: "smooth" })}
            className="inline-flex items-center gap-1 text-sm text-[#2563EB] hover:underline">
            요금제 비교 보기 <ArrowDown size={14} />
          </button>
        </div>

        {/* ── 가격 카드 3열 ── */}
        <div id="plans" className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto mb-12">

          {/* Free */}
          <div className="bg-white rounded-2xl border border-gray-200/80 p-8 flex flex-col">
            <div className="text-xs font-bold text-[#57423c]/30 uppercase tracking-widest mb-4">Free</div>
            <div className="text-3xl font-black tracking-tight mb-1">0원</div>
            <p className="text-sm text-[#57423c]/40 mb-8">가입 없이도 바로 사용</p>
            <ul className="space-y-3 mb-8 flex-1 text-sm">
              <Li text="HWP/HWPX/DOCX 변환 무제한" />
              <Li text="문서 → 엑셀 추출 무제한" />
              <Li text="문서 합치기 / 도장 무제한" />
              <Li text="AI 매핑 하루 3회" />
              <Li text="AI 작성 하루 1회 (+재시도)" />
              <Li text="내 정보 프리셋 1개" />
            </ul>
            <Link href="/tool" className="block text-center py-3 rounded-xl border-2 border-gray-200 text-[#1a1c1b] font-bold text-sm hover:border-[#1a1c1b] transition-colors">
              무료로 시작하기
            </Link>
          </div>

          {/* Plus */}
          <div className="bg-white rounded-2xl border-2 border-[#2563EB] p-8 flex flex-col relative shadow-[0_4px_32px_rgba(37,99,235,0.08)]">
            <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-[#2563EB] text-white text-[11px] font-bold px-4 py-1 rounded-full tracking-wide">
              오픈 특가
            </div>
            <div className="text-xs font-bold text-[#2563EB]/60 uppercase tracking-widest mb-4 flex items-center gap-1.5">
              <Zap size={12} /> Plus
            </div>
            <div className="text-3xl font-black tracking-tight mb-1">4,900원</div>
            <p className="text-sm text-[#2563EB] font-medium mb-2">첫 구매 시 사용량 2배 충전</p>
            <p className="text-xs text-[#57423c]/40 mb-6">한번 결제, 기간 만료 없이 사용. 부족하면 추가 구매.</p>
            <ul className="space-y-3 mb-8 flex-1 text-sm">
              <Li text="무료 기능 전부 포함" />
              <Li text="AI 사용량 게이지 충전" highlight />
              <Li text="첫 구매 2배 충전 (200%)" highlight />
              <Li text="대량 생성 30건" highlight />
              <Li text="내 정보 프리셋 3개" highlight />
              <Li text="양식 매핑 10개 저장" highlight />
              <Li text="기간 만료 없음" highlight />
            </ul>
            <button
              onClick={() => handlePurchase(PLUS_ID)}
              disabled={purchasing === PLUS_ID}
              className="w-full py-3 rounded-xl bg-gradient-to-r from-[#2563EB] to-[#1E40AF] text-white font-bold text-sm hover:opacity-90 transition-all active:scale-[0.98] disabled:opacity-50"
            >
              {purchasing === PLUS_ID ? "처리 중..." : "4,900원으로 시작하기"}
            </button>
          </div>

          {/* Pro */}
          <div className="bg-white rounded-2xl border border-gray-200/80 p-8 flex flex-col">
            <div className="text-xs font-bold text-[#57423c]/30 uppercase tracking-widest mb-4 flex items-center gap-1.5">
              <Crown size={12} /> Pro
            </div>
            <div className="text-3xl font-black tracking-tight mb-1">9,900원<span className="text-base font-normal text-[#57423c]/30">/월</span></div>
            <p className="text-sm text-[#57423c]/50 mb-2">AI 무제한, 횟수 걱정 없이</p>
            <p className="text-xs text-[#57423c]/40 mb-6">매주 자동 리셋. 오픈 특가 가입 시 영구 적용.</p>
            <ul className="space-y-3 mb-8 flex-1 text-sm">
              <Li text="무료 기능 전부 포함" />
              <Li text="AI 매핑/작성 무제한" highlight />
              <Li text="매주 게이지 자동 리셋" highlight />
              <Li text="대량 생성 200건" highlight />
              <Li text="내 정보 프리셋 무제한" highlight />
              <Li text="양식 매핑 무제한 저장" highlight />
              <Li text="스트릭 프리즈 주 2회" highlight />
            </ul>
            <button
              onClick={() => handlePurchase(PRO_ID)}
              disabled={purchasing === PRO_ID}
              className="w-full py-3 rounded-xl border-2 border-[#1a1c1b] text-[#1a1c1b] font-bold text-sm hover:bg-[#1a1c1b] hover:text-white transition-all active:scale-[0.98] disabled:opacity-50"
            >
              {purchasing === PRO_ID ? "처리 중..." : "프로 구독 시작하기"}
            </button>
          </div>
        </div>

        {/* 스크롤 힌트 */}
        <div className="text-center mb-20">
          <button onClick={() => document.getElementById("rewards")?.scrollIntoView({ behavior: "smooth" })}
            className="inline-flex flex-col items-center gap-1 text-xs text-[#57423c]/30 hover:text-[#57423c]/50 transition-colors">
            <span>쓸수록 보상이 쌓입니다</span>
            <ChevronDown size={16} className="animate-bounce" />
          </button>
        </div>

        {/* ── 보상 체계 ── */}
        <div id="rewards" className="mb-24">
          <h2 className="text-xl font-extrabold tracking-tight text-center mb-2">쓸수록 돌아오는 보상</h2>
          <p className="text-sm text-[#57423c]/40 text-center mb-10">문서를 완성할 때마다 보너스 사용량이 충전됩니다</p>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-5 max-w-4xl mx-auto">
            <RewardCard
              icon={<Trophy size={20} />}
              title="업적 보상"
              desc="첫 문서 +25%, 5건 +50%, 10건 +50%"
              color="blue"
            />
            <RewardCard
              icon={<Flame size={20} />}
              title="연속 사용 보너스"
              desc="3일 +10%, 7일 +25%, 30일 +50%"
              color="orange"
            />
            <RewardCard
              icon={<Star size={20} />}
              title="럭키 보너스"
              desc="문서 완성마다 랜덤 보상 찬스"
              color="yellow"
            />
            <RewardCard
              icon={<Gift size={20} />}
              title="추천 보상"
              desc="친구 초대 시 서로 +50%"
              color="green"
            />
          </div>
        </div>

        {/* ── 단계 ── */}
        <div className="mb-24 max-w-3xl mx-auto">
          <h2 className="text-xl font-extrabold tracking-tight text-center mb-8">쓸수록 단계가 올라요</h2>
          <div className="flex items-center justify-between gap-2">
            {[
              { lv: 1, title: "복붙 탈출", medal: "참가", docs: "0건", color: "text-gray-400", bg: "bg-gray-100" },
              { lv: 2, title: "자동화 입문", medal: "동메달", docs: "5건", color: "text-amber-700", bg: "bg-amber-50" },
              { lv: 3, title: "칼퇴 요정", medal: "은메달", docs: "20건", color: "text-slate-400", bg: "bg-slate-50" },
              { lv: 4, title: "팀 에이스", medal: "금메달", docs: "50건", color: "text-yellow-500", bg: "bg-yellow-50" },
              { lv: 5, title: "자동화의 신", medal: "트로피", docs: "100건", color: "text-amber-500", bg: "bg-amber-50" },
            ].map((l, i) => (
              <div key={l.lv} className="flex flex-col items-center gap-1.5 flex-1">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center ${l.bg} ${l.color}`}>
                  {l.lv}
                </div>
                <span className="text-xs font-bold text-[#1a1c1b]">{l.title}</span>
                <span className={`text-[9px] ${l.color}`}>{l.medal}</span>
                <span className="text-[10px] text-[#57423c]/30">{l.docs}</span>
                {i < 4 && l.lv > 1 && <span className="text-[10px] text-[#2563EB]">+{l.lv === 2 ? "25" : "50"}%</span>}
              </div>
            ))}
          </div>
        </div>

        {/* ── 시간 환산 ── */}
        <div className="mb-24">
          <h2 className="text-xl font-extrabold tracking-tight text-center mb-2">같은 서류, 이만큼 차이납니다</h2>
          <p className="text-sm text-[#57423c]/40 text-center mb-8">사업계획서 1건 기준</p>
          <div className="grid md:grid-cols-3 gap-6 max-w-3xl mx-auto">
            <TimeCard label="직접 작성" time="3~5시간" sub="시급 환산 약 45,000원" />
            <TimeCard label="외주 대행" time="3~7일" sub="30~100만원" />
            <TimeCard label="Eazy HWPX" time="3분" sub="4,900원이면 여러 건 가능" highlight />
          </div>
        </div>

        {/* ── 경쟁사 비교 ── */}
        <div className="mb-24">
          <h2 className="text-xl font-extrabold tracking-tight text-center mb-2">다른 서비스와 비교</h2>
          <p className="text-xs text-[#57423c]/30 text-center mb-8">2026년 4월 각 서비스 공식 가격 기준</p>
          <div className="bg-white rounded-2xl border border-gray-200/80 overflow-hidden max-w-3xl mx-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="text-left p-5 font-normal text-[#57423c]/30"></th>
                  <th className="p-5 font-extrabold text-[#2563EB]">Eazy HWPX</th>
                  <th className="p-5 font-normal text-[#57423c]/30">AI 문서 서비스 A</th>
                  <th className="p-5 font-normal text-[#57423c]/30">전자서식 서비스 B</th>
                </tr>
              </thead>
              <tbody>
                <CRow label="AI 작성 가격" v1="4,900원 (1회 결제)" v2="29,900원 (매달)" v3="~24,000원 (매달)" />
                <CRow label="한글 프로그램 설치" v1="필요 없음" v2="필수 (별도 구매)" v3="필요 없음" />
                <CRow label="Mac / 모바일" v1="가능" v2="Windows만" v3="가능" />
                <CRow label="대량 문서 생성" v1="포함" v2="미지원" v3="건당 과금" />
                <CRow label="문서 → 엑셀 추출" v1="무료" v2="미지원" v3="미지원" />
                <CRow label="기간 만료" v1="만료 없음" v2="해지 시 소멸" v3="해지 시 소멸" />
              </tbody>
            </table>
          </div>
        </div>

        {/* ── FAQ ── */}
        <div className="mb-16">
          <h2 className="text-xl font-extrabold tracking-tight text-center mb-8">자주 묻는 질문</h2>
          <div className="max-w-2xl mx-auto space-y-3">
            <FAQ q="한글 프로그램 없어도 사용할 수 있나요?" a="네. 브라우저만 있으면 됩니다. Mac, 태블릿, 모바일에서도 사용 가능합니다." />
            <FAQ q="Plus 사용량이 만료되나요?" a="만료되지 않습니다. 구매한 사용량은 모두 사용할 때까지 유지됩니다." />
            <FAQ q="첫 구매 2배는 처음만 적용되나요?" a="네. 첫 구매에만 200% 충전되고, 이후 구매는 100% 충전됩니다." />
            <FAQ q="Pro를 해지하면?" a="다음 결제일까지 사용 가능합니다. 이후 무료로 자동 전환됩니다." />
            <FAQ q="내 파일이 저장되나요?" a="파일 자체는 처리 후 30분 내 자동 삭제됩니다. 내 정보 프리셋과 매핑 기록만 안전하게 저장됩니다." />
            <FAQ q="환불 가능한가요?" a="구매 후 7일 내 미사용 시 전액 환불 가능합니다." />
            <FAQ q="보상은 어떻게 받나요?" a="문서를 완성하면 자동으로 적용됩니다. 업적, 연속 사용, 럭키 보너스가 게이지에 추가됩니다." />
          </div>
        </div>

        {/* ── 신뢰 ── */}
        <div className="flex items-center justify-center gap-8 text-xs text-[#57423c]/30 pt-8 border-t border-gray-200/60">
          <span className="flex items-center gap-1.5"><Shield size={12} /> 광고 없음</span>
          <span className="flex items-center gap-1.5"><Shield size={12} /> 파일 즉시 삭제</span>
          <span className="flex items-center gap-1.5"><Shield size={12} /> 로그인 없이 사용 가능</span>
        </div>
      </main>

      {showLogin && <LoginModal onClose={() => setShowLogin(false)} />}
    </div>
  );
}

/* ── 컴포넌트 ── */

function Li({ text, highlight }: { text: string; highlight?: boolean }) {
  return (
    <li className="flex items-start gap-2.5">
      <Check className={`w-4 h-4 mt-0.5 shrink-0 ${highlight ? "text-[#2563EB]" : "text-[#2563EB]/40"}`} />
      <span className={highlight ? "text-[#1a1c1b] font-medium" : "text-[#57423c]/70"}>{text}</span>
    </li>
  );
}

function RewardCard({ icon, title, desc, color }: { icon: React.ReactNode; title: string; desc: string; color: string }) {
  const colors: Record<string, string> = {
    blue: "bg-[#DBEAFE] text-[#1E40AF]",
    orange: "bg-orange-50 text-orange-600",
    yellow: "bg-amber-50 text-amber-600",
    green: "bg-emerald-50 text-emerald-600",
  };
  return (
    <div className="bg-white rounded-xl border border-gray-200/80 p-5">
      <div className={`w-9 h-9 rounded-lg flex items-center justify-center mb-3 ${colors[color]}`}>{icon}</div>
      <p className="font-bold text-sm text-[#1a1c1b] mb-1">{title}</p>
      <p className="text-xs text-[#57423c]/50 leading-relaxed">{desc}</p>
    </div>
  );
}

function TimeCard({ label, time, sub, highlight }: { label: string; time: string; sub: string; highlight?: boolean }) {
  return (
    <div className={`rounded-2xl p-6 text-center ${highlight ? "bg-[#2563EB] text-white" : "bg-white border border-gray-200/80"}`}>
      <p className={`text-sm mb-3 ${highlight ? "text-white/70" : "text-[#57423c]/40"}`}>{label}</p>
      <p className="text-2xl font-black tracking-tight mb-1">{time}</p>
      <p className={`text-xs ${highlight ? "text-white/50" : "text-[#57423c]/30"}`}>{sub}</p>
    </div>
  );
}

function CRow({ label, v1, v2, v3 }: { label: string; v1: string; v2: string; v3: string }) {
  return (
    <tr className="border-t border-gray-50">
      <td className="p-5 text-[#57423c]/50">{label}</td>
      <td className="p-5 text-center font-bold text-[#1a1c1b]">{v1}</td>
      <td className="p-5 text-center text-[#57423c]/25">{v2}</td>
      <td className="p-5 text-center text-[#57423c]/25">{v3}</td>
    </tr>
  );
}

function FAQ({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="bg-white rounded-xl border border-gray-200/80 overflow-hidden">
      <button onClick={() => setOpen(!open)} className="w-full p-5 flex items-center justify-between text-left">
        <span className="font-bold text-sm text-[#1a1c1b]">{q}</span>
        <ChevronDown size={16} className={`text-[#57423c]/30 transition-transform shrink-0 ml-4 ${open ? "rotate-180" : ""}`} />
      </button>
      {open && <p className="px-5 pb-5 text-sm text-[#57423c]/50 leading-relaxed -mt-1">{a}</p>}
    </div>
  );
}

function LoginModal({ onClose }: { onClose: () => void }) {
  const { signIn, signUp, signInWithProvider } = useAuth();
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    const result = mode === "login" ? await signIn(email, password) : await signUp(email, password, name);
    if (result.error) setError(result.error);
    else onClose();
    setLoading(false);
  }

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-[100] flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-[#f9f9f6] rounded-2xl p-8 w-full max-w-sm border border-gray-200/80" onClick={(e) => e.stopPropagation()}>
        <h2 className="text-xl font-extrabold tracking-tight mb-6">
          {mode === "login" ? "로그인" : "회원가입"}
        </h2>
        <div className="space-y-3 mb-6">
          <button onClick={() => signInWithProvider("google")}
            className="w-full py-3 rounded-xl border border-gray-200 text-[#1a1c1b] font-medium text-sm hover:bg-white transition-colors">
            Google로 계속
          </button>
          <button onClick={() => signInWithProvider("kakao")}
            className="w-full py-3 rounded-xl bg-[#FEE500] text-[#191919] font-medium text-sm hover:brightness-95 transition-all">
            카카오로 계속
          </button>
        </div>
        <div className="flex items-center gap-4 mb-6">
          <div className="flex-1 h-px bg-gray-200" />
          <span className="text-xs text-[#57423c]/30">또는</span>
          <div className="flex-1 h-px bg-gray-200" />
        </div>
        <form onSubmit={handleSubmit} className="space-y-3">
          {mode === "signup" && (
            <input type="text" placeholder="이름" value={name} onChange={(e) => setName(e.target.value)}
              className="w-full px-4 py-3 rounded-xl border border-gray-200 bg-white text-sm focus:border-[#1a1c1b] focus:outline-none" />
          )}
          <input type="email" placeholder="이메일" value={email} onChange={(e) => setEmail(e.target.value)} required
            className="w-full px-4 py-3 rounded-xl border border-gray-200 bg-white text-sm focus:border-[#1a1c1b] focus:outline-none" />
          <input type="password" placeholder="비밀번호" value={password} onChange={(e) => setPassword(e.target.value)} required
            className="w-full px-4 py-3 rounded-xl border border-gray-200 bg-white text-sm focus:border-[#1a1c1b] focus:outline-none" />
          {error && <p className="text-xs text-red-500">{error}</p>}
          <button type="submit" disabled={loading}
            className="w-full py-3 rounded-xl bg-[#1a1c1b] text-white font-bold text-sm hover:bg-black transition-colors disabled:opacity-50">
            {loading ? "처리 중..." : mode === "login" ? "로그인" : "가입하기"}
          </button>
        </form>
        <p className="text-xs text-[#57423c]/40 text-center mt-4">
          {mode === "login" ? (
            <>계정이 없으신가요? <button onClick={() => setMode("signup")} className="text-[#1a1c1b] font-bold">회원가입</button></>
          ) : (
            <>이미 계정이 있으신가요? <button onClick={() => setMode("login")} className="text-[#1a1c1b] font-bold">로그인</button></>
          )}
        </p>
      </div>
    </div>
  );
}
