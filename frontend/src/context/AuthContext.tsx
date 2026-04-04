"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { supabase } from "@/lib/supabase";

const API = process.env.NEXT_PUBLIC_API_URL || "/api";

interface UserProfile {
  user_id: string;
  email: string;
  plan: "free" | "plus" | "pro";
  gauge_pct: number;
  level: number;
  level_title: string;
  streak_days: number;
  total_docs: number;
  preset_limit: number;
  mapping_save_limit: number;
  referral_code: string | null;
  first_purchase_used: boolean;
}

interface AuthContextType {
  user: UserProfile | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<{ error?: string }>;
  signUp: (email: string, password: string, name: string, referralCode?: string) => Promise<{ error?: string }>;
  signOut: () => Promise<void>;
  signInWithProvider: (provider: "kakao" | "google") => Promise<void>;
  refreshStatus: () => Promise<void>;
  accessToken: string | null;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [accessToken, setAccessToken] = useState<string | null>(null);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) {
        setAccessToken(session.access_token);
        fetchProfile(session.access_token);
      } else {
        setLoading(false);
      }
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      if (session) {
        setAccessToken(session.access_token);
        fetchProfile(session.access_token);
      } else {
        setUser(null);
        setAccessToken(null);
        setLoading(false);
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  async function fetchProfile(token: string) {
    try {
      const res = await fetch(`${API}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        setUser(await res.json());
      }
    } catch {
    } finally {
      setLoading(false);
    }
  }

  async function refreshStatus() {
    if (!accessToken) return;
    try {
      const res = await fetch(`${API}/auth/status`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      if (res.ok) {
        const data = await res.json();
        setUser((prev) => prev ? { ...prev, ...data } : null);
      }
    } catch {}
  }

  async function signIn(email: string, password: string) {
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) return { error: error.message };
    return {};
  }

  async function signUp(email: string, password: string, name: string, referralCode?: string) {
    try {
      const res = await fetch(`${API}/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, name, referral_code: referralCode || "" }),
      });
      if (!res.ok) {
        const data = await res.json();
        return { error: data.detail || "가입 실패" };
      }
      return await signIn(email, password);
    } catch (e: any) {
      return { error: e.message };
    }
  }

  async function signInWithProvider(provider: "kakao" | "google") {
    const { error } = await supabase.auth.signInWithOAuth({
      provider,
      options: { redirectTo: `${window.location.origin}/auth/callback` },
    });
    if (error) throw error;
  }

  async function signOut() {
    await supabase.auth.signOut();
    setUser(null);
    setAccessToken(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, signIn, signUp, signOut, signInWithProvider, refreshStatus, accessToken }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
