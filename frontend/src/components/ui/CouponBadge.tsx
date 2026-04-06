"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { Ticket } from "lucide-react";

export default function CouponBadge() {
  const { user, accessToken } = useAuth();
  const [couponName, setCouponName] = useState<string | null>(null);

  useEffect(() => {
    if (!user || !accessToken) return;
    const API = process.env.NEXT_PUBLIC_API_URL || "/api";
    fetch(`${API}/coupon/my-coupon`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    })
      .then((r) => r.json())
      .then((d) => {
        if (d.active) setCouponName(d.coupon_name || "Plus 체험중");
      })
      .catch(() => {});
  }, [user, accessToken]);

  if (!couponName) return null;

  return (
    <div className="flex items-center gap-1.5 bg-[#EFF6FF] border border-[#BFDBFE] px-3 py-1 rounded-full">
      <Ticket size={12} className="text-[#2563EB]" />
      <span className="text-xs font-bold text-[#2563EB]">{couponName}</span>
    </div>
  );
}
