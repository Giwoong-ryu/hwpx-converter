"use client";

import { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import Link from "next/link";
import { FileText, Check, Shield, Zap, Crown, ChevronDown, Gift, Flame, Trophy, Star } from "lucide-react";

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

      <main className="pt-20 pb-20 max-w-screen-xl mx-auto px-8 lg:px-12">

        {/* ── 헤드라인 ── */}
        <div className="text-center mb-8">
          <h1 className="text-[2rem] lg:text-[2.4rem] font-extrabold leading-[1.15] tracking-tight mb-2">
            문서 변환/추출은 <span className="text-[#2563EB]">무료</span>.<br />
            AI 자동 작성만 유료입니다.
          </h1>
          <p className="text-sm text-[#57423c]/60 max-w-lg mx-auto">
            광고 없음. 파일은 처리 후 즉시 삭제. 로그인 없이도 사용 가능.
          </p>
        </div>

        {/* ── 가격 카드 3열 ── */}
        <div id="plans" className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto mb-12">

          {/* Free */}
          <div className="bg-white rounded-2xl border border-gray-200/80 p-8 flex flex-col">
            <div className="text-xs font-bold text-[#57423c]/30 uppercase tracking-widest mb-4">Free</div>
            <div className="text-3xl font-black tracking-tight mb-1">0원</div>
            <p className="text-base text-[#57423c]/40 mb-8">가입 없이도 바로 사용</p>
            <ul className="space-y-3 mb-8 flex-1 text-sm">
              <Li text="HWP/HWPX/DOCX 변환 무제한" />
              <Li text="문서 → 엑셀 추출 무제한" />
              <Li text="문서 합치기 / 도장 무제한" />
              <Li text="AI 매핑 하루 3회" />
              <Li text="AI 작성 하루 1회 (+재시도)" />
              <Li text="내 정보 미리 저장 1개" />
            </ul>
            <Link href="/tool" className="block text-center py-3 rounded-xl border-2 border-gray-200 text-[#1a1c1b] font-bold text-sm hover:border-[#1a1c1b] transition-colors">
              무료로 시작하기
            </Link>
          </div>

          {/* Plus */}
          <div className="bg-white rounded-2xl border-2 border-[#2563EB] p-8 flex flex-col relative shadow-[0_4px_32px_rgba(37,99,235,0.08)]">
            <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-[#2563EB] text-white text-xs font-bold px-4 py-1 rounded-full tracking-wide">
              오픈 특가
            </div>
            <div className="text-xs font-bold text-[#2563EB]/60 uppercase tracking-widest mb-4 flex items-center gap-1.5">
              <Zap size={12} /> Plus
            </div>
            <div className="text-3xl font-black tracking-tight mb-1">4,900원</div>
            <p className="text-base text-[#2563EB] font-medium mb-2">첫 구매 시 사용량 2배 충전</p>
            <p className="text-sm text-[#57423c]/40 mb-6">한번 결제, 기간 만료 없이 사용. 부족하면 추가 구매.</p>
            <ul className="space-y-3 mb-8 flex-1 text-sm">
              <Li text="무료 기능 전부 포함" />
              <Li text="AI 사용량 충전" highlight />
              <Li text="첫 구매 2배 충전 (200%)" highlight />
              <Li text="대량 생성 30건" highlight />
              <Li text="내 정보 미리 저장 3개" highlight />
              <Li text="자주 쓰는 양식 10개 저장" highlight />
              <Li text="다 쓸 때까지 사라지지 않아요" highlight />
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
            <p className="text-base text-[#57423c]/50 mb-2">AI 무제한, 횟수 걱정 없이</p>
            <p className="text-sm text-[#57423c]/40 mb-6">매주 자동 리셋. 오픈 특가 가입 시 영구 적용.</p>
            <ul className="space-y-3 mb-8 flex-1 text-sm">
              <Li text="무료 기능 전부 포함" />
              <Li text="AI 매핑/작성 무제한" highlight />
              <Li text="매주 게이지 자동 리셋" highlight />
              <Li text="대량 생성 200건" highlight />
              <Li text="내 정보 미리 저장 무제한" highlight />
              <Li text="자주 쓰는 양식 무제한 저장" highlight />
              <Li text="며칠 못 써도 연속 기록 유지 (주 2회)" highlight />
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

        {/* ── 쓸수록 혜택이 쌓여요 ── */}
        <div className="mb-20 max-w-2xl mx-auto mt-12">
          <h2 className="text-xl font-extrabold tracking-tight text-center mb-2">쓸수록 혜택이 쌓여요</h2>
          <p className="text-sm text-[#57423c]/50 text-center mb-8">문서를 만들 때마다 보너스 사용량이 자동으로 충전돼요</p>

          <div className="space-y-4">
            <Step emoji={<Trophy size={18} className="text-[#2563EB]" />} title="첫 문서를 완성하면" desc="보너스 +25%가 바로 충전돼요." />
            <Step emoji={<Flame size={18} className="text-orange-500" />} title="매일 사용하면" desc="3일째부터 연속 사용 보너스가 쌓여요. 7일, 30일까지 보너스가 커져요." />
            <Step emoji={<Star size={18} className="text-amber-500" />} title="문서 5건, 10건 달성하면" desc="업적 보너스 +50%가 충전돼요. 단계도 올라가요." />
            <Step emoji={<Gift size={18} className="text-violet-500" />} title="가끔은 깜짝 보너스도" desc="문서를 완성할 때마다 랜덤으로 추가 보너스가 나올 수 있어요." />
          </div>
        </div>

        {/* ── FAQ ── */}
        <div className="mb-16">
          <h2 className="text-xl font-extrabold tracking-tight text-center mb-8">자주 묻는 질문</h2>
          <div className="max-w-2xl mx-auto space-y-3">
            <FAQ q="한글 프로그램이 없어도 되나요?" a="네. 브라우저만 있으면 됩니다. Mac, 태블릿, 스마트폰에서도 사용할 수 있어요." />
            <FAQ q="한번 구매하면 사용량이 사라지나요?" a="아니요. 다 쓸 때까지 유지됩니다. 유효기간이 없어요." />
            <FAQ q="첫 구매 2배 충전은 언제까지 적용되나요?" a="처음 구매할 때 한 번만 적용돼요. 이후 추가 구매는 1배(100%)로 충전됩니다." />
            <FAQ q="Pro를 해지하면 어떻게 되나요?" a="다음 결제일까지는 Pro로 사용할 수 있어요. 이후 자동으로 무료 플랜으로 전환됩니다." />
            <FAQ q="내 파일이 서버에 남나요?" a="파일은 처리 후 30분 안에 자동 삭제돼요. 서버에 남는 건 내 정보 프리셋과 매핑 기록뿐이에요." />
            <FAQ q="환불할 수 있나요?" a="구매 후 7일 안에 사용하지 않았다면 전액 환불 가능해요." />
            <FAQ q="다른 AI 문서 서비스랑 뭐가 다른가요?" a="한글 프로그램 없이 사용할 수 있고, Mac에서도 돼요. 한번 결제하면 매달 돈이 나가지 않아요." />
          </div>
        </div>

        {/* ── 신뢰 ── */}
        <div className="flex items-center justify-center gap-8 text-sm text-[#57423c]/30 pt-8 border-t border-gray-200/60">
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

function Step({ emoji, title, desc }: { emoji: React.ReactNode; title: string; desc: string }) {
  return (
    <div className="flex items-start gap-4 bg-white rounded-xl border border-gray-200/80 p-4">
      <div className="w-9 h-9 rounded-lg bg-[#f4f4f1] flex items-center justify-center shrink-0 mt-0.5">{emoji}</div>
      <div>
        <p className="font-bold text-sm text-[#1a1c1b] mb-0.5">{title}</p>
        <p className="text-sm text-[#57423c]/60 leading-relaxed">{desc}</p>
      </div>
    </div>
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
      {open && <p className="px-5 pb-5 text-base text-[#57423c]/50 leading-relaxed -mt-1">{a}</p>}
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
          <span className="text-sm text-[#57423c]/30">또는</span>
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
          {error && <p className="text-sm text-red-500">{error}</p>}
          <button type="submit" disabled={loading}
            className="w-full py-3 rounded-xl bg-[#1a1c1b] text-white font-bold text-sm hover:bg-black transition-colors disabled:opacity-50">
            {loading ? "처리 중..." : mode === "login" ? "로그인" : "가입하기"}
          </button>
        </form>
        <p className="text-sm text-[#57423c]/40 text-center mt-4">
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
