"use client";

import { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import Link from "next/link";
import { FileText, Check, Shield, Zap, Crown, ChevronDown, Gift, Flame, Trophy, Star, ArrowRight, Ticket } from "lucide-react";
import { redeemCoupon } from "@/lib/api";
import CouponBadge from "@/components/ui/CouponBadge";

const PLUS_ID = "307b2685-27de-4b96-ac7d-670a669c85d8";
const PRO_ID = "fe4b5d80-c912-403b-b940-58b4c50bb6b8";

export default function PricingPage() {
  const { user, accessToken } = useAuth();
  const [purchasing, setPurchasing] = useState<string | null>(null);
  const [showLogin, setShowLogin] = useState(false);
  const [couponCode, setCouponCode] = useState("");
  const [couponLoading, setCouponLoading] = useState(false);
  const [couponResult, setCouponResult] = useState<{ ok: boolean; message: string } | null>(null);

  async function handleCoupon() {
    if (!couponCode.trim()) return;
    if (!user || !accessToken) {
      setShowLogin(true);
      return;
    }
    setCouponLoading(true);
    setCouponResult(null);
    try {
      const data = await redeemCoupon(couponCode.trim());
      setCouponResult({ ok: true, message: data.message || "쿠폰이 적용되었습니다!" });
      setCouponCode("");
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "쿠폰 적용에 실패했습니다.";
      setCouponResult({ ok: false, message: msg });
    } finally {
      setCouponLoading(false);
    }
  }

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
          <div className="flex items-center gap-4">
            <CouponBadge />
            <Link href="/tool" className="text-base text-[#57423c]/70 hover:text-[#1a1c1b] transition-colors">도구</Link>
            {user ? (
              <span className="text-base text-[#57423c]/50">{user.email}</span>
            ) : (
              <Link href="/tool" className="bg-gradient-to-r from-[#2563EB] to-[#1E40AF] text-white px-5 py-2 rounded-lg font-semibold text-base hover:opacity-90 transition-all active:scale-95">
                무료로 시작하기
              </Link>
            )}
          </div>
        </div>
      </nav>

      <main className="pt-24 pb-20 max-w-screen-xl mx-auto px-8 lg:px-12">

        {/* ── 헤드라인 ── */}
        <div className="text-center mb-6">
          <h1 className="text-[2.2rem] lg:text-[2.8rem] font-extrabold leading-[1.15] tracking-tight">
            문서 변환/추출은 <span className="text-[#2563EB]">무료</span>.<br />
            AI 자동 채우기만 유료입니다.
          </h1>
        </div>

        {/* ── 가격 카드 3열 ── */}
        <div id="plans" className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto mb-6">

          {/* Free */}
          <div className="bg-white rounded-2xl border border-gray-200/80 p-6 flex flex-col">
            <div className="text-sm font-bold text-[#57423c]/30 uppercase tracking-widest mb-3">Free</div>
            <div className="text-4xl font-black tracking-tight mb-1">0원</div>
            <p className="text-base text-[#57423c]/50 mb-5">가입 없이도 바로 사용</p>
            <ul className="space-y-3 mb-6 flex-1">
              <Li text="HWP/HWPX/DOCX 변환 무제한" />
              <Li text="문서 → 엑셀 추출 무제한" />
              <Li text="문서 합치기 / 도장 무제한" />
              <Li text="AI 매핑 하루 3회" />
              <Li text="AI 작성 하루 1회 (+재시도)" />
              <Li text="내 정보 미리 저장 1개" />
            </ul>
            <Link href="/tool" className="block text-center py-3.5 rounded-xl border-2 border-gray-200 text-[#1a1c1b] font-bold text-base hover:border-[#1a1c1b] transition-colors">
              무료로 시작하기
            </Link>
          </div>

          {/* Plus */}
          <div className="bg-white rounded-2xl border-2 border-[#2563EB] p-6 flex flex-col relative shadow-[0_4px_32px_rgba(37,99,235,0.08)]">
            <div className="text-sm font-bold text-[#2563EB]/60 uppercase tracking-widest mb-3 flex items-center gap-1.5">
              <Zap size={14} /> Plus
            </div>
            <div className="text-4xl font-black tracking-tight mb-1">4,900원</div>
            <p className="text-base text-[#2563EB] font-bold mb-1.5">첫 구매 시 게이지 2배 충전</p>
            <p className="text-sm text-[#57423c]/50 mb-4 leading-relaxed">한번 결제, 기간 만료 없이 사용.<br />부족하면 추가 구매.</p>
            <ul className="space-y-3 mb-6 flex-1">
              <Li text="무료 기능 전부 포함" />
              <Li text="AI 사용량 게이지 충전" highlight />
              <Li text="첫 구매 2배 충전 (200%)" highlight />
              <Li text="대량 생성 30건" highlight />
              <Li text="내 정보 미리 저장 3개" highlight />
              <Li text="자주 쓰는 양식 10개 저장" highlight />
              <Li text="다 쓸 때까지 사라지지 않아요" highlight />
            </ul>
            <button
              onClick={() => handlePurchase(PLUS_ID)}
              disabled={purchasing === PLUS_ID}
              className="w-full py-3.5 rounded-xl bg-gradient-to-r from-[#2563EB] to-[#1E40AF] text-white font-bold text-base hover:opacity-90 transition-all active:scale-[0.98] disabled:opacity-50"
            >
              {purchasing === PLUS_ID ? "처리 중..." : "4,900원으로 시작하기"}
            </button>
          </div>

          {/* Pro */}
          <div className="bg-white rounded-2xl border border-gray-200/80 p-6 flex flex-col">
            <div className="text-sm font-bold text-[#57423c]/30 uppercase tracking-widest mb-3 flex items-center gap-1.5">
              <Crown size={14} /> Pro
            </div>
            <div className="text-4xl font-black tracking-tight mb-1">9,900원<span className="text-lg font-normal text-[#57423c]/30">/월</span></div>
            <p className="text-base text-[#57423c]/50 mb-1.5">AI 무제한, 횟수 걱정 없이</p>
            <p className="text-sm text-[#57423c]/50 mb-4 leading-relaxed">매주 게이지 자동 리셋.<br />구독 중 요금 인상 없음.</p>
            <ul className="space-y-3 mb-6 flex-1">
              <Li text="무료 기능 전부 포함" />
              <Li text="AI 매핑/작성 무제한" highlight />
              <Li text="매주 게이지 자동 리셋" highlight />
              <Li text="대량 생성 200건" highlight />
              <Li text="내 정보 미리 저장 무제한" highlight />
              <Li text="자주 쓰는 양식 무제한 저장" highlight />
              <Li text="며칠 못 써도 연속 기록 유지" highlight />
            </ul>
            <button
              onClick={() => handlePurchase(PRO_ID)}
              disabled={purchasing === PRO_ID}
              className="w-full py-3.5 rounded-xl border-2 border-[#1a1c1b] text-[#1a1c1b] font-bold text-base hover:bg-[#1a1c1b] hover:text-white transition-all active:scale-[0.98] disabled:opacity-50"
            >
              {purchasing === PRO_ID ? "처리 중..." : "프로 구독 시작하기"}
            </button>
          </div>
        </div>

        {/* ── 쿠폰 입력 + 스크롤 힌트 ── */}
        <div className="flex items-center justify-center gap-8 max-w-4xl mx-auto mb-10 mt-8">
          {/* 쿠폰 입력 */}
          <div className="flex items-center gap-2">
            <Ticket size={16} className="text-[#57423c]/30 shrink-0" />
            <input
              type="text"
              value={couponCode}
              onChange={(e) => { setCouponCode(e.target.value.toUpperCase()); setCouponResult(null); }}
              onKeyDown={(e) => e.key === "Enter" && handleCoupon()}
              placeholder="쿠폰 코드"
              className="w-36 px-3 py-2 rounded-lg border border-gray-200 bg-white text-sm focus:border-[#2563EB] focus:outline-none"
            />
            <button
              onClick={handleCoupon}
              disabled={couponLoading || !couponCode.trim()}
              className="px-4 py-2 rounded-lg bg-[#2563EB] text-white font-bold text-sm hover:opacity-90 transition-all active:scale-95 disabled:opacity-50"
            >
              {couponLoading ? "..." : "적용"}
            </button>
            {couponResult && (
              <span className={`text-sm font-medium ${couponResult.ok ? "text-emerald-600" : "text-red-500"}`}>
                {couponResult.message}
              </span>
            )}
          </div>

          {/* 스크롤 힌트 */}
          <div className="flex flex-col items-center gap-1 animate-bounce text-[#57423c]/40">
            <span className="text-xs uppercase font-bold tracking-widest">Scroll to explore</span>
            <ChevronDown size={14} />
          </div>
        </div>

        {/* ── 이렇게 작동해요 (게이지 개념) ── */}
        <div className="max-w-3xl mx-auto mb-16 bg-white rounded-2xl border border-gray-200/80 p-8">
          <h2 className="text-2xl font-extrabold tracking-tight text-center mb-2">AI 사용량, 이렇게 작동해요</h2>
          <p className="text-base text-[#57423c]/50 text-center mb-8">복잡한 구독이 아닙니다. 충전해두고, 쓸 때마다 차감됩니다.</p>
          <div className="grid md:grid-cols-3 gap-6 text-center">
            <div>
              <div className="w-14 h-14 rounded-xl bg-[#EFF6FF] flex items-center justify-center mx-auto mb-3">
                <Zap size={24} className="text-[#2563EB]" />
              </div>
              <p className="text-lg font-bold text-[#1a1c1b] mb-1">게이지 충전</p>
              <p className="text-base text-[#57423c]/60 leading-relaxed">구매하면 AI 사용량이 충전돼요.<br />스마트폰 데이터처럼 쓸 때만 줄어요.</p>
            </div>
            <div>
              <div className="w-14 h-14 rounded-xl bg-[#F0FDF4] flex items-center justify-center mx-auto mb-3">
                <Gift size={24} className="text-emerald-500" />
              </div>
              <p className="text-lg font-bold text-[#1a1c1b] mb-1">쓰면 보너스 적립</p>
              <p className="text-base text-[#57423c]/60 leading-relaxed">사업계획서 1건 완성하면<br />다음 1건 분량이 보너스로 충전돼요.</p>
            </div>
            <div>
              <div className="w-14 h-14 rounded-xl bg-[#FEF3C7] flex items-center justify-center mx-auto mb-3">
                <Shield size={24} className="text-amber-500" />
              </div>
              <p className="text-lg font-bold text-[#1a1c1b] mb-1">기간 만료 없음</p>
              <p className="text-base text-[#57423c]/60 leading-relaxed">한번 충전하면 1년이 지나도<br />다 쓸 때까지 사라지지 않아요.</p>
            </div>
          </div>
        </div>

        {/* ── 쓸수록 혜택이 쌓여요 ── */}
        <div className="mb-20 max-w-2xl mx-auto">
          <h2 className="text-2xl font-extrabold tracking-tight text-center mb-3">쓸수록 혜택이 쌓여요</h2>
          <p className="text-base text-[#57423c]/50 text-center mb-8 leading-relaxed">문서를 만들수록 보너스가 쌓여서 더 오래 쓸 수 있어요</p>
          <div className="space-y-4">
            <Step emoji={<Trophy size={20} className="text-[#2563EB]" />} title="첫 문서를 완성하면" desc="사업계획서 1건 완성 = 다음 1건 분량이 보너스로 자동 충전" />
            <Step emoji={<Flame size={20} className="text-orange-500" />} title="매일 꾸준히 사용하면" desc="3일 연속 사용부터 보너스가 쌓여요. 7일, 30일까지 보너스가 커져요." />
            <Step emoji={<Star size={20} className="text-amber-500" />} title="문서 5건, 10건 달성하면" desc="이력서 5건 달성 = 보너스 2건분 추가 충전. 칭호도 올라가요." />
            <Step emoji={<Gift size={20} className="text-violet-500" />} title="가끔은 깜짝 보너스도" desc="문서를 완성할 때마다 랜덤으로 추가 보너스가 나올 수 있어요." />
          </div>
        </div>

        {/* ── FAQ ── */}
        <div className="mb-16">
          <h2 className="text-2xl font-extrabold tracking-tight text-center mb-8">자주 묻는 질문</h2>
          <div className="max-w-2xl mx-auto space-y-3">
            <FAQ q="한글 프로그램이 없어도 되나요?" a="네. 브라우저만 있으면 됩니다. Mac, 태블릿, 스마트폰에서도 사용할 수 있어요." />
            <FAQ q="사용량 게이지가 뭔가요?" a="AI 기능을 쓸 때마다 줄어드는 에너지 바라고 생각하시면 돼요. 100%에서 시작해서, 문서를 만들 때마다 조금씩 줄어들고, 보너스로 다시 차오릅니다." />
            <FAQ q="한번 구매하면 사용량이 사라지나요?" a="아니요. 다 쓸 때까지 유지됩니다. 유효기간이 없어요." />
            <FAQ q="첫 구매 2배 충전은 언제까지 적용되나요?" a="처음 구매할 때 한 번만 적용돼요. 이후 추가 구매는 1배(100%)로 충전됩니다." />
            <FAQ q="Pro를 해지하면 어떻게 되나요?" a="다음 결제일까지는 Pro로 사용할 수 있어요. 이후 자동으로 무료 플랜으로 전환됩니다." />
            <FAQ q="내 파일이 서버에 남나요?" a="파일은 처리 후 3시간 안에 자동 삭제돼요. 개인정보는 저장하지 않습니다." />
            <FAQ q="환불할 수 있나요?" a="구매 후 7일 안에 사용하지 않았다면 전액 환불 가능해요." />
          </div>
        </div>

        {/* ── 신뢰 ── */}
        <div className="flex items-center justify-center gap-8 text-base text-[#57423c]/30 pt-8 border-t border-gray-200/60">
          <span className="flex items-center gap-1.5"><Shield size={14} /> 광고 없음</span>
          <span className="flex items-center gap-1.5"><Shield size={14} /> 파일 즉시 삭제</span>
          <span className="flex items-center gap-1.5"><Shield size={14} /> 로그인 없이 사용 가능</span>
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
      <Check className={`w-5 h-5 mt-0.5 shrink-0 ${highlight ? "text-[#2563EB]" : "text-[#2563EB]/40"}`} />
      <span className={`text-base ${highlight ? "text-[#1a1c1b] font-medium" : "text-[#57423c]/70"}`}>{text}</span>
    </li>
  );
}

