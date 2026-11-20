"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
type Point = { id:string; tracking_code:string; title:string; category:string; status:string; priority:string; latitude:number; longitude:number };
export default function MapPage() {
 const [points,setPoints]=useState<Point[]>([]); const [error,setError]=useState("");
 useEffect(()=>{const token=localStorage.getItem("civiclens_access_token"); if(!token){setError("Please log in with an Authority or Admin account to view complaint locations.");return;}
 const params=new URLSearchParams({min_lat:"-90",max_lat:"90",min_lon:"-180",max_lon:"180"});
 fetch(`${API}/geo/complaints?${params}`,{headers:{Authorization:`Bearer ${token}`}}).then(async r=>{if(!r.ok)throw new Error(await r.text());return r.json();}).then(d=>setPoints(d.items)).catch(e=>setError(e.message));},[]);
 return <main style={{maxWidth:1000,margin:"40px auto",padding:24}}><Link href="/">← Home</Link><h1 style={{fontSize:32,fontWeight:700,marginTop:20}}>Complaint locations</h1><p>Location records returned by the secure geospatial API. Select a map link to open the point in OpenStreetMap.</p>
 {error&&<p role="alert" style={{padding:16,background:"#fff1f0",marginTop:20}}>{error}</p>}
 <p style={{marginTop:18,fontWeight:600}}>Visible complaints: {points.length}</p><div style={{display:"grid",gap:12,marginTop:16}}>{points.map(p=><article key={p.id} style={{background:"white",border:"1px solid #dce7df",borderRadius:12,padding:16,display:"flex",justifyContent:"space-between",gap:16,flexWrap:"wrap"}}><div><b>{p.title}</b><p style={{color:"#60756a",fontSize:13}}>{p.tracking_code} · {p.category} · {p.status} · {p.priority}</p><p style={{fontSize:13}}>Lat {p.latitude}, Lon {p.longitude}</p></div><a target="_blank" rel="noreferrer" href={`https://www.openstreetmap.org/?mlat=${p.latitude}&mlon=${p.longitude}#map=17/${p.latitude}/${p.longitude}`} style={{color:"#176b4b",fontWeight:700}}>Open map ↗</a></article>)}</div>
 </main>;
}
