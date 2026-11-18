"use client";
import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
type Overview = { total_complaints: number; resolved_complaints: number; open_complaints: number; resolution_rate_percent: number; by_status: Record<string, number>; by_category: Record<string, number> };
export default function AnalyticsPage() {
  const [data, setData] = useState<Overview | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { const token = localStorage.getItem("civiclens_access_token");
    if (!token) { setError("Please log in with an Authority or Admin account to view analytics."); return; }
    fetch(`${API}/analytics/overview`, { headers: { Authorization: `Bearer ${token}` } })
      .then(async r => { if (!r.ok) throw new Error(await r.text()); return r.json(); })
      .then(setData).catch(e => setError(e.message));
  }, []);
  return <main style={{maxWidth:1000,margin:"40px auto",padding:24}}><a href="/">← Home</a><h1 style={{fontSize:32,fontWeight:700,marginTop:20}}>Civic analytics</h1><p>Live summary calculated from complaints stored in the database.</p>
    {error && <p role="alert" style={{padding:16,background:"#fff1f0",marginTop:20}}>{error}</p>}
    {data && <><section style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(180px,1fr))",gap:16,marginTop:24}}>{[["Total complaints",data.total_complaints],["Open complaints",data.open_complaints],["Resolved",data.resolved_complaints],["Resolution rate",`${data.resolution_rate_percent}%`]].map(([label,value])=><article key={String(label)} style={{background:"white",padding:22,borderRadius:14,border:"1px solid #dce7df"}}><p style={{color:"#60756a"}}>{label}</p><strong style={{fontSize:30}}>{value}</strong></article>)}</section><section style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(280px,1fr))",gap:20,marginTop:24}}><article style={{background:"white",padding:20,borderRadius:14}}><h2 style={{fontWeight:700}}>By status</h2>{Object.entries(data.by_status).map(([k,v])=><p key={k} style={{display:"flex",justifyContent:"space-between",padding:"8px 0",borderBottom:"1px solid #eee"}}><span>{k.replaceAll("_"," ")}</span><b>{v}</b></p>)}</article><article style={{background:"white",padding:20,borderRadius:14}}><h2 style={{fontWeight:700}}>By category</h2>{Object.entries(data.by_category).map(([k,v])=><p key={k} style={{display:"flex",justifyContent:"space-between",padding:"8px 0",borderBottom:"1px solid #eee"}}><span>{k.replaceAll("_"," ")}</span><b>{v}</b></p>)}</article></section></>}
  </main>;
}
