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
import { FileText, ChevronLeft, User } from "lucide-react";

export default function MyPage() {
  const { user, loading } = useAuth();
  const [showLogin, setShowLogin] = useState(false);

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
          <User size={48} className="text-[#57423c]/20 mx-auto mb-4" />
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
      <footer className="max-w-screen-xl mx-auto px-6 lg:px-10 py-4 flex items-center justify-center gap-4 text-sm text-[#57423c]/50">
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
