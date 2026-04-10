"use client";

import { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { supabase } from "@/lib/supabase";

type Mode = "login" | "signup" | "forgot";

export default function LoginModal({ onClose }: { onClose: () => void }) {
  const { signIn, signUp, signInWithProvider } = useAuth();
  const [mode, setMode] = useState<Mode>("signup");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [forgotSent, setForgotSent] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    if (mode === "forgot") {
      const { error: err } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/auth/callback?type=recovery`,
      });
      if (err) setError(err.message);
      else setForgotSent(true);
      setLoading(false);
      return;
    }

    const result = mode === "login"
      ? await signIn(email, password)
      : await signUp(email, password, name);
    if (result.error) setError(result.error);
    else onClose();
    setLoading(false);
  }

  const TITLES: Record<Mode, string> = {
    login: "로그인",
    signup: "무료 가입",
    forgot: "비밀번호 찾기",
  };

  const SUBTITLES: Record<Mode, string> = {
    login: "계정에 로그인합니다",
    signup: "가입하면 하루 10회 AI 자동 채우기를 무료로 사용할 수 있어요",
    forgot: "가입한 이메일로 재설정 링크를 보내드립니다",
  };

  return (
    <div
      className="fixed inset-0 bg-black/40 backdrop-blur-sm z-100 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-[#f9f9f6] rounded-2xl p-8 w-full max-w-sm border border-gray-200/80"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-xl font-extrabold tracking-tight mb-2">
          {TITLES[mode]}
        </h2>
        <p className="text-sm text-[#57423c]/60 mb-6">{SUBTITLES[mode]}</p>

        {/* 비밀번호 찾기 성공 */}
        {forgotSent ? (
          <div className="text-center py-4">
            <div className="w-12 h-12 rounded-full bg-emerald-100 flex items-center justify-center mx-auto mb-3">
              <svg className="w-6 h-6 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <p className="text-sm font-bold text-[#1a1c1b] mb-1">이메일을 확인해주세요</p>
            <p className="text-xs text-[#57423c]/65 mb-5">{email}로 재설정 링크를 보냈습니다.</p>
            <button
              onClick={() => { setForgotSent(false); setMode("login"); }}
              className="text-sm text-[#2563EB] hover:underline"
            >
              로그인으로 돌아가기
            </button>
          </div>
        ) : (
          <>
            {/* 소셜 로그인 (forgot 제외) */}
            {mode !== "forgot" && (
              <>
                <div className="space-y-3 mb-6">
                  <button
                    onClick={() => signInWithProvider("google")}
                    className="w-full py-3 rounded-xl border border-gray-200 text-[#1a1c1b] font-medium text-sm hover:bg-white transition-colors"
                  >
                    Google로 계속
                  </button>
                  <button
                    onClick={() => signInWithProvider("kakao")}
                    className="w-full py-3 rounded-xl bg-[#FEE500] text-[#191919] font-medium text-sm hover:brightness-95 transition-all"
                  >
                    카카오로 계속
                  </button>
                </div>
                <div className="flex items-center gap-4 mb-6">
                  <div className="flex-1 h-px bg-gray-200" />
                  <span className="text-xs text-[#57423c]/65">또는</span>
                  <div className="flex-1 h-px bg-gray-200" />
                </div>
              </>
            )}

            {/* 폼 */}
            <form onSubmit={handleSubmit} className="space-y-3">
              {mode === "signup" && (
                <input
                  type="text"
                  placeholder="이름"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border border-gray-200 bg-white text-sm focus:border-[#1a1c1b] focus:outline-none"
                />
              )}
              <input
                type="email"
                placeholder="이메일"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full px-4 py-3 rounded-xl border border-gray-200 bg-white text-sm focus:border-[#1a1c1b] focus:outline-none"
              />
              {mode !== "forgot" && (
                <input
                  type="password"
                  placeholder="비밀번호"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="w-full px-4 py-3 rounded-xl border border-gray-200 bg-white text-sm focus:border-[#1a1c1b] focus:outline-none"
                />
              )}
              {error && <p className="text-xs text-red-500">{error}</p>}
              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 rounded-xl bg-[#1a1c1b] text-white font-bold text-sm hover:bg-black transition-colors disabled:opacity-50"
              >
                {loading ? "처리 중..." : mode === "login" ? "로그인" : mode === "signup" ? "무료로 가입하기" : "재설정 링크 보내기"}
              </button>
            </form>

            {/* 하단 모드 전환 링크 */}
            <div className="mt-4 text-center space-y-1.5">
              {mode === "login" && (
                <>
                  <p className="text-xs text-[#57423c]/60">
                    계정이 없으신가요?{" "}
                    <button onClick={() => { setMode("signup"); setError(""); }} className="text-[#1a1c1b] font-bold">무료 가입</button>
                  </p>
                  <p className="text-xs">
                    <button
                      onClick={() => { setMode("forgot"); setError(""); }}
                      className="text-[#57423c]/60 hover:text-[#1a1c1b] transition-colors"
                    >
                      비밀번호를 잊으셨나요?
                    </button>
                  </p>
                </>
              )}
              {mode === "signup" && (
                <p className="text-xs text-[#57423c]/60">
                  이미 계정이 있으신가요?{" "}
                  <button onClick={() => { setMode("login"); setError(""); }} className="text-[#1a1c1b] font-bold">로그인</button>
                </p>
              )}
              {mode === "forgot" && (
                <p className="text-xs text-[#57423c]/60">
                  <button onClick={() => { setMode("login"); setError(""); }} className="text-[#1a1c1b] font-bold">← 로그인으로 돌아가기</button>
                </p>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
