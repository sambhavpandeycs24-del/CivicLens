"use client";
import { useEffect, useState } from "react";
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
export function ApiStatus() {
  const [status, setStatus] = useState<"checking" | "online" | "offline">("checking");
  useEffect(() => { let active = true; fetch(API_URL.replace(/\/api\/v1$/, "") + "/health").then((response) => { if (active) setStatus(response.ok ? "online" : "offline"); }).catch(() => { if (active) setStatus("offline"); }); return () => { active = false; }; }, []);
  const label = status === "online" ? "API online" : status === "offline" ? "API offline — start the backend" : "Checking API connection…";
  return <div className="flex items-center gap-2 text-sm text-[#64756e]"><span className={`h-2.5 w-2.5 rounded-full ${status === "online" ? "bg-emerald-500" : status === "offline" ? "bg-rose-500" : "bg-amber-400"}`} />{label}</div>;
}
