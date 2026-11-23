"use client";

import Link from "next/link";
import { useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

type Complaint = { tracking_code: string; title: string; status: string; category: string; address: string };

export default function TrackPage() {
  const [code, setCode] = useState("");
  const [item, setItem] = useState<Complaint | null>(null);
  const [error, setError] = useState("");

  async function search() {
    setError("");
    setItem(null);
    const token = window.localStorage.getItem("civiclens_access_token");
    if (!token) {
      setError("Sign in to view your complaint status.");
      return;
    }
    const response = await fetch(`${API}/complaints/mine`, { headers: { Authorization: `Bearer ${token}` } });
    if (!response.ok) {
      setError("Unable to retrieve complaints.");
      return;
    }
    const complaints: Complaint[] = await response.json();
    const found = complaints.find((complaint) => complaint.tracking_code.toUpperCase() === code.trim().toUpperCase()) ?? null;
    setItem(found);
    if (!found) setError("No complaint found for this account and tracking code.");
  }

  return (
    <main className="mx-auto min-h-screen max-w-2xl px-6 py-16">
      <Link href="/" className="text-sm font-semibold text-[#176b4b]">← CivicLens AI</Link>
      <h1 className="mt-8 text-3xl font-bold">Track a complaint</h1>
      <p className="mt-3 text-[#64756e]">Sign in first, then enter the tracking code shown after submission.</p>
      <div className="mt-7 flex gap-3">
        <input aria-label="Tracking code" value={code} onChange={(event) => setCode(event.target.value)} placeholder="CL-XXXXXXXX" className="min-w-0 flex-1 rounded-xl border p-3" />
        <button onClick={search} className="rounded-full bg-[#176b4b] px-5 py-3 font-semibold text-white">Track</button>
      </div>
      {error && <p role="alert" className="mt-5 rounded bg-red-50 p-4 text-red-700">{error}</p>}
      {item && <article className="mt-5 rounded-2xl border bg-white p-5"><p className="text-sm text-[#64756e]">{item.tracking_code}</p><h2 className="mt-2 text-xl font-bold">{item.title}</h2><p className="mt-2">{item.category} · {item.status.replaceAll("_", " ")}</p><p className="mt-2 text-sm text-[#64756e]">{item.address}</p></article>}
      <Link href="/login" className="mt-6 inline-block text-sm font-semibold text-[#176b4b]">Citizen sign in / register</Link>
    </main>
  );
}
