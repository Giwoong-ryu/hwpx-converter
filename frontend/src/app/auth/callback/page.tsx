"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";

const API = process.env.NEXT_PUBLIC_API_URL || "/api";

export default function AuthCallback() {
  const router = useRouter();

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) {
        // 프로필 생성 (소셜 로그인 첫 가입 시)
        fetch(`${API}/auth/me`, {
          headers: { Authorization: `Bearer ${session.access_token}` },
        }).then((res) => {
          if (res.ok) {
            router.push("/tool");
          } else {
            // 프로필 없으면 생성
            fetch(`${API}/auth/signup`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                email: session.user.email || "",
                password: crypto.randomUUID(),
                name: session.user.user_metadata?.full_name || "",
              }),
            }).then(() => router.push("/tool"));
          }
        });
      } else {
        router.push("/");
      }
    });
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <p className="text-gray-500">로그인 처리 중...</p>
    </div>
  );
}
