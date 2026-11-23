"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
type Point = {
  id: string;
  tracking_code: string;
  title: string;
  category: string;
  status: string;
  priority: string;
  latitude: number;
  longitude: number;
};
type Hotspot = {
  category: string;
  time_bucket: string;
  complaint_count: number;
  latitude: number;
  longitude: number;
};
type HotspotResponse = {
  days: number;
  radius_meters: number;
  method: string;
  hotspots: Hotspot[];
};

export default function MapPage() {
  const [points, setPoints] = useState<Point[]>([]);
  const [hotspots, setHotspots] = useState<HotspotResponse | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = localStorage.getItem("civiclens_access_token");
    if (!token) {
      setError("Please log in with an Authority or Admin account to view complaint locations.");
      return;
    }
    const headers = { Authorization: `Bearer ${token}` };
    const params = new URLSearchParams({ min_lat: "-90", max_lat: "90", min_lon: "-180", max_lon: "180" });
    Promise.all([
      fetch(`${API}/geo/complaints?${params}`, { headers }),
      fetch(`${API}/geo/hotspots?days=30`, { headers }),
    ]).then(async ([pointsResponse, hotspotsResponse]) => {
      if (!pointsResponse.ok) throw new Error(await pointsResponse.text());
      if (!hotspotsResponse.ok) throw new Error(await hotspotsResponse.text());
      const pointsData: { items: Point[] } = await pointsResponse.json();
      const hotspotData: HotspotResponse = await hotspotsResponse.json();
      setPoints(pointsData.items);
      setHotspots(hotspotData);
    }).catch((caught: unknown) => setError(caught instanceof Error ? caught.message : "Unable to load geospatial analytics"));
  }, []);

  return (
    <main className="mx-auto min-h-screen max-w-7xl px-5 py-8 text-[#17372b] sm:px-8">
      <nav className="flex flex-wrap gap-4 text-sm font-semibold text-[#176b4b]">
        <Link href="/">← Home</Link><Link href="/dashboard/analytics">Performance analytics</Link><Link href="/dashboard/ai">AI assistant</Link>
      </nav>
      <h1 className="mt-7 text-3xl font-bold sm:text-4xl">Geographic hotspots</h1>
      <p className="mt-2 text-[#64756e]">Complaint clusters by issue category and week, based on the last 30 days.</p>
      {error && <p role="alert" className="mt-5 break-words rounded-xl bg-red-50 p-4 text-sm text-red-800">{error}</p>}
      {hotspots && <>
        <section className="mt-6 grid gap-4 sm:grid-cols-3">
          <article className="rounded-2xl border border-[#e1e9e3] bg-white p-5"><p className="text-sm text-[#64756e]">Clusters</p><b className="mt-2 block text-3xl">{hotspots.hotspots.length}</b></article>
          <article className="rounded-2xl border border-[#e1e9e3] bg-white p-5"><p className="text-sm text-[#64756e]">Visible complaints</p><b className="mt-2 block text-3xl">{points.length}</b></article>
          <article className="rounded-2xl border border-[#e1e9e3] bg-white p-5"><p className="text-sm text-[#64756e]">Cluster method</p><b className="mt-2 block text-lg">{hotspots.method.replaceAll("_", " ")}</b></article>
        </section>
        <section className="mt-7">
          <h2 className="text-xl font-bold">Category and time-based clusters</h2>
          <p className="mt-1 text-sm text-[#64756e]">
            {hotspots.method === "postgis_clusterdbscan"
              ? `Clusters include at least two reports within ${hotspots.radius_meters} metres.`
              : "Local/test fallback groups reports by rounded coordinates and week; distance-based clusters require PostgreSQL/PostGIS."}
          </p>
          <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {hotspots.hotspots.map((item, index) => {
              const strength = Math.min(1, item.complaint_count / Math.max(4, points.length / 4));
              return <article key={`${item.category}-${item.time_bucket}-${index}`} className="overflow-hidden rounded-2xl border border-[#e1e9e3] bg-white">
                <div className="h-2 bg-[#176b4b]" style={{ opacity: 0.35 + strength * 0.65 }} />
                <div className="p-5">
                  <div className="flex items-start justify-between gap-3">
                    <div><p className="text-xs font-bold uppercase tracking-wider text-[#64756e]">{item.time_bucket} week</p><h3 className="mt-1 text-lg font-bold capitalize">{item.category.replaceAll("_", " ")}</h3></div>
                    <span className="rounded-full bg-[#e6f1e9] px-3 py-1 text-sm font-bold text-[#176b4b]">{item.complaint_count} reports</span>
                  </div>
                  <div className="mt-4 h-2 overflow-hidden rounded-full bg-[#edf1ee]"><div className="h-full rounded-full bg-[#176b4b]" style={{ width: `${Math.max(8, strength * 100)}%` }} /></div>
                  <a className="mt-4 inline-block text-sm font-bold text-[#176b4b]" target="_blank" rel="noreferrer"
                    href={`https://www.openstreetmap.org/?mlat=${item.latitude}&mlon=${item.longitude}#map=16/${item.latitude}/${item.longitude}`}>
                    Open cluster location ↗
                  </a>
                </div>
              </article>;
            })}
            {hotspots.hotspots.length === 0 && <p className="rounded-xl bg-white p-5 text-sm text-[#64756e]">No clusters meet the minimum complaint count and time window.</p>}
          </div>
        </section>
      </>}
      <section className="mt-9">
        <h2 className="text-xl font-bold">Individual complaint locations ({points.length})</h2>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          {points.map((point) => <article key={point.id} className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[#e1e9e3] bg-white p-4">
            <div><b>{point.title}</b><p className="text-xs text-[#64756e]">{point.tracking_code} · {point.category} · {point.status} · {point.priority}</p></div>
            <a className="text-sm font-bold text-[#176b4b]" target="_blank" rel="noreferrer"
              href={`https://www.openstreetmap.org/?mlat=${point.latitude}&mlon=${point.longitude}#map=17/${point.latitude}/${point.longitude}`}>Open map ↗</a>
          </article>)}
        </div>
      </section>
    </main>
  );
}
