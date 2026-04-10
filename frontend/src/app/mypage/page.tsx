"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import ProfileHeader from "@/components/mypage/ProfileHeader";
import LevelAchievements from "@/components/mypage/LevelAchievements";
import PresetManager from "@/components/mypage/PresetManager";
import MappingManager from "@/components/mypage/MappingManager";
import PlanInfo from "@/components/mypage/PlanInfo";
import LoginModal from "@/components/ui/LoginModal";
import { FileText, ChevronLeft, User, Ticket } from "lucide-react";
import { checkCoupon, redeemCoupon } from "@/lib/api";

export default function MyPage() {
  const { user, accessToken, loading } = useAuth();
  const [showLogin, setShowLogin] = useState(false);
  const [couponCode, setCouponCode] = useState("");
  const [couponLoading, setCouponLoading] = useState(false);
  const [couponError, setCouponError] = useState("");
  const [couponInfo, setCouponInfo] = useState<{ code: string; label: string; value: number; expires: string } | null>(null);
  const [couponApplied, setCouponApplied] = useState(false);

  async function handleCheckCoupon() {
    if (!couponCode.trim() || !user || !accessToken) return;
    setCouponLoading(true);
    setCouponError("");
    setCouponInfo(null);
    try {
      const data = await checkCoupon(couponCode.trim());
      setCouponInfo({ code: data.code, label: data.label, value: data.value, expires: data.expires });
    } catch (e: unknown) {
      setCouponError(e instanceof Error ? e.message : "유효하지 않은 쿠폰입니다.");
    } finally {
      setCouponLoading(false);
    }
  }

  async function handleUseCoupon() {
    if (!couponInfo) return;
    setCouponLoading(true);
    try {
      await redeemCoupon(couponInfo.code);
      setCouponApplied(true);
      setCouponCode("");
    } catch (e: unknown) {
      setCouponError(e instanceof Error ? e.message : "쿠폰 적용에 실패했습니다.");
      setCouponInfo(null);
    } finally {
      setCouponLoading(false);
    }
  }

  useEffect(() => {
    if (!loading && !user) setShowLogin(true);
  }, [loading, user]);

  return (
    <div className="min-h-screen bg-[#f9f9f6]">
      {/* 헤더 */}
      <header className="sticky top-0 z-50 bg-[#f9f9f6]/80 backdrop-blur-xl border-b border-[#93C5FD]/50">
        <div className="max-w-screen-xl mx-auto px-6 lg:px-10 py-3.5 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/tool" className="flex items-center gap-1 text-[#57423c] hover:text-[#1E40AF] transition-colors">
              <ChevronLeft size={16} />
            </Link>
            <Link href="/" className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-[#1a1c1b] flex items-center justify-center">
                <FileText size={14} className="text-white" strokeWidth={2.2} />
              </div>
              <span className="text-lg font-extrabold tracking-tighter text-[#1a1c1b]">Eazy HWPX</span>
            </Link>
            <span className="hidden sm:block text-sm text-[#57423c]">마이페이지</span>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/tool" className="text-sm text-[#57423c] hover:text-[#1E40AF] transition-colors">도구</Link>
            <Link href="/pricing" className="text-sm text-[#57423c] hover:text-[#1E40AF] transition-colors">요금제</Link>
          </div>
        </div>
      </header>

      {/* 비로그인 */}
      {!loading && !user && (
        <div className="max-w-md mx-auto px-6 py-20 text-center">
          <User size={48} className="text-[#57423c]/40 mx-auto mb-4" />
          <p className="text-lg font-bold text-[#1a1c1b] mb-2">로그인이 필요해요</p>
          <p className="text-sm text-[#57423c] mb-6">마이페이지에서 내 사용 현황, 업적, 프리셋을 확인할 수 있어요.</p>
          <button
            onClick={() => setShowLogin(true)}
            className="bg-gradient-to-r from-[#2563EB] to-[#1E40AF] text-white px-6 py-2.5 rounded-xl font-semibold text-sm hover:opacity-90 transition-all"
          >
            로그인 / 가입
          </button>
        </div>
      )}

      {/* 로그인 상태 */}
      {user && (
        <div className="max-w-screen-xl mx-auto px-6 lg:px-10 py-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* 왼쪽 (프로필 + 요금제) */}
            <div className="lg:col-span-1 space-y-6">
              <ProfileHeader />
              <PlanInfo />

              {/* 쿠폰 입력 */}
              <div className="bg-white rounded-2xl border border-gray-200/80 p-5">
                <div className="flex items-center gap-2 mb-3">
                  <Ticket size={16} className="text-[#2563EB]" />
                  <span className="font-bold text-sm text-[#1a1c1b]">쿠폰 / 프로모션 코드</span>
                </div>

                {couponApplied ? (
                  /* Step 3: 적용 완료 */
                  <div className="flex items-center gap-2 bg-emerald-50 border border-emerald-200 px-4 py-3 rounded-xl">
                    <Ticket size={14} className="text-emerald-600 shrink-0" />
                    <span className="text-sm font-bold text-emerald-700">쿠폰이 적용되었습니다!</span>
                  </div>
                ) : couponInfo ? (
                  /* Step 2: 쿠폰 카드 */
                  <div className="border-2 border-dashed border-[#2563EB]/40 rounded-2xl p-4 relative overflow-hidden">
                    <div className="absolute top-0 right-0 bg-[#2563EB] text-white text-[10px] font-bold px-3 py-1 rounded-bl-xl">쿠폰 발급</div>
                    <div className="flex items-center gap-2.5 mb-3">
                      <div className="w-9 h-9 rounded-xl bg-[#EFF6FF] flex items-center justify-center shrink-0">
                        <Ticket size={16} className="text-[#2563EB]" />
                      </div>
                      <div>
                        <p className="text-sm font-extrabold text-[#1a1c1b]">{couponInfo.label}</p>
                        <p className="text-xs text-[#57423c]/65">코드: {couponInfo.code} / {couponInfo.expires}까지</p>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={handleUseCoupon}
                        disabled={couponLoading}
                        className="flex-1 py-2 rounded-xl bg-[#2563EB] text-white font-bold text-sm hover:opacity-90 transition-all active:scale-95 disabled:opacity-50"
                      >
                        {couponLoading ? "적용 중..." : "지금 사용하기"}
                      </button>
                      <button
                        onClick={() => { setCouponInfo(null); setCouponCode(""); }}
                        className="px-3 py-2 rounded-xl border border-gray-200 text-[#57423c] font-bold text-sm hover:bg-gray-50 transition-all"
                      >
                        나중에
                      </button>
                    </div>
                  </div>
                ) : (
                  /* Step 1: 코드 입력 */
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      value={couponCode}
                      onChange={(e) => { setCouponCode(e.target.value.toUpperCase()); setCouponError(""); }}
                      onKeyDown={(e) => e.key === "Enter" && handleCheckCoupon()}
                      placeholder="코드 입력"
                      className="flex-1 px-3 py-2.5 rounded-xl border border-gray-200 bg-[#f9f9f6] text-sm focus:border-[#2563EB] focus:outline-none"
                    />
                    <button
                      onClick={handleCheckCoupon}
                      disabled={couponLoading || !couponCode.trim()}
                      className="px-4 py-2.5 rounded-xl bg-[#2563EB] text-white font-bold text-sm hover:opacity-90 transition-all active:scale-95 disabled:opacity-50 shrink-0"
                    >
                      {couponLoading ? "..." : "확인"}
                    </button>
                  </div>
                )}
                {couponError && <p className="text-sm text-red-500 font-medium mt-2">{couponError}</p>}
              </div>
            </div>

            {/* 오른쪽 (업적 + 프리셋 + 매핑) */}
            <div className="lg:col-span-2 space-y-6">
              <LevelAchievements />
              <PresetManager />
              <MappingManager />
            </div>
          </div>
        </div>
      )}

      {/* 푸터 */}
      <footer className="max-w-screen-xl mx-auto px-6 lg:px-10 py-4 flex items-center justify-center gap-4 text-sm text-[#57423c]/65">
        <span>Eazy HWPX</span>
        <span>·</span>
        <Link href="/pricing" className="hover:text-[#1E40AF] transition-colors">요금제</Link>
        <span>·</span>
        <Link href="/tool" className="hover:text-[#1E40AF] transition-colors">도구</Link>
      </footer>

      {showLogin && <LoginModal onClose={() => setShowLogin(false)} />}
    </div>
  );
}
