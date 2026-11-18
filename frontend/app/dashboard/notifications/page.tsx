"use client";
import { useEffect, useState } from "react";
const API=process.env.NEXT_PUBLIC_API_URL??"http://localhost:8000/api/v1";
type Notice={id:string;title:string;message:string;is_read:boolean;created_at:string};
export default function NotificationsPage(){const [items,setItems]=useState<Notice[]>([]);const [error,setError]=useState("");
 async function load(){const token=localStorage.getItem("civiclens_access_token");if(!token){setError("Please log in to view your notifications.");return;}try{const r=await fetch(`${API}/notifications/mine`,{headers:{Authorization:`Bearer ${token}`}});if(!r.ok)throw new Error(await r.text());setItems(await r.json());}catch(e){setError(e instanceof Error?e.message:"Unable to load notifications");}}
 useEffect(()=>{load();},[]);
 async function markRead(id:string){const token=localStorage.getItem("civiclens_access_token");const r=await fetch(`${API}/notifications/${id}/read`,{method:"PATCH",headers:{Authorization:`Bearer ${token}`}});if(r.ok)load();}
 return <main style={{maxWidth:850,margin:"40px auto",padding:24}}><a href="/">← Home</a><h1 style={{fontSize:32,fontWeight:700,marginTop:20}}>Notifications</h1>{error&&<p role="alert">{error}</p>}<div style={{display:"grid",gap:12,marginTop:20}}>{items.map(n=><article key={n.id} style={{background:"white",padding:18,borderRadius:12,border:"1px solid #dce7df"}}><div style={{display:"flex",justifyContent:"space-between",gap:12}}><b>{n.title}</b>{!n.is_read&&<button onClick={()=>markRead(n.id)} style={{color:"#176b4b"}}>Mark read</button>}</div><p style={{marginTop:8}}>{n.message}</p><small style={{color:"#60756a"}}>{new Date(n.created_at).toLocaleString()}</small></article>)}</div>{items.length===0&&!error&&<p>No notifications yet.</p>}</main>;
}
