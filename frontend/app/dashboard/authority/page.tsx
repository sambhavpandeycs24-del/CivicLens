"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

type Complaint = {
  id: string;
  tracking_code: string;
  title: string;
  description: string;
  category: string;
  status: string;
  priority: string;
  address: string;
  assigned_to_id: string | null;
};

type DuplicateData = {
  possible_duplicates: Array<{ tracking_code: string; similarity: number; reason: string }>;
};

export default function AuthorityDashboard() {
  const [items, setItems] = useState<Complaint[]>([]);
  const [duplicates, setDuplicates] = useState<Record<string, DuplicateData>>({});
  const [status, setStatus] = useState("");
  const [category, setCategory] = useState("");
  const [priority, setPriority] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    const token = localStorage.getItem("civiclens_access_token");
    if (!token) {
      setError("Please log in with an Authority or Admin account.");
      return;
    }
    const params = new URLSearchParams();
    if (status) params.set("status", status);
    if (category) params.set("category", category);
    if (priority) params.set("priority", priority);
    try {
      const response = await fetch(`${API}/complaints?${params}`, { headers: { Authorization: `Bearer ${token}` } });
      if (!response.ok) throw new Error(await response.text());
      const data: Complaint[] = await response.json();
      setItems(data);
      setError("");
      await Promise.all(data.map(async (complaint) => {
        const duplicateResponse = await fetch(`${API}/complaints/${complaint.id}/duplicates`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (duplicateResponse.ok) {
          const duplicateData: DuplicateData = await duplicateResponse.json();
          setDuplicates((current) => ({
            ...current,
            [complaint.id]: duplicateData,
          }));
        }
      }));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to load complaints");
    }
  }, [status, category, priority]);

  useEffect(() => { load(); }, [load]);

  async function updateComplaint(id: string, changes: Record<string, string>) {
    const token = localStorage.getItem("civiclens_access_token");
    setMessage("");
    try {
      const response = await fetch(`${API}/complaints/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(changes),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail ?? "Update failed");
      setMessage(`Updated ${data.tracking_code}`);
      await load();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Update failed");
    }
  }

  return (
    <main className="mx-auto min-h-screen max-w-6xl px-6 py-10">
      <Link href="/">← Home</Link>
      <h1 className="mt-5 text-3xl font-bold">Authority complaint workflow</h1>
      <div className="mt-6 grid gap-3 rounded-xl border bg-white p-4 sm:grid-cols-4">
        <select value={status} onChange={(event) => setStatus(event.target.value)} className="rounded border p-2">
          <option value="">All statuses</option>
          {["submitted","under_review","assigned","in_progress","resolved","rejected"].map((value) => <option key={value} value={value}>{value.replaceAll("_"," ")}</option>)}
        </select>
        <select value={category} onChange={(event) => setCategory(event.target.value)} className="rounded border p-2">
          <option value="">All categories</option>
          {["pothole","garbage","streetlight","water_leakage","drainage","other"].map((value) => <option key={value} value={value}>{value.replaceAll("_"," ")}</option>)}
        </select>
        <select value={priority} onChange={(event) => setPriority(event.target.value)} className="rounded border p-2">
          <option value="">All priorities</option>
          {["low","medium","high","urgent"].map((value) => <option key={value} value={value}>{value}</option>)}
        </select>
        <button onClick={load} className="rounded bg-[#176b4b] px-4 py-2 font-semibold text-white">Apply filters</button>
      </div>
      {error && <p role="alert" className="mt-4 rounded bg-red-50 p-3 text-red-700">{error}</p>}
      {message && <p role="status" className="mt-4 rounded bg-green-50 p-3 text-green-800">{message}</p>}
      <div className="mt-6 grid gap-4">
        {items.map((complaint) => {
          const possible = duplicates[complaint.id]?.possible_duplicates ?? [];
          return (
            <article key={complaint.id} className="rounded-xl border bg-white p-5">
              <div className="flex flex-wrap justify-between gap-3">
                <div>
                  <b>{complaint.title}</b>
                  <p className="text-sm text-[#60756a]">{complaint.tracking_code} · {complaint.category} · {complaint.status}</p>
                </div>
                <span className={`rounded-full px-3 py-1 text-sm font-bold ${complaint.priority === "urgent" ? "bg-red-100 text-red-700" : complaint.priority === "high" ? "bg-orange-100 text-orange-700" : "bg-slate-100"}`}>Priority: {complaint.priority}</span>
              </div>
              {possible.length > 0 && (
                <p className="mt-3 rounded bg-amber-50 p-3 text-sm">
                  Possible duplicates: {possible.map((item) => `${item.tracking_code} (${item.similarity})`).join(", ")}
                </p>
              )}
              <div className="mt-4 flex flex-wrap gap-3">
                <select aria-label="Complaint status" defaultValue={complaint.status} onChange={(event) => updateComplaint(complaint.id, { status: event.target.value })} className="rounded border p-2">
                  {["submitted","under_review","assigned","in_progress","resolved","rejected"].map((value) => <option key={value} value={value}>{value.replaceAll("_"," ")}</option>)}
                </select>
                <select aria-label="Complaint priority" defaultValue={complaint.priority} onChange={(event) => updateComplaint(complaint.id, { priority: event.target.value })} className="rounded border p-2">
                  {["low","medium","high","urgent"].map((value) => <option key={value} value={value}>{value}</option>)}
                </select>
              </div>
            </article>
          );
        })}
        {items.length === 0 && !error && <p>No complaints match these filters.</p>}
      </div>
    </main>
  );
}