function Step({ emoji, title, desc }: { emoji: React.ReactNode; title: string; desc: string }) {
  return (
    <div className="flex items-start gap-4 bg-white rounded-xl border border-gray-200/80 p-5">
      <div className="w-10 h-10 rounded-lg bg-[#f4f4f1] flex items-center justify-center shrink-0 mt-0.5">{emoji}</div>
      <div>
        <p className="font-bold text-base text-[#1a1c1b] mb-1">{title}</p>
        <p className="text-base text-[#57423c]/60 leading-relaxed">{desc}</p>
      </div>
    </div>
  );
}

function FAQ({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="bg-white rounded-xl border border-gray-200/80 overflow-hidden">
      <button onClick={() => setOpen(!open)} className="w-full p-5 flex items-center justify-between text-left">
        <span className="font-bold text-base text-[#1a1c1b]">{q}</span>
        <ChevronDown size={18} className={`text-[#57423c]/30 transition-transform shrink-0 ml-4 ${open ? "rotate-180" : ""}`} />
      </button>
      {open && <p className="px-5 pb-5 text-base text-[#57423c]/60 leading-relaxed -mt-1">{a}</p>}
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
            className="w-full py-3 rounded-xl border border-gray-200 text-[#1a1c1b] font-medium text-base hover:bg-white transition-colors">
            Google로 계속
          </button>
          <button onClick={() => signInWithProvider("kakao")}
            className="w-full py-3 rounded-xl bg-[#FEE500] text-[#191919] font-medium text-base hover:brightness-95 transition-all">
            카카오로 계속
          </button>
        </div>
        <div className="flex items-center gap-4 mb-6">
          <div className="flex-1 h-px bg-gray-200" />
          <span className="text-base text-[#57423c]/30">또는</span>
          <div className="flex-1 h-px bg-gray-200" />
        </div>
        <form onSubmit={handleSubmit} className="space-y-3">
          {mode === "signup" && (
            <input type="text" placeholder="이름" value={name} onChange={(e) => setName(e.target.value)}
              className="w-full px-4 py-3 rounded-xl border border-gray-200 bg-white text-base focus:border-[#1a1c1b] focus:outline-none" />
          )}
          <input type="email" placeholder="이메일" value={email} onChange={(e) => setEmail(e.target.value)} required
            className="w-full px-4 py-3 rounded-xl border border-gray-200 bg-white text-base focus:border-[#1a1c1b] focus:outline-none" />
          <input type="password" placeholder="비밀번호" value={password} onChange={(e) => setPassword(e.target.value)} required
            className="w-full px-4 py-3 rounded-xl border border-gray-200 bg-white text-base focus:border-[#1a1c1b] focus:outline-none" />
          {error && <p className="text-base text-red-500">{error}</p>}
          <button type="submit" disabled={loading}
            className="w-full py-3 rounded-xl bg-[#1a1c1b] text-white font-bold text-base hover:bg-black transition-colors disabled:opacity-50">
            {loading ? "처리 중..." : mode === "login" ? "로그인" : "가입하기"}
          </button>
        </form>
        <p className="text-base text-[#57423c]/40 text-center mt-4">
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
