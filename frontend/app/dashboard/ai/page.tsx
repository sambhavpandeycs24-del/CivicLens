"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
const categories = ["pothole", "garbage", "streetlight", "water_leakage", "drainage", "other"];
type Analysis = {
  suggested_category: string;
  category_confidence: number;
  category_reason: string;
  classification_method: string;
  suggested_priority: string;
  priority_score: number;
  priority_reasons: string[];
  duplicate_candidates: Array<{ tracking_code: string; similarity: number; reason: string }>;
  decision_notice: string;
};
type Summary = {
  summary: string;
  issue: string;
  location: string;
  urgency: string;
  recommended_action: string;
  generated_by: string;
};
type FormFields = { title: string; description: string; category: string; priority: string; address: string };

async function postJson<T>(path: string, token: string, body: object): Promise<T> {
  const response = await fetch(`${API}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error(await response.text());
  return response.json() as Promise<T>;
}

export default function AiDashboardPage() {
  const [fields, setFields] = useState<FormFields>({
    title: "",
    description: "",
    category: "other",
    priority: "medium",
    address: "",
  });
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  function updateField(key: keyof FormFields, value: string) {
    setFields((current) => ({ ...current, [key]: value }));
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setAnalysis(null);
    setSummary(null);
    try {
      const token = localStorage.getItem("civiclens_access_token");
      if (!token) throw new Error("Please log in to use the protected AI assistance endpoints.");
      const [analysisResult, summaryResult] = await Promise.all([
        postJson<Analysis>("/ai/analyze", token, {
          title: fields.title,
          description: fields.description,
          category: fields.category,
        }),
        postJson<Summary>("/ai/summarize", token, fields),
      ]);
      setAnalysis(analysisResult);
      setSummary(summaryResult);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to analyze this complaint");
    } finally {
      setBusy(false);
    }
  }

  const inputClass = "w-full rounded-xl border border-[#d7e1da] bg-white p-3 font-normal outline-none focus:border-[#176b4b]";

  return (
    <main className="mx-auto min-h-screen max-w-6xl px-5 py-8 text-[#17372b] sm:px-8">
      <nav className="flex flex-wrap gap-4 text-sm font-semibold text-[#176b4b]">
        <Link href="/">← Home</Link><Link href="/dashboard/analytics">Performance analytics</Link><Link href="/dashboard/map">Hotspot map</Link>
      </nav>
      <header className="mt-7">
        <p className="text-xs font-bold uppercase tracking-[.16em] text-[#176b4b]">Human-reviewed decision support</p>
        <h1 className="mt-2 text-3xl font-bold sm:text-4xl">AI complaint intelligence</h1>
        <p className="mt-2 max-w-3xl text-[#64756e]">Review category and priority signals, possible duplicates, and a concise operational summary. Nothing is saved or changed by this analysis.</p>
      </header>

      <div className="mt-7 grid items-start gap-6 lg:grid-cols-[.9fr_1.1fr]">
        <form onSubmit={submit} className="grid gap-4 rounded-2xl border border-[#e1e9e3] bg-white p-5 shadow-sm sm:p-6">
          <label className="grid gap-2 text-sm font-semibold">Issue title
            <input required minLength={5} maxLength={160} value={fields.title} onChange={(event) => updateField("title", event.target.value)} className={inputClass} placeholder="e.g. Broken streetlight near clinic" />
          </label>
          <label className="grid gap-2 text-sm font-semibold">Description
            <textarea required minLength={10} maxLength={5000} rows={5} value={fields.description} onChange={(event) => updateField("description", event.target.value)} className={inputClass} placeholder="Describe the issue, impact, and any urgent details." />
          </label>
          <label className="grid gap-2 text-sm font-semibold">Citizen-selected category
            <select value={fields.category} onChange={(event) => updateField("category", event.target.value)} className={inputClass}>
              {categories.map((category) => <option key={category} value={category}>{category.replaceAll("_", " ")}</option>)}
            </select>
          </label>
          <label className="grid gap-2 text-sm font-semibold">Current priority
            <select value={fields.priority} onChange={(event) => updateField("priority", event.target.value)} className={inputClass}>
              {["low", "medium", "high", "urgent"].map((priority) => <option key={priority} value={priority}>{priority}</option>)}
            </select>
          </label>
          <label className="grid gap-2 text-sm font-semibold">Location / address
            <input required minLength={1} maxLength={300} value={fields.address} onChange={(event) => updateField("address", event.target.value)} className={inputClass} placeholder="Area, landmark, city" />
          </label>
          <button disabled={busy} className="rounded-full bg-[#176b4b] px-5 py-3 font-semibold text-white disabled:opacity-60">
            {busy ? "Analyzing…" : "Analyze complaint"}
          </button>
        </form>

        <section aria-live="polite" className="grid gap-5">
          {error && <p role="alert" className="break-words rounded-xl bg-red-50 p-4 text-sm text-red-800">{error}</p>}
          {!analysis && !error && <div className="rounded-2xl border border-dashed border-[#cbd8d0] p-8 text-sm text-[#64756e]">Analysis and summary will appear here after submission.</div>}
          {analysis && <>
            <article className="rounded-2xl border border-[#e1e9e3] bg-white p-5 shadow-sm">
              <h2 className="text-xl font-bold">AI signals</h2>
              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                <div className="rounded-xl bg-[#f5f8f5] p-4"><p className="text-xs text-[#64756e]">Category suggestion</p><b className="mt-1 block capitalize">{analysis.suggested_category.replaceAll("_", " ")}</b><p className="mt-1 text-xs">{Math.round(analysis.category_confidence * 100)}% confidence · {analysis.classification_method.replaceAll("_", " ")}</p><p className="mt-2 text-xs text-[#64756e]">{analysis.category_reason}</p></div>
                <div className="rounded-xl bg-[#f5f8f5] p-4"><p className="text-xs text-[#64756e]">Priority suggestion</p><b className="mt-1 block capitalize">{analysis.suggested_priority}</b><p className="mt-1 text-xs">Advisory score {analysis.priority_score}/100</p><ul className="mt-2 list-disc pl-4 text-xs text-[#64756e]">{analysis.priority_reasons.map((reason) => <li key={reason}>{reason}</li>)}</ul></div>
              </div>
              <div className="mt-4 rounded-xl bg-amber-50 p-4 text-sm"><b>Possible duplicates</b>
                {analysis.duplicate_candidates.length
                  ? <ul className="mt-2 list-disc pl-5">{analysis.duplicate_candidates.map((item) => <li key={item.tracking_code}>{item.tracking_code} · {Math.round(item.similarity * 100)}% · {item.reason}</li>)}</ul>
                  : <p className="mt-1">No likely matches found in the recent complaint window.</p>}
              </div>
              <p className="mt-3 text-xs text-[#64756e]">{analysis.decision_notice}</p>
            </article>
            {summary && <article className="rounded-2xl border border-[#e1e9e3] bg-white p-5 shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-2"><h2 className="text-xl font-bold">Complaint brief</h2><span className="rounded-full bg-[#e6f1e9] px-3 py-1 text-xs font-semibold">{summary.generated_by.replaceAll("_", " ")}</span></div>
              <p className="mt-4 text-lg font-semibold">{summary.summary}</p>
              <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
                <div><dt className="text-xs font-bold uppercase text-[#64756e]">Issue</dt><dd className="mt-1">{summary.issue}</dd></div>
                <div><dt className="text-xs font-bold uppercase text-[#64756e]">Location</dt><dd className="mt-1">{summary.location}</dd></div>
                <div><dt className="text-xs font-bold uppercase text-[#64756e]">Urgency</dt><dd className="mt-1">{summary.urgency}</dd></div>
                <div><dt className="text-xs font-bold uppercase text-[#64756e]">Recommended action</dt><dd className="mt-1">{summary.recommended_action}</dd></div>
              </dl>
            </article>}
          </>}
        </section>
      </div>
    </main>
  );
}
