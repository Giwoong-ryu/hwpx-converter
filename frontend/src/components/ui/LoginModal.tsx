"use client";

import { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { Ticket } from "lucide-react";
import { redeemCoupon } from "@/lib/api";

export default function LoginModal({ onClose }: { onClose: () => void }) {
  const { signIn, signUp, signInWithProvider } = useAuth();
  const [mode, setMode] = useState<"login" | "signup">("signup");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [couponCode, setCouponCode] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [couponResult, setCouponResult] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    if (mode === "login") {
      const result = await signIn(email, password);
      if (result.error) setError(result.error);
      else onClose();
    } else {
      const result = await signUp(email, password, name);
      if (result.error) {
        setError(result.error);
      } else {
        // 가입 성공 → 쿠폰이 있으면 자동 적용
        if (couponCode.trim()) {
          try {
            const data = await redeemCoupon(couponCode.trim());
            setCouponResult(data.message || "쿠폰이 적용되었습니다!");
            // 잠시 보여주고 닫기
            setTimeout(() => onClose(), 2000);
          } catch {
            // 쿠폰 실패해도 가입은 완료됨
            setCouponResult("가입 완료! (쿠폰 적용은 로그인 후 요금제 페이지에서 가능합니다)");
            setTimeout(() => onClose(), 2000);
          }
        } else {
          onClose();
        }
      }
    }
    setLoading(false);
  }

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-[100] flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-[#f9f9f6] rounded-2xl p-8 w-full max-w-sm border border-gray-200/80" onClick={(e) => e.stopPropagation()}>

        {couponResult ? (
          <div className="text-center py-4">
            <div className="w-12 h-12 rounded-full bg-emerald-100 flex items-center justify-center mx-auto mb-3">
              <Ticket size={20} className="text-emerald-600" />
            </div>
            <p className="text-base font-bold text-[#1a1c1b] mb-1">가입 완료!</p>
            <p className="text-sm text-emerald-600 font-medium">{couponResult}</p>
          </div>
        ) : (
          <>
            <h2 className="text-xl font-extrabold tracking-tight mb-2">
              {mode === "login" ? "로그인" : "무료 가입"}
            </h2>
            <p className="text-sm text-[#57423c]/40 mb-6">
              {mode === "login" ? "계정에 로그인합니다" : "가입하면 AI 기능을 매일 무료로 사용할 수 있습니다"}
            </p>

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

              {mode === "signup" && (
                <div className="relative">
                  <Ticket size={14} className="absolute left-4 top-1/2 -translate-y-1/2 text-[#57423c]/30" />
                  <input type="text" placeholder="쿠폰 코드 (선택)" value={couponCode}
                    onChange={(e) => setCouponCode(e.target.value.toUpperCase())}
                    className="w-full pl-10 pr-4 py-3 rounded-xl border border-dashed border-gray-300 bg-gray-50 text-sm focus:border-[#2563EB] focus:outline-none placeholder-[#57423c]/30" />
                </div>
              )}

              {error && <p className="text-xs text-red-500">{error}</p>}
              <button type="submit" disabled={loading}
                className="w-full py-3 rounded-xl bg-[#1a1c1b] text-white font-bold text-sm hover:bg-black transition-colors disabled:opacity-50">
                {loading ? "처리 중..." : mode === "login" ? "로그인" : "무료로 가입하기"}
              </button>
            </form>

            <p className="text-xs text-[#57423c]/40 text-center mt-4">
              {mode === "login" ? (
                <>계정이 없으신가요? <button onClick={() => setMode("signup")} className="text-[#1a1c1b] font-bold">무료 가입</button></>
              ) : (
                <>이미 계정이 있으신가요? <button onClick={() => setMode("login")} className="text-[#1a1c1b] font-bold">로그인</button></>
              )}
            </p>
          </>
        )}
      </div>
    </div>
  );
}
