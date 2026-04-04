"use client";

import { AuthProvider } from "@/context/AuthContext";
import { ReactNode } from "react";

export function AuthWrapper({ children }: { children: ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>;
}
