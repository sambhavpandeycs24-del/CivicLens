"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
type Overview = {
  total_complaints: number;
  resolved_complaints: number;
  open_complaints: number;
  resolution_rate_percent: number;
  by_status: Record<string, number>;
  by_category: Record<string, number>;
};
type Department = {
  department: string;
  authority_count: number;
  total_complaints: number;
  resolved_complaints: number;
  resolution_rate_percent: number;
  average_resolution_hours: number | null;
  pending_workload: number;
  overdue_complaints: number;
  sample_sufficient: boolean;
  sample_note: string | null;
};
type SlaItem = {
  tracking_code: string;
  title: string;
  category: string;
  priority: string;
  department: string;
  risk_level: string;
  target_hours: number;
  elapsed_hours: number;
  explanation: string;
};
type DashboardData = {
  overview: Overview;
  departments: Department[];
  sla: { risk_counts: Record<string, number>; items: SlaItem[] };
};

async function getJson<T>(path: string, token: string): Promise<T> {
  const response = await fetch(`${API}${path}`, { headers: { Authorization: `Bearer ${token}` } });
  if (!response.ok) throw new Error(await response.text());
  return response.json() as Promise<T>;
}

const cardClass = "rounded-2xl border border-[#e1e9e3] bg-white p-5 shadow-sm";
const riskClass: Record<string, string> = {
  overdue: "bg-red-100 text-red-800",
  at_risk: "bg-amber-100 text-amber-900",
  on_track: "bg-emerald-100 text-emerald-800",
};

export default function AnalyticsPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    const token = localStorage.getItem("civiclens_access_token");
    if (!token) {
      setError("Please log in with an Authority or Admin account to view analytics.");
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const [overview, departments, sla] = await Promise.all([
        getJson<Overview>("/analytics/overview", token),
        getJson<{ departments: Department[] }>("/analytics/departments", token),
        getJson<DashboardData["sla"]>("/analytics/sla", token),
      ]);
      setData({ overview, departments: departments.departments, sla });
      setError("");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to load intelligence analytics");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  return (
    <main className="mx-auto min-h-screen max-w-7xl px-5 py-8 text-[#17372b] sm:px-8">
      <nav className="flex flex-wrap gap-4 text-sm font-semibold text-[#176b4b]">
        <Link href="/">← Home</Link><Link href="/dashboard/map">Hotspot map</Link><Link href="/dashboard/ai">AI assistant</Link>
      </nav>
      <div className="mt-7 flex flex-wrap items-end justify-between gap-4">
        <div><p className="text-xs font-bold uppercase tracking-[.16em] text-[#176b4b]">Protected authority intelligence</p>
          <h1 className="mt-2 text-3xl font-bold sm:text-4xl">Civic performance</h1>
          <p className="mt-2 max-w-2xl text-[#64756e]">Operational measures and transparent SLA baselines from recorded complaints.</p>
        </div>
        <button onClick={() => void load()} className="rounded-full border border-[#cbd8d0] px-4 py-2 text-sm font-semibold">Refresh</button>
      </div>
      {error && <p role="alert" className="mt-6 break-words rounded-xl bg-red-50 p-4 text-sm text-red-800">{error}</p>}
      {loading && !data && !error && <p className="mt-6 text-[#64756e]">Loading analytics…</p>}
      {data && <>
        <section className="mt-7 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            ["Total complaints", data.overview.total_complaints],
            ["Open workload", data.overview.open_complaints],
            ["Resolved", data.overview.resolved_complaints],
            ["Resolution rate", `${data.overview.resolution_rate_percent}%`],
          ].map(([label, value]) => <article key={String(label)} className={cardClass}>
            <p className="text-sm text-[#64756e]">{label}</p><strong className="mt-2 block text-3xl">{value}</strong>
          </article>)}
        </section>

        <section className="mt-8 grid gap-5 lg:grid-cols-2">
          <article className={cardClass}>
            <h2 className="text-xl font-bold">Department performance</h2>
            <p className="mt-1 text-sm text-[#64756e]">No comparative ranking; small samples are marked descriptive only.</p>
            <div className="mt-4 grid gap-3">
              {data.departments.map((item) => <div key={item.department} className="rounded-xl bg-[#f5f8f5] p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h3 className="font-bold">{item.department}</h3>
                  <span className="rounded-full bg-white px-3 py-1 text-xs">{item.authority_count} authorities</span>
                </div>
                <div className="mt-3 grid grid-cols-2 gap-2 text-sm sm:grid-cols-4">
                  <p>Total <b className="block">{item.total_complaints}</b></p>
                  <p>Resolved <b className="block">{item.resolution_rate_percent}%</b></p>
                  <p>Pending <b className="block">{item.pending_workload}</b></p>
                  <p>Overdue <b className="block text-red-700">{item.overdue_complaints}</b></p>
                </div>
                <p className="mt-3 text-xs text-[#64756e]">
                  Average resolution: {item.average_resolution_hours === null ? "not available" : `${item.average_resolution_hours} hours`}
                  {!item.sample_sufficient && ` · ${item.sample_note}`}
                </p>
              </div>)}
              {data.departments.length === 0 && <p className="text-sm text-[#64756e]">No department data is available yet.</p>}
            </div>
          </article>
          <article className={cardClass}>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div><h2 className="text-xl font-bold">SLA risk</h2><p className="mt-1 text-sm text-[#64756e]">Transparent elapsed-time baseline; not an automated status change.</p></div>
              <div className="flex gap-2 text-xs">
                {Object.entries(data.sla.risk_counts).map(([risk, count]) => <span key={risk} className={`rounded-full px-3 py-1 ${riskClass[risk] ?? "bg-slate-100"}`}>{risk.replaceAll("_", " ")}: {count}</span>)}
              </div>
            </div>
            <div className="mt-4 grid gap-3">
              {data.sla.items.map((item) => <div key={item.tracking_code} className="rounded-xl border border-[#e7ece8] p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div><b>{item.title}</b><p className="text-xs text-[#64756e]">{item.tracking_code} · {item.category} · {item.department}</p></div>
                  <span className={`rounded-full px-3 py-1 text-xs font-bold ${riskClass[item.risk_level] ?? "bg-slate-100"}`}>{item.risk_level.replaceAll("_", " ")}</span>
                </div>
                <p className="mt-2 text-sm">{item.explanation} Target: {item.target_hours}h.</p>
              </div>)}
              {data.sla.items.length === 0 && <p className="text-sm text-[#64756e]">No active complaints in this scope.</p>}
            </div>
          </article>
        </section>
      </>}
    </main>
  );
}
