"use client";

import Link from "next/link";
import { useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export default function ReportPage() {
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(formData: FormData) {
    setBusy(true);
    setMessage("");
    try {
      const token = window.localStorage.getItem("civiclens_access_token");
      if (!token) throw new Error("Please log in first. Authentication UI is scheduled for the next frontend iteration.");
      const payload = {
        title: String(formData.get("title") ?? ""),
        description: String(formData.get("description") ?? ""),
        category: String(formData.get("category") ?? "other"),
        address: String(formData.get("address") ?? ""),
        latitude: Number(formData.get("latitude")),
        longitude: Number(formData.get("longitude")),
      };
      const response = await fetch(`${API}/complaints`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail ?? "Could not submit complaint");
      const image = formData.get("image");
      if (image instanceof File && image.size > 0) {
        const imageForm = new FormData();
        imageForm.append("file", image);
        const imageResponse = await fetch(`${API}/complaints/${data.id}/image`, {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
          body: imageForm,
        });
        const imageData = await imageResponse.json();
        if (!imageResponse.ok) throw new Error(imageData.detail ?? "Complaint created, but image upload failed");
      }
      setMessage(`Complaint submitted. Tracking ID: ${data.tracking_code}`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Something went wrong");
    } finally {
      setBusy(false);
    }
  }

  return <main className="min-h-screen bg-[#f6f8f5] px-6 py-12 text-[#17372b]">
    <div className="mx-auto max-w-2xl">
      <Link href="/" className="text-sm font-semibold text-[#176b4b]">← CivicLens AI</Link>
      <h1 className="mt-8 text-4xl font-bold">Report a civic issue</h1>
      <p className="mt-3 text-[#64756e]">Provide accurate details so the responsible civic team can investigate.</p>
      <form action={submit} className="mt-8 grid gap-5 rounded-3xl border border-[#e0e9e2] bg-white p-7 shadow-sm">
        <label className="grid gap-2 text-sm font-semibold">Issue title<input name="title" required minLength={5} maxLength={160} className="rounded-xl border p-3 font-normal" placeholder="e.g. Pothole near school" /></label>
        <label className="grid gap-2 text-sm font-semibold">Category<select name="category" className="rounded-xl border p-3 font-normal"><option value="pothole">Pothole / Road damage</option><option value="garbage">Garbage</option><option value="streetlight">Streetlight</option><option value="water_leakage">Water leakage</option><option value="drainage">Drainage</option><option value="other">Other</option></select></label>
        <label className="grid gap-2 text-sm font-semibold">Description<textarea name="description" required minLength={10} rows={4} className="rounded-xl border p-3 font-normal" placeholder="Describe the issue and its impact..." /></label>
        <label className="grid gap-2 text-sm font-semibold">Address<input name="address" required minLength={5} className="rounded-xl border p-3 font-normal" placeholder="Area, landmark, city" /></label>
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="grid gap-2 text-sm font-semibold">Latitude<input name="latitude" type="number" step="any" min="-90" max="90" required className="rounded-xl border p-3 font-normal" /></label>
          <label className="grid gap-2 text-sm font-semibold">Longitude<input name="longitude" type="number" step="any" min="-180" max="180" required className="rounded-xl border p-3 font-normal" /></label>
        </div>
        <label className="grid gap-2 text-sm font-semibold">Optional image<input name="image" type="file" accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp" className="rounded-xl border p-3 font-normal" /></label>
        <button disabled={busy} className="rounded-full bg-[#176b4b] px-6 py-3 font-semibold text-white disabled:opacity-60">{busy ? "Submitting..." : "Submit complaint"}</button>
        {message && <p role="status" className="rounded-xl bg-[#edf5ef] p-4 text-sm">{message}</p>}
      </form>
    </div>
  </main>;
}
