"use client";

import { useState } from "react";
import { useAuth } from "@/context/AuthContext";

export default function LoginModal({ onClose }: { onClose: () => void }) {
  const { signIn, signUp, signInWithProvider } = useAuth();
  const [mode, setMode] = useState<"login" | "signup">("signup");
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
      </div>
    </div>
  );
}
